"""Full analysis pipeline orchestrator.

Coordinates all stages of repository analysis:
1. Parse files (ParserService)
2. Build dependency graph (GraphService)
3. Embed chunks (EmbeddingService)
4. Generate summaries (AnalysisService)
5. Detect bugs (BugDetectionService)
6. Generate refactoring suggestions (RefactorService)
7. Persist all results
"""

import asyncio
from pathlib import Path

from core.exceptions import RepositoryNotFoundError
from core.logging import get_logger
from domain.models import AnalysisStatus, Repository
from infrastructure.database.repositories.repo_repository import (
    PostgresIssueStore,
    PostgresRefactorStore,
    PostgresRepositoryStore,
)
from services.analysis_service import AnalysisService
from services.bug_detection_service import BugDetectionService
from services.embedding_service import EmbeddingService
from services.graph_service import GraphService
from services.parser_service import ParserService
from services.refactor_service import RefactorService
from services.repo_service import RepoIngestionService

logger = get_logger(__name__)


class AnalysisPipeline:
    """
    Orchestrates the complete repository analysis pipeline.

    Designed to be called from a background task (FastAPI BackgroundTasks
    or Celery worker) after the initial HTTP response has been sent.
    """

    def __init__(self) -> None:
        self._repo_store = PostgresRepositoryStore()
        self._issue_store = PostgresIssueStore()
        self._refactor_store = PostgresRefactorStore()
        self._ingestion = RepoIngestionService()
        self._parser = ParserService()
        self._graph = GraphService()
        self._embedding = EmbeddingService()
        self._analysis = AnalysisService()
        self._bug_detector = BugDetectionService()
        self._refactor = RefactorService()

    async def run(self, repo_id: str) -> None:
        """
        Execute all pipeline stages for the given repo_id.
        The repo must already be cloned and in PARSING status.
        """
        repo = await self._repo_store.get_by_id(repo_id)
        if not repo:
            raise RepositoryNotFoundError(repo_id)

        try:
            await self._run_stages(repo)
        except Exception as exc:
            logger.error("Pipeline failed", repo_id=repo_id, error=str(exc))
            repo.mark_status(AnalysisStatus.FAILED, error=str(exc))
            await self._repo_store.save(repo)
            raise

    async def _run_stages(self, repo: Repository) -> None:
        repo_dir = self._ingestion.get_repo_dir(repo.repo_id)

        # ── Stage 1: Parse ────────────────────────────────────────────────────
        logger.info("Stage 1/5: Parsing", repo_id=repo.repo_id)
        file_analyses = self._parser.parse_repository(repo_dir)

        # ── Stage 2: Dependency graph ─────────────────────────────────────────
        logger.info("Stage 2/5: Building graph", repo_id=repo.repo_id)
        repo.mark_status(AnalysisStatus.EMBEDDING)
        await self._repo_store.save(repo)

        await self._graph.build_and_save(repo.repo_id, file_analyses)

        # ── Stage 3: Embed chunks ─────────────────────────────────────────────
        logger.info("Stage 3/5: Embedding", repo_id=repo.repo_id)
        await self._embedding.embed_files(repo.repo_id, file_analyses)

        # ── Stage 4: Summaries + bug detection + refactoring (parallel LLM) ──
        logger.info("Stage 4/5: LLM analysis", repo_id=repo.repo_id)
        repo.mark_status(AnalysisStatus.ANALYZING)
        await self._repo_store.save(repo)

        # Run LLM-heavy tasks concurrently
        (
            arch_summary,
            semantic_issues,
            llm_suggestions,
        ) = await asyncio.gather(
            self._analysis.summarise_repository(repo.github_url, file_analyses),
            self._bug_detector.detect_semantic_issues(repo.repo_id, file_analyses),
            self._refactor.generate_llm_suggestions(repo.repo_id, file_analyses),
            return_exceptions=True,
        )

        # ── Stage 5: Static analysis (no LLM needed) ─────────────────────────
        logger.info("Stage 5/5: Static analysis + persist", repo_id=repo.repo_id)
        static_issues = self._bug_detector.detect_static_issues(
            repo.repo_id, file_analyses
        )
        static_suggestions = self._refactor.detect_static_smells(
            repo.repo_id, file_analyses
        )

        # Combine and persist
        all_issues = static_issues + (
            semantic_issues if isinstance(semantic_issues, list) else []
        )
        all_suggestions = static_suggestions + (
            llm_suggestions if isinstance(llm_suggestions, list) else []
        )

        if all_issues:
            await self._issue_store.save_bulk(all_issues)
        if all_suggestions:
            await self._refactor_store.save_bulk(all_suggestions)

        # Finalise repository record
        repo.architecture_summary = (
            arch_summary if isinstance(arch_summary, str) else None
        )
        repo.mark_status(AnalysisStatus.COMPLETE)
        await self._repo_store.save(repo)

        logger.info(
            "Analysis pipeline complete",
            repo_id=repo.repo_id,
            files=len(file_analyses),
            issues=len(all_issues),
            suggestions=len(all_suggestions),
        )

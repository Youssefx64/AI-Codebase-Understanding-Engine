"""Celery task definitions.

Tasks are thin wrappers that delegate to the async pipeline service,
running it synchronously via asyncio.run() within the Celery worker context.
"""

import asyncio

from celery import Task
from celery.utils.log import get_task_logger

from workers.celery_app import celery_app

logger = get_task_logger(__name__)


class PipelineTask(Task):
    """Base task with retry configuration for transient failures."""

    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes max backoff
    max_retries = 3


@celery_app.task(bind=True, base=PipelineTask, name="workers.tasks.run_analysis_pipeline")
def run_analysis_pipeline(self: Task, repo_id: str) -> dict:
    """
    Full analysis pipeline task.

    Clones (if needed), parses, embeds, and analyses the repository.
    """
    logger.info("Starting analysis pipeline", extra={"repo_id": repo_id})

    from services.pipeline_service import AnalysisPipeline

    pipeline = AnalysisPipeline()
    try:
        asyncio.run(pipeline.run(repo_id))
        logger.info("Pipeline complete", extra={"repo_id": repo_id})
        return {"status": "complete", "repo_id": repo_id}
    except Exception as exc:
        logger.error("Pipeline failed", extra={"repo_id": repo_id, "error": str(exc)})
        raise self.retry(exc=exc)


@celery_app.task(bind=True, base=PipelineTask, name="workers.tasks.generate_embeddings")
def generate_embeddings(self: Task, repo_id: str) -> dict:
    """
    Re-embed a repository without re-running the full pipeline.
    Useful for updating the vector index after a code change.
    """
    logger.info("Re-embedding repository", extra={"repo_id": repo_id})

    from pathlib import Path

    from services.embedding_service import EmbeddingService
    from services.parser_service import ParserService
    from services.repo_service import RepoIngestionService

    ingestion = RepoIngestionService()
    parser = ParserService()
    embedding = EmbeddingService()

    repo_dir = ingestion.get_repo_dir(repo_id)
    file_analyses = parser.parse_repository(repo_dir)

    async def _run():
        return await embedding.embed_files(repo_id, file_analyses)

    total = asyncio.run(_run())
    return {"status": "complete", "repo_id": repo_id, "chunks": total}

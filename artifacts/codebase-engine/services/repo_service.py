"""Repository ingestion service.

Responsible for:
1. Cloning a GitHub repository to local disk.
2. Detecting the programming language(s) used.
3. Persisting the Repository aggregate via the store.
4. Triggering downstream analysis (parsing, embedding, etc.).
"""

import os
import shutil
import urllib.parse
from pathlib import Path
from typing import List

import git  # GitPython

from core.config import get_settings
from core.exceptions import RepositoryIngestionError
from core.logging import get_logger
from domain.models import AnalysisStatus, Repository, SupportedLanguage
from infrastructure.database.repositories.repo_repository import PostgresRepositoryStore
from parsers.parser_factory import get_parser_factory

logger = get_logger(__name__)

_IGNORED_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "env",
    ".tox", "dist", "build", ".mypy_cache", ".pytest_cache", "coverage",
    ".next", ".nuxt", "out", ".cache",
}


class RepoIngestionService:
    """Handles cloning and initial metadata extraction for a GitHub repository."""

    def __init__(self) -> None:
        self._store = PostgresRepositoryStore()
        self._factory = get_parser_factory()
        settings = get_settings()
        self._base_dir = Path(settings.repos_base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    async def ingest(self, github_url: str, branch: str = "main") -> Repository:
        """
        Clone the repository and persist initial metadata.

        Returns a Repository in PARSING status so the caller can
        hand off to further analysis stages.
        """
        # Parse owner/name from URL
        owner, name = _parse_github_url(github_url)

        # Upsert: check for existing record
        existing = await self._store.get_by_url(github_url)
        if existing and existing.status == AnalysisStatus.COMPLETE:
            logger.info("Repo already analysed", repo_id=existing.repo_id)
            return existing

        repo = existing or Repository(
            github_url=github_url,
            owner=owner,
            name=name,
            branch=branch,
        )

        repo.mark_status(AnalysisStatus.CLONING)
        await self._store.save(repo)

        # Clone
        repo_dir = self._base_dir / repo.repo_id
        try:
            if repo_dir.exists():
                shutil.rmtree(repo_dir)
            _clone_repo(github_url, branch, repo_dir)
        except Exception as exc:
            repo.mark_status(AnalysisStatus.FAILED, error=str(exc))
            await self._store.save(repo)
            raise RepositoryIngestionError(github_url, str(exc)) from exc

        # Detect languages and count files/lines
        languages, file_count, total_lines = self._scan_repo(repo_dir)
        repo.languages = languages
        repo.file_count = file_count
        repo.total_lines = total_lines
        repo.mark_status(AnalysisStatus.PARSING)
        await self._store.save(repo)

        logger.info(
            "Repo cloned",
            repo_id=repo.repo_id,
            owner=owner,
            name=name,
            files=file_count,
            lines=total_lines,
            languages=[l.value for l in languages],
        )
        return repo

    def _scan_repo(
        self, repo_dir: Path
    ) -> tuple[List[SupportedLanguage], int, int]:
        """Walk the repo and collect language distribution, file count, line count."""
        lang_counts: dict[SupportedLanguage, int] = {}
        total_files = 0
        total_lines = 0

        for path in repo_dir.rglob("*"):
            if path.is_file() and not _is_ignored(path, repo_dir):
                total_files += 1
                lang = self._factory.detect_language(str(path))
                if lang != SupportedLanguage.UNKNOWN:
                    lang_counts[lang] = lang_counts.get(lang, 0) + 1
                try:
                    total_lines += path.read_text(errors="replace").count("\n")
                except Exception:
                    pass

        languages = sorted(lang_counts, key=lambda l: lang_counts[l], reverse=True)
        return languages, total_files, total_lines

    def get_repo_dir(self, repo_id: str) -> Path:
        """Return the local clone directory for a repository."""
        return self._base_dir / repo_id


def _clone_repo(url: str, branch: str, dest: Path) -> None:
    """Clone a GitHub repository via GitPython."""
    try:
        git.Repo.clone_from(url, str(dest), branch=branch, depth=50)
    except git.exc.GitCommandError as exc:
        # Try default branch on failure (main vs master)
        try:
            git.Repo.clone_from(url, str(dest), depth=50)
        except git.exc.GitCommandError:
            raise exc


def _parse_github_url(url: str) -> tuple[str, str]:
    """Extract (owner, repo_name) from a GitHub URL."""
    parsed = urllib.parse.urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) >= 2:
        return parts[0], parts[1].removesuffix(".git")
    return "unknown", "unknown"


def _is_ignored(path: Path, base: Path) -> bool:
    """Return True if the path belongs to a directory we should skip."""
    try:
        relative = path.relative_to(base)
        return any(part in _IGNORED_DIRS for part in relative.parts)
    except ValueError:
        return False

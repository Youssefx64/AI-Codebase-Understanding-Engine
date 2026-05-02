"""Parser orchestration service.

Walks a cloned repository, delegates file parsing to the correct parser
via the factory, and aggregates results into a collection of FileAnalysis
objects that downstream services consume.
"""

from pathlib import Path
from typing import List

from core.logging import get_logger
from domain.models import FileAnalysis, SupportedLanguage
from parsers.parser_factory import get_parser_factory
from services.repo_service import _is_ignored

logger = get_logger(__name__)

_MAX_FILE_SIZE_BYTES = 512 * 1024  # 512 KB — skip minified or generated files
_SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".bin", ".exe", ".dll",
    ".pdf", ".lock", ".min.js", ".min.css",
    ".map",
}


class ParserService:
    """Orchestrates multi-file parsing across a repository clone."""

    def __init__(self) -> None:
        self._factory = get_parser_factory()

    def parse_repository(self, repo_dir: Path) -> List[FileAnalysis]:
        """
        Walk ``repo_dir`` and return a FileAnalysis for every parseable file.

        Files are processed synchronously; the list is returned in full
        so callers can immediately hand off to the embedding pipeline.
        """
        results: List[FileAnalysis] = []

        for file_path in sorted(repo_dir.rglob("*")):
            if not file_path.is_file():
                continue
            if _is_ignored(file_path, repo_dir):
                continue
            if file_path.suffix.lower() in _SKIP_EXTENSIONS:
                continue
            if file_path.stat().st_size > _MAX_FILE_SIZE_BYTES:
                logger.debug("Skipping large file", path=str(file_path))
                continue

            parser = self._factory.get_for_file(str(file_path))
            if parser is None:
                continue

            try:
                content = file_path.read_text(errors="replace")
                rel_path = str(file_path.relative_to(repo_dir))
                analysis = parser.parse_file(rel_path, content)
                results.append(analysis)
            except Exception as exc:
                logger.warning("Failed to read file", path=str(file_path), error=str(exc))

        logger.info(
            "Repository parsed",
            total_files=len(results),
            languages=list({a.language.value for a in results}),
        )
        return results

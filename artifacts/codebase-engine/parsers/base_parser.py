"""Abstract base parser (Strategy Pattern).

All language-specific parsers inherit from BaseParser and implement
the Visitor Pattern internally via AST node traversal methods.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from core.logging import get_logger
from domain.models import FileAnalysis, SupportedLanguage

logger = get_logger(__name__)


class BaseParser(ABC):
    """
    Strategy interface and shared utilities for language-specific parsers.

    Subclasses implement:
    - ``supported_extensions`` – file extensions this parser handles
    - ``language``             – the SupportedLanguage enum value
    - ``_parse_content``       – core AST/parse logic returning FileAnalysis
    """

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """List of file extensions this parser handles (e.g. ['.py'])."""
        ...

    @property
    @abstractmethod
    def language(self) -> SupportedLanguage:
        """The language this parser targets."""
        ...

    def supports(self, language_or_ext: str) -> bool:
        """Return True if this parser can handle the given language or extension."""
        return (
            language_or_ext.lower() == self.language.value
            or language_or_ext.lower() in self.supported_extensions
        )

    def parse_file(self, file_path: str, content: str) -> FileAnalysis:
        """
        Public entry point: parse ``content`` from ``file_path``.

        Catches all exceptions and returns a minimal FileAnalysis on failure
        so that one bad file does not abort the entire ingestion pipeline.
        """
        try:
            analysis = self._parse_content(file_path, content)
            logger.debug(
                "Parsed file",
                path=file_path,
                functions=len(analysis.functions),
                classes=len(analysis.classes),
            )
            return analysis
        except Exception as exc:
            logger.warning("Parse error", path=file_path, error=str(exc))
            return FileAnalysis(
                file_path=file_path,
                language=self.language,
                lines_of_code=content.count("\n") + 1,
            )

    @abstractmethod
    def _parse_content(self, file_path: str, content: str) -> FileAnalysis:
        """Language-specific implementation. Must be overridden."""
        ...

    # ── Shared utilities ───────────────────────────────────────────────────────

    @staticmethod
    def count_lines(content: str) -> int:
        """Return the number of non-blank lines."""
        return sum(1 for line in content.splitlines() if line.strip())

    @staticmethod
    def extract_docstring(node_body) -> str | None:
        """
        Extract a docstring from an AST node body list (Python ast nodes).
        Returns None when no docstring is present.
        """
        try:
            import ast

            if (
                node_body
                and isinstance(node_body[0], ast.Expr)
                and isinstance(node_body[0].value, ast.Constant)
                and isinstance(node_body[0].value.value, str)
            ):
                return node_body[0].value.value.strip()
        except Exception:
            pass
        return None

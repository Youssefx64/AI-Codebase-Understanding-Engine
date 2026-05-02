"""Parser Factory — selects the correct parser for a given file.

Implements the Factory Pattern: callers request a parser by file extension
or language name and receive the appropriate concrete implementation without
needing to know which class backs it.
"""

from pathlib import Path
from typing import Dict, List, Optional

from core.exceptions import UnsupportedLanguageError
from core.logging import get_logger
from domain.interfaces import ICodeParser
from domain.models import SupportedLanguage
from parsers.base_parser import BaseParser
from parsers.javascript_parser import JavaScriptParser
from parsers.python_parser import PythonParser

logger = get_logger(__name__)


class ParserFactory:
    """
    Registry of available parsers.

    New parsers can be registered at startup via ``register()``,
    making the factory open for extension without modification (OCP).
    """

    def __init__(self) -> None:
        self._parsers: List[BaseParser] = []
        self._ext_cache: Dict[str, BaseParser] = {}

    def register(self, parser: BaseParser) -> None:
        """Add a parser to the registry."""
        self._parsers.append(parser)
        for ext in parser.supported_extensions:
            self._ext_cache[ext.lower()] = parser
        logger.debug("Parser registered", language=parser.language.value)

    def get_by_extension(self, extension: str) -> Optional[BaseParser]:
        """Return the parser that handles the given file extension."""
        return self._ext_cache.get(extension.lower())

    def get_by_language(self, language: str) -> Optional[BaseParser]:
        """Return the parser for the given language name."""
        for parser in self._parsers:
            if parser.supports(language):
                return parser
        return None

    def get_for_file(self, file_path: str) -> Optional[BaseParser]:
        """Infer and return the parser for a file path based on its extension."""
        ext = Path(file_path).suffix.lower()
        return self.get_by_extension(ext)

    def detect_language(self, file_path: str) -> SupportedLanguage:
        """Detect the programming language from a file path."""
        parser = self.get_for_file(file_path)
        return parser.language if parser else SupportedLanguage.UNKNOWN

    def supported_extensions(self) -> List[str]:
        """Return all file extensions the factory can parse."""
        return list(self._ext_cache.keys())


def build_default_factory() -> ParserFactory:
    """Build and return a factory pre-loaded with all built-in parsers."""
    factory = ParserFactory()
    factory.register(PythonParser())
    factory.register(JavaScriptParser())
    return factory


# Module-level singleton
_factory: Optional[ParserFactory] = None


def get_parser_factory() -> ParserFactory:
    """Return the shared parser factory instance."""
    global _factory
    if _factory is None:
        _factory = build_default_factory()
    return _factory

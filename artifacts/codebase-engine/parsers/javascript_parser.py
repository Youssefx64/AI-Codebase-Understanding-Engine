"""JavaScript / TypeScript parser using regex-based heuristics.

A full JS AST parser (e.g. esprima) would require a Node.js bridge,
so this implementation uses well-targeted regular expressions to extract
the most useful structural information: imports, exports, functions, and classes.
The results are sufficient for dependency graph construction and chunking.
"""

import re
from typing import List, Optional

from domain.models import (
    ClassInfo,
    FileAnalysis,
    FunctionInfo,
    ImportInfo,
    SupportedLanguage,
)
from parsers.base_parser import BaseParser

# ── Compiled patterns ──────────────────────────────────────────────────────────

_RE_IMPORT = re.compile(
    r"""
    (?:import\s+                          # import keyword
      (?:
        (?:\{[^}]*\}|\*\s+as\s+\w+|\w+)  # named / namespace / default
        \s*,?\s*
      )*
      \s*from\s+['"]([^'"]+)['"]          # from 'module'
    |
      require\(['"]([^'"]+)['"]\)          # require('module')
    )
    """,
    re.VERBOSE,
)

_RE_FUNCTION = re.compile(
    r"""
    (?:export\s+)?                        # optional export
    (?:async\s+)?                         # optional async
    (?:function\*?\s+(\w+)               # named function
    |
    (?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\(.*?\)\s*=>))
    """,
    re.VERBOSE,
)

_RE_CLASS = re.compile(
    r"(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?"
)

_RE_ARROW = re.compile(
    r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\("
)


class JavaScriptParser(BaseParser):
    """Regex-based parser for JavaScript and TypeScript files."""

    @property
    def supported_extensions(self) -> List[str]:
        return [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]

    @property
    def language(self) -> SupportedLanguage:
        return SupportedLanguage.JAVASCRIPT

    def _parse_content(self, file_path: str, content: str) -> FileAnalysis:
        lines = content.splitlines()

        imports = self._extract_imports(content)
        functions = self._extract_functions(content, file_path, lines)
        classes = self._extract_classes(content, file_path, lines)

        loc = self.count_lines(content)

        return FileAnalysis(
            file_path=file_path,
            language=self.language,
            lines_of_code=loc,
            functions=functions,
            classes=classes,
            imports=imports,
            complexity_score=float(len(functions) + len(classes)),
        )

    def _extract_imports(self, content: str) -> List[ImportInfo]:
        results: List[ImportInfo] = []
        for i, line in enumerate(content.splitlines(), 1):
            for m in _RE_IMPORT.finditer(line):
                module = m.group(1) or m.group(2) or ""
                results.append(
                    ImportInfo(
                        module=module,
                        names=[],
                        is_from_import="from" in line,
                        line=i,
                    )
                )
        return results

    def _extract_functions(
        self, content: str, file_path: str, lines: List[str]
    ) -> List[FunctionInfo]:
        results: List[FunctionInfo] = []
        for i, line in enumerate(lines, 1):
            m = _RE_FUNCTION.search(line) or _RE_ARROW.search(line)
            if m:
                name = next((g for g in m.groups() if g), None)
                if not name or name in ("if", "for", "while", "switch"):
                    continue
                is_async = "async" in line
                results.append(
                    FunctionInfo(
                        name=name,
                        file_path=file_path,
                        start_line=i,
                        end_line=i,
                        is_async=is_async,
                    )
                )
        return results

    def _extract_classes(
        self, content: str, file_path: str, lines: List[str]
    ) -> List[ClassInfo]:
        results: List[ClassInfo] = []
        for i, line in enumerate(lines, 1):
            m = _RE_CLASS.search(line)
            if m:
                name = m.group(1)
                base = m.group(2)
                results.append(
                    ClassInfo(
                        name=name,
                        file_path=file_path,
                        start_line=i,
                        end_line=i,
                        bases=[base] if base else [],
                    )
                )
        return results

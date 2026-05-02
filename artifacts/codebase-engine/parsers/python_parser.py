"""Python AST parser using the stdlib ``ast`` module.

Implements the Visitor Pattern by walking the AST tree with dedicated
``visit_*`` methods for each node type, matching the standard ast.NodeVisitor
contract.
"""

import ast
from typing import Any, Dict, List, Optional, Set

from domain.models import (
    ClassInfo,
    FileAnalysis,
    FunctionInfo,
    ImportInfo,
    SupportedLanguage,
)
from parsers.base_parser import BaseParser


class _ASTVisitor(ast.NodeVisitor):
    """
    Visitor Pattern implementation: collects structural information while
    walking the Python AST.
    """

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.functions: List[FunctionInfo] = []
        self.classes: List[ClassInfo] = []
        self.imports: List[ImportInfo] = []
        self._current_class: Optional[ClassInfo] = None

    # ── Import visitors ────────────────────────────────────────────────────────

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(
                ImportInfo(
                    module=alias.name,
                    names=[],
                    is_from_import=False,
                    line=node.lineno,
                    alias=alias.asname,
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.imports.append(
            ImportInfo(
                module=node.module or "",
                names=[alias.name for alias in node.names],
                is_from_import=True,
                line=node.lineno,
            )
        )
        self.generic_visit(node)

    # ── Class visitor ──────────────────────────────────────────────────────────

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{_unparse_attr(base)}")

        class_info = ClassInfo(
            name=node.name,
            file_path=self.file_path,
            start_line=node.lineno,
            end_line=getattr(node, "end_lineno", node.lineno),
            docstring=BaseParser.extract_docstring(node.body),
            bases=bases,
        )

        prev = self._current_class
        self._current_class = class_info
        self.generic_visit(node)
        self._current_class = prev

        # Collect attribute assignments from __init__
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    ):
                        attr = target.attr
                        if attr not in class_info.attributes:
                            class_info.attributes.append(attr)

        self.classes.append(class_info)

    # ── Function visitors ──────────────────────────────────────────────────────

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node, is_async=True)

    def _visit_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool
    ) -> None:
        args = [a.arg for a in node.args.args]

        return_type: Optional[str] = None
        if node.returns:
            try:
                return_type = ast.unparse(node.returns)
            except Exception:
                pass

        decorators = []
        for dec in node.decorator_list:
            try:
                decorators.append(ast.unparse(dec))
            except Exception:
                pass

        # Collect calls made within this function body
        calls: List[str] = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                try:
                    calls.append(ast.unparse(child.func))
                except Exception:
                    pass

        complexity = _cyclomatic_complexity(node)

        func_info = FunctionInfo(
            name=node.name,
            file_path=self.file_path,
            start_line=node.lineno,
            end_line=getattr(node, "end_lineno", node.lineno),
            docstring=BaseParser.extract_docstring(node.body),
            arguments=args,
            return_type=return_type,
            calls=list(set(calls)),
            decorators=decorators,
            is_async=is_async,
            complexity=complexity,
        )

        if self._current_class:
            self._current_class.methods.append(func_info)
        else:
            self.functions.append(func_info)

        self.generic_visit(node)


def _unparse_attr(node: ast.Attribute) -> str:
    """Recursively unparse an attribute access (e.g. a.b.c)."""
    if isinstance(node.value, ast.Attribute):
        return f"{_unparse_attr(node.value)}.{node.attr}"
    if isinstance(node.value, ast.Name):
        return f"{node.value.id}.{node.attr}"
    return node.attr


def _cyclomatic_complexity(node: ast.AST) -> int:
    """
    Approximate cyclomatic complexity by counting branching constructs.
    McCabe's formula: 1 + number of branches.
    """
    count = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                               ast.With, ast.AsyncWith, ast.AsyncFor)):
            count += 1
        elif isinstance(child, ast.BoolOp):
            count += len(child.values) - 1
    return count


class PythonParser(BaseParser):
    """Parser for Python 3 source files using the stdlib ast module."""

    @property
    def supported_extensions(self) -> List[str]:
        return [".py", ".pyw"]

    @property
    def language(self) -> SupportedLanguage:
        return SupportedLanguage.PYTHON

    def _parse_content(self, file_path: str, content: str) -> FileAnalysis:
        tree = ast.parse(content, filename=file_path)
        visitor = _ASTVisitor(file_path)
        visitor.visit(tree)

        loc = self.count_lines(content)

        avg_complexity = (
            sum(f.complexity for f in visitor.functions) / len(visitor.functions)
            if visitor.functions
            else 0.0
        )

        return FileAnalysis(
            file_path=file_path,
            language=self.language,
            lines_of_code=loc,
            functions=visitor.functions,
            classes=visitor.classes,
            imports=visitor.imports,
            complexity_score=round(avg_complexity, 2),
        )

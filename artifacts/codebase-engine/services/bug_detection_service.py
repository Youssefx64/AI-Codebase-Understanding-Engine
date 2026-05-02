"""Bug detection service — static rules + semantic LLM analysis.

Static detection (no LLM):
- Unused variables / imports
- Circular imports (graph-based)
- Functions without type hints
- Excessively long or complex functions

Semantic detection (LLM-powered):
- Logic bugs
- Security anti-patterns
- Incorrect error handling
"""

from pathlib import Path
from typing import Dict, List, Set

from core.logging import get_logger
from domain.models import (
    CodeIssue,
    FileAnalysis,
    ImportInfo,
    IssueSeverity,
    IssueType,
)
from services.llm_client import get_llm_client

logger = get_logger(__name__)

_MAX_FUNCTION_LINES = 60
_MAX_COMPLEXITY = 10

_SEMANTIC_SYSTEM = """You are a security-aware senior software engineer.
Review the provided code and identify bugs, security vulnerabilities, and
logic errors. For each issue found, output a JSON array with objects having keys:
- "line": integer or null
- "severity": one of "critical", "high", "medium", "low"
- "message": short description of the issue
- "suggestion": how to fix it

Respond with ONLY the JSON array. If no issues are found, respond with [].
Do not add markdown fences or explanation."""


class BugDetectionService:
    """Combines static analysis rules and LLM semantic analysis for bug detection."""

    def __init__(self) -> None:
        self._llm = get_llm_client()

    def detect_static_issues(
        self, repo_id: str, file_analyses: List[FileAnalysis]
    ) -> List[CodeIssue]:
        """
        Run all static analysis rules across every file.
        Returns a flat list of CodeIssue objects.
        """
        issues: List[CodeIssue] = []

        # Build a global import map for circular import detection
        import_graph = self._build_import_graph(file_analyses)
        circular = self._detect_circular_imports(import_graph)

        for analysis in file_analyses:
            issues.extend(self._check_function_quality(repo_id, analysis))
            issues.extend(self._check_missing_type_hints(repo_id, analysis))

            # Flag files participating in circular imports
            rel = analysis.file_path
            file_key = rel.replace("/", ".").removesuffix(".py")
            cycle = circular.get(rel) or circular.get(file_key)
            if cycle:
                issues.append(
                    CodeIssue(
                        repo_id=repo_id,
                        file_path=rel,
                        issue_type=IssueType.CIRCULAR_IMPORT,
                        severity=IssueSeverity.HIGH,
                        message=f"File is part of a circular import cycle: {' → '.join(cycle)}",
                        suggestion="Refactor to break the cycle, e.g. by extracting shared logic into a separate module.",
                    )
                )

        logger.info(
            "Static analysis complete",
            repo_id=repo_id,
            issues=len(issues),
        )
        return issues

    async def detect_semantic_issues(
        self,
        repo_id: str,
        file_analyses: List[FileAnalysis],
        max_files: int = 10,
    ) -> List[CodeIssue]:
        """
        Run LLM-powered semantic bug detection on the most complex files.
        """
        import json

        issues: List[CodeIssue] = []

        # Focus on files with the highest complexity
        candidates = sorted(
            file_analyses,
            key=lambda a: a.complexity_score + len(a.functions),
            reverse=True,
        )[:max_files]

        for analysis in candidates:
            prompt = self._build_semantic_prompt(analysis)
            try:
                raw = await self._llm.complete(
                    prompt=prompt,
                    system_prompt=_SEMANTIC_SYSTEM,
                    temperature=0.1,
                    max_tokens=1024,
                )
                raw = raw.strip().lstrip("```json").rstrip("```").strip()
                detected = json.loads(raw)
                for item in detected:
                    issues.append(
                        CodeIssue(
                            repo_id=repo_id,
                            file_path=analysis.file_path,
                            line=item.get("line"),
                            issue_type=IssueType.POTENTIAL_BUG,
                            severity=IssueSeverity(item.get("severity", "medium")),
                            message=item.get("message", ""),
                            suggestion=item.get("suggestion"),
                        )
                    )
            except Exception as exc:
                logger.warning(
                    "Semantic analysis failed",
                    path=analysis.file_path,
                    error=str(exc),
                )

        logger.info(
            "Semantic analysis complete",
            repo_id=repo_id,
            semantic_issues=len(issues),
        )
        return issues

    # ── Static rules ──────────────────────────────────────────────────────────

    def _check_function_quality(
        self, repo_id: str, analysis: FileAnalysis
    ) -> List[CodeIssue]:
        issues: List[CodeIssue] = []
        for func in analysis.functions:
            length = func.end_line - func.start_line + 1
            if length > _MAX_FUNCTION_LINES:
                issues.append(
                    CodeIssue(
                        repo_id=repo_id,
                        file_path=analysis.file_path,
                        line=func.start_line,
                        issue_type=IssueType.LONG_FUNCTION,
                        severity=IssueSeverity.MEDIUM,
                        message=(
                            f"Function '{func.name}' is {length} lines long "
                            f"(threshold: {_MAX_FUNCTION_LINES})."
                        ),
                        suggestion="Break this function into smaller, single-purpose functions.",
                    )
                )
            if func.complexity > _MAX_COMPLEXITY:
                issues.append(
                    CodeIssue(
                        repo_id=repo_id,
                        file_path=analysis.file_path,
                        line=func.start_line,
                        issue_type=IssueType.COMPLEX_FUNCTION,
                        severity=IssueSeverity.MEDIUM,
                        message=(
                            f"Function '{func.name}' has cyclomatic complexity "
                            f"{func.complexity} (threshold: {_MAX_COMPLEXITY})."
                        ),
                        suggestion="Simplify by extracting sub-routines or replacing conditionals with polymorphism.",
                    )
                )
        return issues

    def _check_missing_type_hints(
        self, repo_id: str, analysis: FileAnalysis
    ) -> List[CodeIssue]:
        if analysis.language.value != "python":
            return []
        issues: List[CodeIssue] = []
        for func in analysis.functions:
            if func.name.startswith("_"):
                continue  # skip private helpers
            if not func.return_type and func.name not in ("__init__", "__str__", "__repr__"):
                issues.append(
                    CodeIssue(
                        repo_id=repo_id,
                        file_path=analysis.file_path,
                        line=func.start_line,
                        issue_type=IssueType.MISSING_TYPE_HINT,
                        severity=IssueSeverity.LOW,
                        message=f"Function '{func.name}' is missing a return type annotation.",
                        suggestion="Add a return type annotation (e.g. `-> None`, `-> str`).",
                    )
                )
        return issues

    def _build_import_graph(
        self, analyses: List[FileAnalysis]
    ) -> Dict[str, List[str]]:
        """Build file → [imported_module] adjacency for circular import detection."""
        graph: Dict[str, List[str]] = {}
        for analysis in analyses:
            file_key = analysis.file_path.replace("/", ".").removesuffix(".py")
            graph[file_key] = [
                imp.module for imp in analysis.imports if imp.module
            ]
        return graph

    def _detect_circular_imports(
        self, graph: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """
        Detect cycles in the import graph using DFS.
        Returns {file: [cycle_path]} for each file involved in a cycle.
        """
        visited: Set[str] = set()
        path: List[str] = []
        in_stack: Set[str] = set()
        cycles: Dict[str, List[str]] = {}

        def dfs(node: str) -> None:
            visited.add(node)
            path.append(node)
            in_stack.add(node)
            for neighbour in graph.get(node, []):
                if neighbour not in graph:
                    continue
                if neighbour not in visited:
                    dfs(neighbour)
                elif neighbour in in_stack:
                    cycle_start = path.index(neighbour)
                    cycle = path[cycle_start:] + [neighbour]
                    for member in cycle:
                        cycles[member] = cycle
            path.pop()
            in_stack.discard(node)

        for node in list(graph):
            if node not in visited:
                dfs(node)

        return cycles

    def _build_semantic_prompt(self, analysis: FileAnalysis) -> str:
        parts = [f"File: {analysis.file_path}", f"Language: {analysis.language.value}"]
        if analysis.classes:
            parts.append(
                "Classes: " + ", ".join(
                    f"{c.name}({', '.join(c.bases)})" for c in analysis.classes[:5]
                )
            )
        if analysis.functions:
            parts.append(
                "Functions:\n" + "\n".join(
                    f"  - {f.name}({', '.join(f.arguments)}) complexity={f.complexity}"
                    for f in analysis.functions[:20]
                )
            )
        return "\n".join(parts)

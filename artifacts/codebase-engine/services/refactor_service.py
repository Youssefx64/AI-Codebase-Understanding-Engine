"""Refactoring suggestions service.

Combines static structural analysis (code-smell detection) with
LLM-powered pattern recommendations.
"""

import json
from typing import List

from core.logging import get_logger
from domain.models import FileAnalysis, RefactorSuggestion
from services.llm_client import get_llm_client

logger = get_logger(__name__)

_REFACTOR_SYSTEM = """You are a senior software architect specialising in clean code and design patterns.
Review the provided code structure and suggest concrete refactoring improvements.

Respond with a JSON array. Each element must have:
- "title": short title of the suggestion (≤ 60 chars)
- "description": detailed explanation of what to change and why
- "pattern": design pattern or principle being applied (e.g. "Single Responsibility", "Factory", "Strategy")
- "effort": one of "low", "medium", "high"
- "start_line": integer or null
- "end_line": integer or null

Respond with ONLY the JSON array. Max 5 suggestions per file.
If no meaningful refactoring is needed, respond with []."""


class RefactorService:
    """Produces refactoring suggestions via static rules and LLM analysis."""

    def __init__(self) -> None:
        self._llm = get_llm_client()

    def detect_static_smells(
        self, repo_id: str, file_analyses: List[FileAnalysis]
    ) -> List[RefactorSuggestion]:
        """
        Identify structural code smells without calling the LLM.
        """
        suggestions: List[RefactorSuggestion] = []
        for analysis in file_analyses:
            suggestions.extend(self._check_god_class(repo_id, analysis))
            suggestions.extend(self._check_duplicate_logic(repo_id, analysis))
            suggestions.extend(self._check_feature_envy(repo_id, analysis))
        logger.info(
            "Static smell detection complete",
            repo_id=repo_id,
            suggestions=len(suggestions),
        )
        return suggestions

    async def generate_llm_suggestions(
        self,
        repo_id: str,
        file_analyses: List[FileAnalysis],
        max_files: int = 8,
    ) -> List[RefactorSuggestion]:
        """
        Use the LLM to generate design-pattern and architectural suggestions.
        """
        suggestions: List[RefactorSuggestion] = []

        candidates = sorted(
            file_analyses,
            key=lambda a: len(a.functions) + len(a.classes) * 3,
            reverse=True,
        )[:max_files]

        for analysis in candidates:
            prompt = self._build_prompt(analysis)
            try:
                raw = await self._llm.complete(
                    prompt=prompt,
                    system_prompt=_REFACTOR_SYSTEM,
                    temperature=0.3,
                    max_tokens=1024,
                )
                raw = raw.strip().lstrip("```json").rstrip("```").strip()
                items = json.loads(raw)
                for item in items:
                    suggestions.append(
                        RefactorSuggestion(
                            repo_id=repo_id,
                            file_path=analysis.file_path,
                            start_line=item.get("start_line"),
                            end_line=item.get("end_line"),
                            title=item.get("title", "Refactoring suggestion"),
                            description=item.get("description", ""),
                            pattern=item.get("pattern"),
                            effort=item.get("effort", "medium"),
                        )
                    )
            except Exception as exc:
                logger.warning(
                    "LLM refactor failed",
                    path=analysis.file_path,
                    error=str(exc),
                )

        logger.info(
            "LLM refactor suggestions generated",
            repo_id=repo_id,
            count=len(suggestions),
        )
        return suggestions

    # ── Static smell detectors ────────────────────────────────────────────────

    def _check_god_class(
        self, repo_id: str, analysis: FileAnalysis
    ) -> List[RefactorSuggestion]:
        suggestions = []
        for cls in analysis.classes:
            if len(cls.methods) > 15:
                suggestions.append(
                    RefactorSuggestion(
                        repo_id=repo_id,
                        file_path=analysis.file_path,
                        start_line=cls.start_line,
                        end_line=cls.end_line,
                        title=f"God Class: '{cls.name}' has {len(cls.methods)} methods",
                        description=(
                            f"Class '{cls.name}' is doing too much ({len(cls.methods)} methods). "
                            "Split it into smaller, single-responsibility classes."
                        ),
                        pattern="Single Responsibility Principle",
                        effort="high",
                    )
                )
        return suggestions

    def _check_duplicate_logic(
        self, repo_id: str, analysis: FileAnalysis
    ) -> List[RefactorSuggestion]:
        suggestions = []
        # Detect functions with similar names as a proxy for duplication
        func_names = [f.name for f in analysis.functions]
        seen: dict = {}
        for name in func_names:
            base = name.rstrip("0123456789_v")
            seen.setdefault(base, []).append(name)
        for base, names in seen.items():
            if len(names) >= 3:
                suggestions.append(
                    RefactorSuggestion(
                        repo_id=repo_id,
                        file_path=analysis.file_path,
                        title=f"Possible duplicate logic: {', '.join(names[:3])}",
                        description=(
                            f"Functions {names} appear to share similar naming, "
                            "suggesting duplicated logic. Consider extracting common behaviour."
                        ),
                        pattern="DRY Principle",
                        effort="medium",
                    )
                )
        return suggestions

    def _check_feature_envy(
        self, repo_id: str, analysis: FileAnalysis
    ) -> List[RefactorSuggestion]:
        suggestions = []
        for func in analysis.functions:
            # A function that calls many methods on a single external object
            # is likely suffering from Feature Envy
            call_prefixes: dict = {}
            for call in func.calls:
                if "." in call:
                    obj = call.split(".")[0]
                    call_prefixes[obj] = call_prefixes.get(obj, 0) + 1
            for obj, count in call_prefixes.items():
                if count >= 4 and obj not in ("self", "cls", "super"):
                    suggestions.append(
                        RefactorSuggestion(
                            repo_id=repo_id,
                            file_path=analysis.file_path,
                            start_line=func.start_line,
                            title=f"Feature Envy in '{func.name}' (calls '{obj}' {count}×)",
                            description=(
                                f"'{func.name}' heavily uses '{obj}' ({count} calls). "
                                "Consider moving this logic closer to '{obj}'."
                            ),
                            pattern="Feature Envy",
                            effort="medium",
                        )
                    )
        return suggestions

    def _build_prompt(self, analysis: FileAnalysis) -> str:
        parts = [f"File: {analysis.file_path}", f"Language: {analysis.language.value}"]
        if analysis.classes:
            for cls in analysis.classes[:5]:
                method_names = [m.name for m in cls.methods[:10]]
                parts.append(
                    f"Class '{cls.name}' (bases: {cls.bases}) "
                    f"methods: {method_names}"
                )
        if analysis.functions:
            for func in analysis.functions[:10]:
                parts.append(
                    f"Function '{func.name}'({', '.join(func.arguments)}) "
                    f"complexity={func.complexity} lines={func.end_line - func.start_line + 1}"
                )
        return "\n".join(parts)

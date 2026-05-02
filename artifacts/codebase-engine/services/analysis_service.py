"""Code understanding and architecture summary service.

Uses the LLM to generate:
- Per-file summaries
- Module/directory summaries
- A whole-repository architecture explanation
"""

from pathlib import Path
from typing import Dict, List

from core.logging import get_logger
from domain.models import FileAnalysis
from services.llm_client import get_llm_client

logger = get_logger(__name__)

_FILE_SUMMARY_SYSTEM = """You are a senior software engineer.
Summarise the following source file in 2-4 sentences.
Focus on: purpose, key classes/functions, and notable patterns.
Be concise and precise. Do not repeat the file path in the summary."""

_ARCH_SYSTEM = """You are a principal engineer performing a code review.
Given the file-level summaries for a repository, produce a structured
architecture overview covering:
1. High-level purpose of the project
2. Major components and their responsibilities
3. Key design patterns or architectural styles observed
4. Data flow / request lifecycle (if applicable)
5. Notable strengths and potential concerns

Keep the overview under 600 words. Use Markdown headings."""


class AnalysisService:
    """Generates natural-language summaries at file, module, and repo level."""

    def __init__(self) -> None:
        self._llm = get_llm_client()

    async def summarise_file(self, analysis: FileAnalysis) -> str:
        """Return a 2-4 sentence natural language summary for a single file."""
        prompt = self._build_file_prompt(analysis)
        try:
            summary = await self._llm.complete(
                prompt=prompt,
                system_prompt=_FILE_SUMMARY_SYSTEM,
                temperature=0.1,
                max_tokens=256,
            )
            return summary.strip()
        except Exception as exc:
            logger.warning("File summary failed", path=analysis.file_path, error=str(exc))
            return f"File: {analysis.file_path} ({analysis.language.value}, {analysis.lines_of_code} LOC)"

    async def summarise_repository(
        self, github_url: str, file_analyses: List[FileAnalysis]
    ) -> str:
        """
        Generate a full architecture explanation for the repository.

        Summarises up to 40 representative files to keep the prompt manageable.
        """
        # Select representative files (limit LLM context)
        selected = self._select_representative_files(file_analyses)

        file_summaries: List[str] = []
        for analysis in selected:
            summary = await self.summarise_file(analysis)
            analysis.summary = summary
            file_summaries.append(f"**{analysis.file_path}**: {summary}")

        combined = "\n".join(file_summaries)
        prompt = (
            f"Repository: {github_url}\n\n"
            f"File Summaries ({len(selected)} files):\n{combined}\n\n"
            "Produce a structured architecture overview as described."
        )

        arch_summary = await self._llm.complete(
            prompt=prompt,
            system_prompt=_ARCH_SYSTEM,
            temperature=0.2,
            max_tokens=2048,
        )

        logger.info(
            "Architecture summary generated",
            url=github_url,
            files_analysed=len(selected),
        )
        return arch_summary.strip()

    def _select_representative_files(
        self, analyses: List[FileAnalysis], max_files: int = 40
    ) -> List[FileAnalysis]:
        """
        Select up to ``max_files`` representative files.

        Priority: files with most functions + classes (highest structural density).
        """
        scored = sorted(
            analyses,
            key=lambda a: len(a.functions) + len(a.classes) * 2,
            reverse=True,
        )
        return scored[:max_files]

    def _build_file_prompt(self, analysis: FileAnalysis) -> str:
        parts = [f"File: {analysis.file_path}", f"Language: {analysis.language.value}"]

        if analysis.classes:
            class_names = ", ".join(c.name for c in analysis.classes[:10])
            parts.append(f"Classes: {class_names}")

        if analysis.functions:
            func_names = ", ".join(f.name for f in analysis.functions[:15])
            parts.append(f"Functions: {func_names}")

        if analysis.imports:
            import_mods = ", ".join(i.module for i in analysis.imports[:10])
            parts.append(f"Imports: {import_mods}")

        return "\n".join(parts)

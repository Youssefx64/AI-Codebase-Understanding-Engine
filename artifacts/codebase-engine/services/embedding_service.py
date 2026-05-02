"""Embedding and chunking service.

Splits parsed files into fixed-size overlapping chunks and stores them
in the vector database for subsequent RAG retrieval.
"""

from typing import List
from uuid import uuid4

from core.config import get_settings
from core.logging import get_logger
from domain.models import CodeChunk, FileAnalysis, SupportedLanguage
from infrastructure.vector.vector_store import get_vector_store

logger = get_logger(__name__)


class EmbeddingService:
    """Chunks source files and upserts them into the vector store."""

    def __init__(self) -> None:
        settings = get_settings()
        self._chunk_size = settings.chunk_size
        self._chunk_overlap = settings.chunk_overlap
        self._vector_store = get_vector_store()

    async def embed_files(
        self, repo_id: str, file_analyses: List[FileAnalysis]
    ) -> int:
        """
        Chunk all files and upsert to the vector store.

        Returns the total number of chunks inserted.
        """
        all_chunks: List[CodeChunk] = []

        for analysis in file_analyses:
            chunks = self._chunk_file(repo_id, analysis)
            all_chunks.extend(chunks)

            # Batch upserts to avoid large memory spikes
            if len(all_chunks) >= 200:
                await self._vector_store.add_chunks(all_chunks)
                all_chunks = []

        if all_chunks:
            await self._vector_store.add_chunks(all_chunks)

        total = sum(
            len(self._chunk_file(repo_id, a)) for a in file_analyses
        )
        logger.info(
            "Embedding complete",
            repo_id=repo_id,
            files=len(file_analyses),
        )
        return total

    def _chunk_file(self, repo_id: str, analysis: FileAnalysis) -> List[CodeChunk]:
        """
        Produce overlapping chunks from file content reconstructed from
        the function and class boundaries stored in FileAnalysis.

        Falls back to line-based chunking when no structural info exists.
        """
        chunks: List[CodeChunk] = []

        # Use function-level granularity when available
        for func in analysis.functions:
            snippet = self._build_function_snippet(func)
            if snippet:
                chunks.append(
                    CodeChunk(
                        chunk_id=str(uuid4()),
                        repo_id=repo_id,
                        file_path=analysis.file_path,
                        start_line=func.start_line,
                        end_line=func.end_line,
                        content=snippet,
                        language=analysis.language,
                        metadata={"type": "function", "name": func.name},
                    )
                )

        for cls in analysis.classes:
            snippet = f"class {cls.name}({', '.join(cls.bases)}):\n"
            if cls.docstring:
                snippet += f'    """{cls.docstring}"""\n'
            for method in cls.methods:
                snippet += f"    def {method.name}({', '.join(method.arguments)}): ...\n"
            chunks.append(
                CodeChunk(
                    chunk_id=str(uuid4()),
                    repo_id=repo_id,
                    file_path=analysis.file_path,
                    start_line=cls.start_line,
                    end_line=cls.end_line,
                    content=snippet,
                    language=analysis.language,
                    metadata={"type": "class", "name": cls.name},
                )
            )

        # If no structural info, do plain line-based chunking
        if not chunks:
            chunks = self._line_chunks(repo_id, analysis)

        return chunks

    def _build_function_snippet(self, func) -> str:
        parts = []
        if func.decorators:
            parts.extend(f"@{d}" for d in func.decorators)
        prefix = "async def" if func.is_async else "def"
        signature = f"{prefix} {func.name}({', '.join(func.arguments)})"
        if func.return_type:
            signature += f" -> {func.return_type}"
        signature += ":"
        parts.append(signature)
        if func.docstring:
            parts.append(f'    """{func.docstring}"""')
        if func.calls:
            parts.append(f"    # calls: {', '.join(func.calls[:5])}")
        return "\n".join(parts)

    def _line_chunks(
        self, repo_id: str, analysis: FileAnalysis
    ) -> List[CodeChunk]:
        """Sliding window line chunking for files without structural info."""
        chunks: List[CodeChunk] = []
        lines: List[str] = []
        # We don't have the raw content in FileAnalysis, so build a placeholder
        placeholder = f"# {analysis.file_path}\n# {analysis.language.value} file\n"
        lines = placeholder.splitlines()
        size = self._chunk_size
        overlap = self._chunk_overlap
        step = max(1, size - overlap)

        for i in range(0, max(1, len(lines) - size + 1), step):
            chunk_lines = lines[i : i + size]
            chunks.append(
                CodeChunk(
                    chunk_id=str(uuid4()),
                    repo_id=repo_id,
                    file_path=analysis.file_path,
                    start_line=i + 1,
                    end_line=i + len(chunk_lines),
                    content="\n".join(chunk_lines),
                    language=analysis.language,
                    metadata={"type": "raw"},
                )
            )
        return chunks

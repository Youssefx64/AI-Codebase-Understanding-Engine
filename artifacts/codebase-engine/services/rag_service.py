"""RAG (Retrieval-Augmented Generation) service.

Retrieves the most relevant code chunks for a developer question,
then constructs a prompt and asks the LLM to answer using that context.
"""

from typing import Any, Dict, List

from core.exceptions import RepositoryNotFoundError
from core.logging import get_logger
from domain.models import AskResponse
from infrastructure.database.repositories.repo_repository import PostgresRepositoryStore
from infrastructure.vector.vector_store import get_vector_store
from services.llm_client import get_llm_client

logger = get_logger(__name__)

_SYSTEM_PROMPT = """You are an expert software engineer and code reviewer.
You have been given relevant source code snippets retrieved from a repository.
Answer the developer's question accurately and concisely, referencing specific
files and line numbers where relevant. If you are unsure, say so clearly.
Do not hallucinate code that is not present in the provided context."""


class RAGService:
    """Retrieves relevant code context and answers developer questions via LLM."""

    def __init__(self) -> None:
        self._vector_store = get_vector_store()
        self._llm = get_llm_client()
        self._repo_store = PostgresRepositoryStore()

    async def ask(
        self, repo_id: str, question: str, max_chunks: int = 5
    ) -> AskResponse:
        """
        Retrieve context for ``question`` from ``repo_id`` and generate an answer.
        """
        repo = await self._repo_store.get_by_id(repo_id)
        if not repo:
            raise RepositoryNotFoundError(repo_id)

        # Retrieve relevant chunks
        chunks = await self._vector_store.search(
            repo_id=repo_id, query=question, top_k=max_chunks
        )

        context = self._format_context(chunks)
        prompt = self._build_prompt(repo.github_url, question, context)

        answer = await self._llm.complete(
            prompt=prompt,
            system_prompt=_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=2048,
        )

        logger.info(
            "RAG answer generated",
            repo_id=repo_id,
            question_len=len(question),
            chunks_used=len(chunks),
        )

        return AskResponse(
            repo_id=repo_id,
            question=question,
            answer=answer,
            source_chunks=chunks,
        )

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        if not chunks:
            return "No relevant code context was found."
        parts = []
        for i, chunk in enumerate(chunks, 1):
            parts.append(
                f"[Chunk {i}] {chunk.get('file_path', '')} "
                f"lines {chunk.get('start_line', '?')}–{chunk.get('end_line', '?')} "
                f"(relevance: {chunk.get('score', 0):.2f})\n"
                f"```\n{chunk.get('content', '')}\n```"
            )
        return "\n\n".join(parts)

    def _build_prompt(self, repo_url: str, question: str, context: str) -> str:
        return f"""Repository: {repo_url}

Developer Question:
{question}

Relevant Code Context:
{context}

Please answer the question based on the code context provided above."""

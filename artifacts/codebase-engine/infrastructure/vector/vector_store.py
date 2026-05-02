"""Vector store implementation using ChromaDB for RAG retrieval.

ChromaDB is used with its default embedding function (sentence-transformers)
so no external embedding API key is required. The collection is namespaced
by repo_id to allow isolated searches per repository.
"""

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import get_settings
from core.exceptions import VectorStoreError
from core.logging import get_logger
from domain.interfaces import IVectorStore
from domain.models import CodeChunk

logger = get_logger(__name__)


class ChromaVectorStore(IVectorStore):
    """IVectorStore backed by ChromaDB with local sentence-transformer embeddings."""

    def __init__(self) -> None:
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            settings = get_settings()
            persist_dir = Path(settings.chroma_persist_dir)
            persist_dir.mkdir(parents=True, exist_ok=True)

            self._client = chromadb.PersistentClient(
                path=str(persist_dir),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            logger.info("ChromaDB initialised", path=str(persist_dir))
        except ImportError as exc:
            raise VectorStoreError(
                f"chromadb package not available: {exc}"
            ) from exc

    def _collection_name(self, repo_id: str) -> str:
        """Derive a safe ChromaDB collection name from a repo_id."""
        # ChromaDB collection names must be 3–63 chars, alphanumeric + hyphens
        safe = f"repo-{hashlib.md5(repo_id.encode()).hexdigest()[:16]}"
        return safe

    async def add_chunks(self, chunks: List[CodeChunk]) -> None:
        if not chunks:
            return
        try:
            col_name = self._collection_name(chunks[0].repo_id)
            collection = self._client.get_or_create_collection(
                name=col_name,
                metadata={"hnsw:space": "cosine"},
            )

            ids = [chunk.chunk_id for chunk in chunks]
            documents = [chunk.content for chunk in chunks]
            metadatas = [
                {
                    "repo_id": chunk.repo_id,
                    "file_path": chunk.file_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "language": chunk.language.value,
                    **{k: str(v) for k, v in chunk.metadata.items()},
                }
                for chunk in chunks
            ]

            # ChromaDB upsert handles duplicate chunk_ids
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            logger.debug("Chunks upserted", count=len(chunks), collection=col_name)
        except Exception as exc:
            raise VectorStoreError(f"Failed to add chunks: {exc}") from exc

    async def search(
        self, repo_id: str, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        try:
            col_name = self._collection_name(repo_id)
            try:
                collection = self._client.get_collection(col_name)
            except Exception:
                return []  # No chunks indexed yet

            results = collection.query(
                query_texts=[query],
                n_results=min(top_k, collection.count() or 1),
            )

            hits: List[Dict[str, Any]] = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    meta = results["metadatas"][0][i] if results.get("metadatas") else {}
                    distance = (
                        results["distances"][0][i] if results.get("distances") else 0.0
                    )
                    hits.append(
                        {
                            "content": doc,
                            "file_path": meta.get("file_path", ""),
                            "start_line": meta.get("start_line", 0),
                            "end_line": meta.get("end_line", 0),
                            "language": meta.get("language", ""),
                            "score": round(1 - distance, 4),
                        }
                    )
            return hits
        except Exception as exc:
            raise VectorStoreError(f"Search failed: {exc}") from exc

    async def delete_by_repo(self, repo_id: str) -> None:
        try:
            col_name = self._collection_name(repo_id)
            self._client.delete_collection(col_name)
            logger.debug("Vector collection deleted", repo_id=repo_id)
        except Exception:
            pass  # Collection may not exist


# Module-level singleton
_store: Optional[ChromaVectorStore] = None


def get_vector_store() -> ChromaVectorStore:
    """Return the module-level ChromaDB store instance."""
    global _store
    if _store is None:
        _store = ChromaVectorStore()
    return _store

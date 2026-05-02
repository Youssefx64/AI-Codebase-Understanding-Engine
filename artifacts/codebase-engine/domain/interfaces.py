"""Abstract interfaces (ports) following clean architecture / Repository Pattern."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from domain.models import (
    CodeChunk,
    CodeIssue,
    DependencyGraph,
    FileAnalysis,
    RefactorSuggestion,
    Repository,
)


class IRepositoryStore(ABC):
    """Port for persisting and retrieving Repository aggregates."""

    @abstractmethod
    async def save(self, repo: Repository) -> Repository:
        ...

    @abstractmethod
    async def get_by_id(self, repo_id: str) -> Optional[Repository]:
        ...

    @abstractmethod
    async def get_by_url(self, github_url: str) -> Optional[Repository]:
        ...

    @abstractmethod
    async def list_all(self, limit: int = 50, offset: int = 0) -> List[Repository]:
        ...

    @abstractmethod
    async def delete(self, repo_id: str) -> bool:
        ...


class IIssueStore(ABC):
    """Port for persisting detected code issues."""

    @abstractmethod
    async def save_bulk(self, issues: List[CodeIssue]) -> None:
        ...

    @abstractmethod
    async def get_by_repo(
        self, repo_id: str, severity: Optional[str] = None
    ) -> List[CodeIssue]:
        ...

    @abstractmethod
    async def delete_by_repo(self, repo_id: str) -> None:
        ...


class IRefactorStore(ABC):
    """Port for persisting refactoring suggestions."""

    @abstractmethod
    async def save_bulk(self, suggestions: List[RefactorSuggestion]) -> None:
        ...

    @abstractmethod
    async def get_by_repo(self, repo_id: str) -> List[RefactorSuggestion]:
        ...

    @abstractmethod
    async def delete_by_repo(self, repo_id: str) -> None:
        ...


class IVectorStore(ABC):
    """Port for storing and retrieving code embeddings (RAG)."""

    @abstractmethod
    async def add_chunks(self, chunks: List[CodeChunk]) -> None:
        ...

    @abstractmethod
    async def search(
        self, repo_id: str, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    async def delete_by_repo(self, repo_id: str) -> None:
        ...


class IGraphStore(ABC):
    """Port for storing and querying the dependency graph."""

    @abstractmethod
    async def save_graph(self, graph: DependencyGraph) -> None:
        ...

    @abstractmethod
    async def get_graph(self, repo_id: str) -> Optional[DependencyGraph]:
        ...

    @abstractmethod
    async def delete_graph(self, repo_id: str) -> None:
        ...


class ICodeParser(ABC):
    """Strategy interface for language-specific AST parsers."""

    @abstractmethod
    def supports(self, language: str) -> bool:
        ...

    @abstractmethod
    def parse_file(self, file_path: str, content: str) -> FileAnalysis:
        ...


class ILLMClient(ABC):
    """Port for LLM completion calls."""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        ...


class ICacheStore(ABC):
    """Port for cache reads/writes."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        ...

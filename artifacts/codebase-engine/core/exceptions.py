"""Custom application exceptions with structured error handling."""

from typing import Any, Optional


class AppError(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class RepositoryNotFoundError(AppError):
    """Raised when a repository record is not found."""

    def __init__(self, repo_id: str) -> None:
        super().__init__(
            message=f"Repository '{repo_id}' not found",
            code="REPO_NOT_FOUND",
            status_code=404,
        )


class RepositoryIngestionError(AppError):
    """Raised when repository cloning or ingestion fails."""

    def __init__(self, url: str, reason: str) -> None:
        super().__init__(
            message=f"Failed to ingest repository '{url}': {reason}",
            code="REPO_INGESTION_FAILED",
            status_code=422,
        )


class ParseError(AppError):
    """Raised when code parsing fails."""

    def __init__(self, file_path: str, reason: str) -> None:
        super().__init__(
            message=f"Failed to parse '{file_path}': {reason}",
            code="PARSE_ERROR",
            status_code=422,
        )


class UnsupportedLanguageError(AppError):
    """Raised when no parser exists for a detected language."""

    def __init__(self, language: str) -> None:
        super().__init__(
            message=f"No parser available for language: '{language}'",
            code="UNSUPPORTED_LANGUAGE",
            status_code=422,
        )


class AnalysisNotReadyError(AppError):
    """Raised when analysis results are requested before completion."""

    def __init__(self, repo_id: str) -> None:
        super().__init__(
            message=f"Analysis for repository '{repo_id}' is not yet complete",
            code="ANALYSIS_NOT_READY",
            status_code=202,
        )


class LLMError(AppError):
    """Raised on LLM API failures."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            message=f"LLM request failed: {reason}",
            code="LLM_ERROR",
            status_code=502,
        )


class VectorStoreError(AppError):
    """Raised on vector database failures."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            message=f"Vector store error: {reason}",
            code="VECTOR_STORE_ERROR",
            status_code=500,
        )


class GraphDBError(AppError):
    """Raised on graph database failures."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            message=f"Graph database error: {reason}",
            code="GRAPH_DB_ERROR",
            status_code=500,
        )

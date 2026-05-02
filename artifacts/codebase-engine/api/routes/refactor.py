"""GET /refactor/{id} — Retrieve refactoring suggestions for a repository."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from core.logging import get_logger
from domain.models import RefactorSuggestion
from infrastructure.cache.redis_cache import get_cache
from infrastructure.database.repositories.repo_repository import PostgresRefactorStore

router = APIRouter(prefix="/refactor", tags=["Refactor"])
logger = get_logger(__name__)

_CACHE_TTL = 300


@router.get(
    "/{repo_id}",
    response_model=List[RefactorSuggestion],
    summary="Get refactoring suggestions for a repository",
    description=(
        "Returns a prioritised list of refactoring opportunities identified "
        "by static analysis and LLM-powered pattern detection."
    ),
)
async def get_refactor_suggestions(
    repo_id: str,
    effort: Optional[str] = Query(
        default=None,
        description="Filter by effort level: low | medium | high",
    ),
    file_path: Optional[str] = Query(
        default=None,
        description="Filter by file path (substring match)",
    ),
) -> List[RefactorSuggestion]:
    cache = await get_cache()
    cache_key = f"refactor:{repo_id}:{effort}:{file_path}"

    cached = await cache.get(cache_key)
    if cached:
        return [RefactorSuggestion(**item) for item in cached]

    store = PostgresRefactorStore()
    suggestions = await store.get_by_repo(repo_id=repo_id)

    if not suggestions:
        from infrastructure.database.repositories.repo_repository import PostgresRepositoryStore
        repo_store = PostgresRepositoryStore()
        repo = await repo_store.get_by_id(repo_id)
        if not repo:
            raise HTTPException(
                status_code=404,
                detail=f"Repository '{repo_id}' not found.",
            )

    # Apply filters
    if effort:
        suggestions = [s for s in suggestions if s.effort == effort]
    if file_path:
        suggestions = [
            s for s in suggestions if file_path.lower() in s.file_path.lower()
        ]

    # Sort: low effort first (quick wins)
    _effort_order = {"low": 0, "medium": 1, "high": 2}
    suggestions.sort(key=lambda s: _effort_order.get(s.effort, 99))

    await cache.set(
        cache_key,
        [s.model_dump(mode="json") for s in suggestions],
        ttl=_CACHE_TTL,
    )
    return suggestions


@router.get(
    "/{repo_id}/by-pattern",
    summary="Group refactoring suggestions by design pattern",
)
async def get_refactor_by_pattern(repo_id: str) -> dict:
    store = PostgresRefactorStore()
    suggestions = await store.get_by_repo(repo_id=repo_id)
    grouped: dict = {}
    for s in suggestions:
        key = s.pattern or "General"
        grouped.setdefault(key, []).append(
            {"title": s.title, "file_path": s.file_path, "effort": s.effort}
        )
    return {"repo_id": repo_id, "patterns": grouped}

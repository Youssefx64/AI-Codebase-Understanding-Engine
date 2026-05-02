"""GET /repo-summary/{id} — Retrieve repository analysis summary."""

from fastapi import APIRouter, HTTPException, status

from core.exceptions import RepositoryNotFoundError
from core.logging import get_logger
from domain.models import RepoSummaryResponse
from infrastructure.cache.redis_cache import get_cache
from infrastructure.database.repositories.repo_repository import PostgresRepositoryStore

router = APIRouter(prefix="/repo-summary", tags=["Summary"])
logger = get_logger(__name__)

_CACHE_TTL = 300  # 5 minutes


@router.get(
    "/{repo_id}",
    response_model=RepoSummaryResponse,
    summary="Get repository analysis summary",
    description=(
        "Returns the current status and analysis results for a repository. "
        "Includes architecture summary once analysis is complete."
    ),
)
async def get_repo_summary(repo_id: str) -> RepoSummaryResponse:
    cache = await get_cache()
    cache_key = f"summary:{repo_id}"

    cached = await cache.get(cache_key)
    if cached:
        return RepoSummaryResponse(**cached)

    store = PostgresRepositoryStore()
    try:
        repo = await store.get_by_id(repo_id)
        if not repo:
            raise RepositoryNotFoundError(repo_id)
    except RepositoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc

    response = RepoSummaryResponse(
        repo_id=repo.repo_id,
        github_url=repo.github_url,
        status=repo.status,
        languages=[lang.value for lang in repo.languages],
        file_count=repo.file_count,
        total_lines=repo.total_lines,
        architecture_summary=repo.architecture_summary,
        created_at=repo.created_at,
        completed_at=repo.completed_at,
    )

    # Only cache completed results
    if repo.architecture_summary:
        await cache.set(cache_key, response.model_dump(mode="json"), ttl=_CACHE_TTL)

    return response


@router.get(
    "",
    response_model=list[RepoSummaryResponse],
    summary="List all analysed repositories",
)
async def list_repos(limit: int = 20, offset: int = 0) -> list[RepoSummaryResponse]:
    store = PostgresRepositoryStore()
    repos = await store.list_all(limit=limit, offset=offset)
    return [
        RepoSummaryResponse(
            repo_id=r.repo_id,
            github_url=r.github_url,
            status=r.status,
            languages=[lang.value for lang in r.languages],
            file_count=r.file_count,
            total_lines=r.total_lines,
            architecture_summary=r.architecture_summary,
            created_at=r.created_at,
            completed_at=r.completed_at,
        )
        for r in repos
    ]

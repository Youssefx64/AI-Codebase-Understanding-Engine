"""GET /issues/{id} — Retrieve detected code issues for a repository."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from core.logging import get_logger
from domain.models import CodeIssue, IssueSeverity
from infrastructure.cache.redis_cache import get_cache
from infrastructure.database.repositories.repo_repository import PostgresIssueStore

router = APIRouter(prefix="/issues", tags=["Issues"])
logger = get_logger(__name__)

_CACHE_TTL = 300


@router.get(
    "/{repo_id}",
    response_model=List[CodeIssue],
    summary="Get detected code issues for a repository",
    description=(
        "Returns all static and semantic issues detected during analysis. "
        "Optionally filter by severity level."
    ),
)
async def get_issues(
    repo_id: str,
    severity: Optional[IssueSeverity] = Query(
        default=None,
        description="Filter by severity: critical | high | medium | low | info",
    ),
    file_path: Optional[str] = Query(
        default=None,
        description="Filter by file path (substring match)",
    ),
) -> List[CodeIssue]:
    cache = await get_cache()
    cache_key = f"issues:{repo_id}:{severity}:{file_path}"

    cached = await cache.get(cache_key)
    if cached:
        return [CodeIssue(**item) for item in cached]

    store = PostgresIssueStore()
    issues = await store.get_by_repo(
        repo_id=repo_id,
        severity=severity.value if severity else None,
    )

    if not issues and not severity:
        # Distinguish between "no issues" and "wrong repo_id"
        from infrastructure.database.repositories.repo_repository import PostgresRepositoryStore
        repo_store = PostgresRepositoryStore()
        repo = await repo_store.get_by_id(repo_id)
        if not repo:
            raise HTTPException(
                status_code=404,
                detail=f"Repository '{repo_id}' not found.",
            )

    # Apply file_path filter
    if file_path:
        issues = [i for i in issues if file_path.lower() in i.file_path.lower()]

    # Sort: critical → high → medium → low → info
    _severity_order = {
        "critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4
    }
    issues.sort(key=lambda i: _severity_order.get(i.severity.value, 99))

    await cache.set(cache_key, [i.model_dump(mode="json") for i in issues], ttl=_CACHE_TTL)
    return issues


@router.get(
    "/{repo_id}/summary",
    summary="Get a summary of issue counts by severity",
)
async def get_issues_summary(repo_id: str) -> dict:
    store = PostgresIssueStore()
    all_issues = await store.get_by_repo(repo_id=repo_id)
    summary: dict = {"total": len(all_issues), "by_severity": {}, "by_type": {}}
    for issue in all_issues:
        sev = issue.severity.value
        itype = issue.issue_type.value
        summary["by_severity"][sev] = summary["by_severity"].get(sev, 0) + 1
        summary["by_type"][itype] = summary["by_type"].get(itype, 0) + 1
    return summary

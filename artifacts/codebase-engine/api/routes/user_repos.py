"""User-scoped repository management routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from api.routes.auth import get_current_user
from core.logging import get_logger
from infrastructure.database.orm_models import RepositoryORM, UserORM
from infrastructure.database.postgres import get_session

router = APIRouter(tags=["User Repos"])
logger = get_logger(__name__)


class RepoListItem(BaseModel):
    repo_id: str
    github_url: str
    owner: str
    name: str
    branch: str
    status: str
    file_count: int
    total_lines: int
    languages: List[str]
    created_at: str
    completed_at: Optional[str]


@router.get("/my-repos", response_model=List[RepoListItem])
async def list_my_repos(
    current_user: UserORM = Depends(get_current_user),
) -> List[RepoListItem]:
    """Return all repositories submitted by the authenticated user."""
    async with get_session() as session:
        result = await session.execute(
            select(RepositoryORM)
            .where(RepositoryORM.user_id == current_user.user_id)
            .order_by(RepositoryORM.created_at.desc())
        )
        rows = result.scalars().all()

    return [
        RepoListItem(
            repo_id=r.repo_id,
            github_url=r.github_url,
            owner=r.owner,
            name=r.name,
            branch=r.branch,
            status=r.status,
            file_count=r.file_count,
            total_lines=r.total_lines,
            languages=r.languages or [],
            created_at=r.created_at.isoformat(),
            completed_at=r.completed_at.isoformat() if r.completed_at else None,
        )
        for r in rows
    ]


@router.delete("/repo/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repo(
    repo_id: str,
    current_user: UserORM = Depends(get_current_user),
) -> None:
    """Delete a repository owned by the authenticated user."""
    async with get_session() as session:
        repo = await session.get(RepositoryORM, repo_id)
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        if repo.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not authorised to delete this repository")
        await session.delete(repo)

    logger.info("Repo deleted", repo_id=repo_id, user_id=current_user.user_id)

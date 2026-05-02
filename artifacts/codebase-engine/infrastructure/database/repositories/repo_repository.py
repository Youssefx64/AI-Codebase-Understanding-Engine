"""Concrete Repository Pattern implementations backed by PostgreSQL/SQLite."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import RepositoryNotFoundError
from core.logging import get_logger
from domain.interfaces import IIssueStore, IRefactorStore, IRepositoryStore
from domain.models import (
    AnalysisStatus,
    CodeIssue,
    IssueSeverity,
    IssueType,
    RefactorSuggestion,
    Repository,
)
from infrastructure.database.orm_models import IssueORM, RefactorORM, RepositoryORM
from infrastructure.database.postgres import get_session

logger = get_logger(__name__)


def _orm_to_repo(orm: RepositoryORM) -> Repository:
    """Map ORM row → domain Repository."""
    return Repository(
        repo_id=orm.repo_id,
        github_url=orm.github_url,
        owner=orm.owner,
        name=orm.name,
        branch=orm.branch,
        status=AnalysisStatus(orm.status),
        languages=orm.languages or [],
        file_count=orm.file_count,
        total_lines=orm.total_lines,
        architecture_summary=orm.architecture_summary,
        error_message=orm.error_message,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
        completed_at=orm.completed_at,
    )


def _repo_to_orm(repo: Repository) -> RepositoryORM:
    """Map domain Repository → ORM row."""
    return RepositoryORM(
        repo_id=repo.repo_id,
        github_url=repo.github_url,
        owner=repo.owner,
        name=repo.name,
        branch=repo.branch,
        status=repo.status.value,
        languages=[lang.value for lang in repo.languages],
        file_count=repo.file_count,
        total_lines=repo.total_lines,
        architecture_summary=repo.architecture_summary,
        error_message=repo.error_message,
        created_at=repo.created_at,
        updated_at=repo.updated_at,
        completed_at=repo.completed_at,
    )


class PostgresRepositoryStore(IRepositoryStore):
    """IRepositoryStore backed by PostgreSQL via SQLAlchemy."""

    async def save(self, repo: Repository) -> Repository:
        async with get_session() as session:
            existing = await session.get(RepositoryORM, repo.repo_id)
            if existing:
                existing.status = repo.status.value
                existing.languages = [l.value for l in repo.languages]
                existing.file_count = repo.file_count
                existing.total_lines = repo.total_lines
                existing.architecture_summary = repo.architecture_summary
                existing.error_message = repo.error_message
                existing.updated_at = datetime.utcnow()
                existing.completed_at = repo.completed_at
            else:
                session.add(_repo_to_orm(repo))
        logger.debug("Repo saved", repo_id=repo.repo_id, status=repo.status)
        return repo

    async def get_by_id(self, repo_id: str) -> Optional[Repository]:
        async with get_session() as session:
            orm = await session.get(RepositoryORM, repo_id)
            return _orm_to_repo(orm) if orm else None

    async def get_by_url(self, github_url: str) -> Optional[Repository]:
        async with get_session() as session:
            stmt = select(RepositoryORM).where(RepositoryORM.github_url == github_url)
            result = await session.execute(stmt)
            orm = result.scalar_one_or_none()
            return _orm_to_repo(orm) if orm else None

    async def list_all(self, limit: int = 50, offset: int = 0) -> List[Repository]:
        async with get_session() as session:
            stmt = (
                select(RepositoryORM)
                .order_by(RepositoryORM.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(stmt)
            return [_orm_to_repo(r) for r in result.scalars()]

    async def delete(self, repo_id: str) -> bool:
        async with get_session() as session:
            orm = await session.get(RepositoryORM, repo_id)
            if not orm:
                return False
            await session.delete(orm)
        return True


class PostgresIssueStore(IIssueStore):
    """IIssueStore backed by PostgreSQL."""

    async def save_bulk(self, issues: List[CodeIssue]) -> None:
        async with get_session() as session:
            for issue in issues:
                session.add(
                    IssueORM(
                        issue_id=issue.issue_id,
                        repo_id=issue.repo_id,
                        file_path=issue.file_path,
                        line=issue.line,
                        issue_type=issue.issue_type.value,
                        severity=issue.severity.value,
                        message=issue.message,
                        suggestion=issue.suggestion,
                        context=issue.context,
                    )
                )
        logger.debug("Saved issues", count=len(issues))

    async def get_by_repo(
        self, repo_id: str, severity: Optional[str] = None
    ) -> List[CodeIssue]:
        async with get_session() as session:
            stmt = select(IssueORM).where(IssueORM.repo_id == repo_id)
            if severity:
                stmt = stmt.where(IssueORM.severity == severity)
            result = await session.execute(stmt)
            return [
                CodeIssue(
                    issue_id=r.issue_id,
                    repo_id=r.repo_id,
                    file_path=r.file_path,
                    line=r.line,
                    issue_type=IssueType(r.issue_type),
                    severity=IssueSeverity(r.severity),
                    message=r.message,
                    suggestion=r.suggestion,
                    context=r.context,
                )
                for r in result.scalars()
            ]

    async def delete_by_repo(self, repo_id: str) -> None:
        async with get_session() as session:
            stmt = select(IssueORM).where(IssueORM.repo_id == repo_id)
            result = await session.execute(stmt)
            for row in result.scalars():
                await session.delete(row)


class PostgresRefactorStore(IRefactorStore):
    """IRefactorStore backed by PostgreSQL."""

    async def save_bulk(self, suggestions: List[RefactorSuggestion]) -> None:
        async with get_session() as session:
            for s in suggestions:
                session.add(
                    RefactorORM(
                        suggestion_id=s.suggestion_id,
                        repo_id=s.repo_id,
                        file_path=s.file_path,
                        start_line=s.start_line,
                        end_line=s.end_line,
                        title=s.title,
                        description=s.description,
                        pattern=s.pattern,
                        original_code=s.original_code,
                        suggested_code=s.suggested_code,
                        effort=s.effort,
                    )
                )

    async def get_by_repo(self, repo_id: str) -> List[RefactorSuggestion]:
        async with get_session() as session:
            stmt = select(RefactorORM).where(RefactorORM.repo_id == repo_id)
            result = await session.execute(stmt)
            return [
                RefactorSuggestion(
                    suggestion_id=r.suggestion_id,
                    repo_id=r.repo_id,
                    file_path=r.file_path,
                    start_line=r.start_line,
                    end_line=r.end_line,
                    title=r.title,
                    description=r.description,
                    pattern=r.pattern,
                    original_code=r.original_code,
                    suggested_code=r.suggested_code,
                    effort=r.effort,
                )
                for r in result.scalars()
            ]

    async def delete_by_repo(self, repo_id: str) -> None:
        async with get_session() as session:
            stmt = select(RefactorORM).where(RefactorORM.repo_id == repo_id)
            result = await session.execute(stmt)
            for row in result.scalars():
                await session.delete(row)

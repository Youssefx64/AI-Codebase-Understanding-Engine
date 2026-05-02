"""SQLAlchemy ORM table definitions."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database.postgres import Base


def _now() -> datetime:
    return datetime.utcnow()


class RepositoryORM(Base):
    """Persisted state for a Repository aggregate."""

    __tablename__ = "repositories"

    repo_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    github_url: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    owner: Mapped[str] = mapped_column(String(255), default="")
    name: Mapped[str] = mapped_column(String(255), default="")
    branch: Mapped[str] = mapped_column(String(128), default="main")
    status: Mapped[str] = mapped_column(String(32), default="pending")
    languages: Mapped[list] = mapped_column(JSON, default=list)
    file_count: Mapped[int] = mapped_column(Integer, default=0)
    total_lines: Mapped[int] = mapped_column(Integer, default=0)
    architecture_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    issues: Mapped[list["IssueORM"]] = relationship(
        "IssueORM", back_populates="repository", cascade="all, delete-orphan"
    )
    suggestions: Mapped[list["RefactorORM"]] = relationship(
        "RefactorORM", back_populates="repository", cascade="all, delete-orphan"
    )


class IssueORM(Base):
    """A single code issue linked to a repository."""

    __tablename__ = "code_issues"

    issue_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    repo_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.repo_id", ondelete="CASCADE"), index=True
    )
    file_path: Mapped[str] = mapped_column(String(1024))
    line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    issue_type: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(Text)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)

    repository: Mapped["RepositoryORM"] = relationship(
        "RepositoryORM", back_populates="issues"
    )


class RefactorORM(Base):
    """A single refactoring suggestion linked to a repository."""

    __tablename__ = "refactor_suggestions"

    suggestion_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    repo_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.repo_id", ondelete="CASCADE"), index=True
    )
    file_path: Mapped[str] = mapped_column(String(1024))
    start_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str] = mapped_column(Text)
    pattern: Mapped[str | None] = mapped_column(String(255), nullable=True)
    original_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    effort: Mapped[str] = mapped_column(String(32), default="medium")

    repository: Mapped["RepositoryORM"] = relationship(
        "RepositoryORM", back_populates="suggestions"
    )

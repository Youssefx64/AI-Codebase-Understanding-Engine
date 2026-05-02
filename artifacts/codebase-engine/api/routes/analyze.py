"""POST /analyze-repo — Submit a repository for analysis."""

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, status

from core.exceptions import AppError, RepositoryIngestionError
from core.logging import get_logger
from domain.models import AnalysisStatus, AnalyzeRepoRequest, AnalyzeRepoResponse
from infrastructure.database.repositories.repo_repository import PostgresRepositoryStore
from services.auth_service import AuthService
from services.pipeline_service import AnalysisPipeline
from services.repo_service import RepoIngestionService

router = APIRouter(prefix="/analyze-repo", tags=["Analysis"])
logger = get_logger(__name__)


async def _run_pipeline(repo_id: str) -> None:
    """Background task: full analysis pipeline."""
    pipeline = AnalysisPipeline()
    await pipeline.run(repo_id)


def _extract_user_id(authorization: Optional[str]) -> Optional[str]:
    """Try to decode a Bearer JWT; return user_id or None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = AuthService().decode_token(token)
        return payload.get("sub")
    except AppError:
        return None


@router.post(
    "",
    response_model=AnalyzeRepoResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a GitHub repository for analysis",
    description=(
        "Clones the repository and enqueues a full analysis pipeline "
        "(parsing, embedding, bug detection, refactoring suggestions). "
        "Returns immediately with the repo_id; poll /repo-summary/{id} for status."
    ),
)
async def analyze_repo(
    payload: AnalyzeRepoRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(default=None),
) -> AnalyzeRepoResponse:
    user_id = _extract_user_id(authorization)
    ingestion = RepoIngestionService()
    store = PostgresRepositoryStore()

    # Check for existing completed analysis
    if not payload.force_reanalysis:
        existing = await store.get_by_url(payload.github_url)
        if existing and existing.status == AnalysisStatus.COMPLETE:
            return AnalyzeRepoResponse(
                repo_id=existing.repo_id,
                status=existing.status,
                message="Repository was already analysed. Use force_reanalysis=true to re-run.",
            )
        if existing and existing.status in (
            AnalysisStatus.PARSING,
            AnalysisStatus.EMBEDDING,
            AnalysisStatus.ANALYZING,
            AnalysisStatus.CLONING,
        ):
            return AnalyzeRepoResponse(
                repo_id=existing.repo_id,
                status=existing.status,
                message="Analysis is already in progress.",
            )

    try:
        repo = await ingestion.ingest(payload.github_url, branch=payload.branch)
    except RepositoryIngestionError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc

    # Associate repo with the authenticated user if a valid token was provided
    if user_id:
        from infrastructure.database.orm_models import RepositoryORM
        from infrastructure.database.postgres import get_session as _gs
        async with _gs() as session:
            orm = await session.get(RepositoryORM, repo.repo_id)
            if orm:
                orm.user_id = user_id

    # Enqueue pipeline as a background task
    background_tasks.add_task(_run_pipeline, repo.repo_id)

    logger.info(
        "Analysis enqueued",
        repo_id=repo.repo_id,
        url=payload.github_url,
    )

    return AnalyzeRepoResponse(
        repo_id=repo.repo_id,
        status=repo.status,
        message="Analysis started. Use GET /repo-summary/{id} to track progress.",
    )

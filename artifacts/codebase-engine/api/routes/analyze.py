"""POST /analyze-repo — Submit a repository for analysis."""

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from core.exceptions import RepositoryIngestionError
from core.logging import get_logger
from domain.models import AnalysisStatus, AnalyzeRepoRequest, AnalyzeRepoResponse
from infrastructure.database.repositories.repo_repository import PostgresRepositoryStore
from services.pipeline_service import AnalysisPipeline
from services.repo_service import RepoIngestionService

router = APIRouter(prefix="/analyze-repo", tags=["Analysis"])
logger = get_logger(__name__)


async def _run_pipeline(repo_id: str) -> None:
    """Background task: full analysis pipeline."""
    pipeline = AnalysisPipeline()
    await pipeline.run(repo_id)


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
) -> AnalyzeRepoResponse:
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

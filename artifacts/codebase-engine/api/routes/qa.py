"""POST /ask — Developer Q&A over the codebase via RAG."""

from fastapi import APIRouter, HTTPException

from core.exceptions import LLMError, RepositoryNotFoundError, VectorStoreError
from core.logging import get_logger
from domain.models import AskQuestionRequest, AskResponse
from services.rag_service import RAGService

router = APIRouter(prefix="/ask", tags=["Q&A"])
logger = get_logger(__name__)


@router.post(
    "",
    response_model=AskResponse,
    summary="Ask a question about the codebase",
    description=(
        "Uses RAG (Retrieval-Augmented Generation) to answer natural language "
        "questions about the analysed repository. Retrieves the most relevant "
        "code chunks and passes them as context to the LLM."
    ),
)
async def ask_question(payload: AskQuestionRequest) -> AskResponse:
    rag = RAGService()
    try:
        return await rag.ask(
            repo_id=payload.repo_id,
            question=payload.question,
            max_chunks=payload.max_chunks,
        )
    except RepositoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
    except (LLMError, VectorStoreError) as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

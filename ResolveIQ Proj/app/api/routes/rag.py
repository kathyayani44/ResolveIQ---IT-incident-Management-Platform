from fastapi import APIRouter, status
from app.schemas.rag import RAGIncidentRequest, RAGResponse
from app.agents.rag.agent import run_rag_request_retrieval

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post(
    "/retrieve",
    response_model=RAGResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve context chunks for an incident query"
)
async def retrieve_rag_context(
    request: RAGIncidentRequest
) -> RAGResponse:
    """
    RAG retrieval endpoint:
    1. Builds search query from incident fields.
    2. Performs dense vector retrieval.
    3. Reranks candidates.
    4. Returns structured RAGResponse with context and citations.
    """
    return run_rag_request_retrieval(request, top_k=5)

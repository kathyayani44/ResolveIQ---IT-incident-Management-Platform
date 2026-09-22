"""
RAG Orchestration Agent for ResolveIQ.
Exposes retrieval functions for CanonicalIncident models and RAG requests.
"""
from typing import Optional, List, Any
from app.schemas.incident import CanonicalIncident
from app.schemas.agent_results import ClassificationResult, RetrievedChunk
from app.schemas.rag import RAGIncidentRequest, RAGResponse, RetrievalResult, incident_to_rag_request
from app.agents.rag.embedder import ResolveIQEmbedder
from app.agents.rag.vectorstore import ResolveIQQdrantStore
from app.agents.rag.retriever import ResolveIQRetriever
from app.agents.rag.reranker import ResolveIQReranker
from app.agents.rag.context_builder import build_context

# Module-level singletons
_embedder: Optional[ResolveIQEmbedder] = None
_store: Optional[ResolveIQQdrantStore] = None
_retriever: Optional[ResolveIQRetriever] = None
_reranker: Optional[ResolveIQReranker] = None


def get_rag_components():
    global _embedder, _store, _retriever, _reranker
    if _embedder is None:
        _embedder = ResolveIQEmbedder()
    if _store is None:
        _store = ResolveIQQdrantStore(db_path="data/qdrant_db")
    if _retriever is None:
        _retriever = ResolveIQRetriever(embedder=_embedder, store=_store)
    if _reranker is None:
        _reranker = ResolveIQReranker()
    return _retriever, _reranker


def build_search_query(request: RAGIncidentRequest) -> str:
    """Build natural language search query from incident request."""
    parts = [request.title]
    if request.category:
        parts.append(request.category)
    if request.service:
        parts.append(request.service)
    if request.severity:
        parts.append(request.severity)
    if request.keywords:
        parts.extend(request.keywords)
    return " ".join(parts).strip()


async def run_rag_retrieval(
    incident: CanonicalIncident,
    classification: Optional[ClassificationResult] = None,
    top_k: int = 5
) -> RetrievalResult:
    """
    Run full RAG retrieval pipeline for a CanonicalIncident and optional ClassificationResult:
    1. Convert incident and classification to RAGIncidentRequest and build search query.
    2. Dense vector search in Qdrant collections.
    3. Rerank candidates with CrossEncoder / heuristic reranker.
    4. Return standardized RetrievalResult contract containing top_k RetrievedChunks.
    """
    rag_request = incident_to_rag_request(incident, classification=classification)
    rag_response = run_rag_request_retrieval(rag_request, top_k=top_k)

    retrieved_chunks = rag_response.to_retrieved_chunks()
    return RetrievalResult(
        query=rag_response.query,
        retrieved_chunks=retrieved_chunks[:top_k]
    )


def run_rag_request_retrieval(
    request: RAGIncidentRequest,
    top_k: int = 5
) -> RAGResponse:
    """Run RAG retrieval pipeline for an RAGIncidentRequest."""
    retriever, reranker = get_rag_components()
    query = build_search_query(request)

    candidates = retriever.retrieve(query=query, top_k=top_k * 2)
    reranked = reranker.rerank(query=query, candidates=list(candidates), top_k=top_k)

    context_dict = build_context(query=query, reranked_chunks=reranked)
    return RAGResponse(**context_dict)

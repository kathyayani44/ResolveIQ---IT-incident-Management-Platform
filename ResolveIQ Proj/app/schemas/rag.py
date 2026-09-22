from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.incident import CanonicalIncident
from app.schemas.agent_results import RetrievedChunk


class RAGIncidentRequest(BaseModel):
    """Incident input for RAG retrieval."""

    title: str = Field(..., description="Incident title or summary")
    category: Optional[str] = Field(default=None, description="Incident category")
    service: Optional[str] = Field(default=None, description="Affected service name")
    severity: Optional[str] = Field(default=None, description="Incident severity level")
    keywords: Optional[List[str]] = Field(default=None, description="Relevant search keywords")

    model_config = {"extra": "ignore"}


class ContextItem(BaseModel):
    """Single retrieved context chunk."""

    chunk_id: str
    source: str
    title: str
    content: str
    score: float
    category: str

    model_config = {"extra": "ignore"}


class RAGResponse(BaseModel):
    """Structured RAG retrieval response."""

    query: str
    retrieved_context: List[ContextItem]
    citations: List[str]

    def to_retrieved_chunks(self) -> List[RetrievedChunk]:
        """Convert RAG context items to standard agent RetrievedChunk models."""
        return [
            RetrievedChunk(
                chunk_id=item.chunk_id,
                text=item.content,
                source=item.source,
                document_type=item.category,
                score=item.score
            )
            for item in self.retrieved_context
        ]

    model_config = {"extra": "ignore"}


class RetrievalResult(BaseModel):
    """Authoritative RetrievalResult contract for ResolveIQ RAG system."""

    query: str = Field(..., description="Query string used for retrieval")
    retrieved_chunks: List[RetrievedChunk] = Field(default_factory=list, description="Top retrieved knowledge chunks")

    model_config = {"extra": "ignore"}


def incident_to_rag_request(
    incident: CanonicalIncident,
    classification: Optional[Any] = None
) -> RAGIncidentRequest:
    """Convert CanonicalIncident and optional ClassificationResult to RAGIncidentRequest."""
    keywords = []
    if isinstance(incident.metadata, dict):
        keywords = incident.metadata.get("labels", [])

    category = getattr(classification, "category", None) if classification else None
    service = getattr(classification, "service", None) if classification else None

    return RAGIncidentRequest(
        title=incident.title,
        category=category,
        service=service,
        severity=incident.severity or incident.priority,
        keywords=keywords
    )


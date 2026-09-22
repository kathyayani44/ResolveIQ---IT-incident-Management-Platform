from typing import Literal, List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    """Result returned by Classification Agent."""

    category: str = Field(..., description="Identified incident category")
    service: Optional[str] = Field(default=None, description="Identified affected service")

    model_config = {"extra": "ignore"}


class RetrievedChunk(BaseModel):
    """Representation of retrieved evidence/knowledge chunk for RCA and Resolution."""

    chunk_id: str = Field(..., description="Unique identifier for the evidence/knowledge chunk")
    text: str = Field(..., description="Content of the retrieved chunk")
    source: Optional[str] = Field(default=None, description="Source document reference")
    document_type: Optional[str] = Field(default=None, description="Type of document, e.g. postmortem, runbook")
    score: Optional[float] = Field(default=None, description="Relevance retrieval score")

    model_config = {"extra": "ignore"}


class RCAEvidence(BaseModel):
    """Individual supporting evidence item for RCA."""

    chunk_id: str = Field(..., description="Chunk ID of supporting evidence")
    reason: str = Field(..., description="Justification explaining why this evidence supports root cause")

    model_config = {"extra": "ignore"}


class RCAResult(BaseModel):
    """Result returned by RCA Agent."""

    root_cause: Optional[str] = Field(default=None, description="Detailed root cause explanation if identified")
    status: Literal["identified", "insufficient_evidence"] = Field(..., description="RCA resolution status")
    evidence: List[RCAEvidence] = Field(default_factory=list, description="Supporting evidence items")

    model_config = {"extra": "ignore"}


class ResolutionResult(BaseModel):
    """Result returned by Resolution Agent."""

    recommendation: str = Field(..., description="High-level recovery recommendation summary")
    steps: List[str] = Field(default_factory=list, description="Sequential actionable recovery steps")
    risks: List[str] = Field(default_factory=list, description="Potential operational risks")
    evidence: List[str] = Field(default_factory=list, description="List of chunk IDs referenced during resolution")
    is_grounded: bool = Field(default=False, description="Whether resolution is grounded in verified retrieved evidence")
    grounding_type: Literal["rag_grounded", "insufficient_evidence", "llm_fallback"] = Field(
        default="insufficient_evidence",
        description="Classification of resolution grounding"
    )
    evidence_sources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Provenance metadata of chunks used for grounding"
    )

    model_config = {"extra": "ignore"}


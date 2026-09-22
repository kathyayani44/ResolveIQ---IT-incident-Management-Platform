from typing import TypedDict, Optional, Dict, Any
from app.schemas.incident import CanonicalIncident
from app.schemas.agent_results import ClassificationResult, RCAResult, ResolutionResult
from app.schemas.rag import RetrievalResult
from app.schemas.approval import HumanApprovalResult


class ResolveIQState(TypedDict, total=False):
    """
    Authoritative state object passed through the ResolveIQ LangGraph orchestration layer.
    Excludes revision fields as per current MVP specification.
    """

    incident: CanonicalIncident
    classification: Optional[ClassificationResult]
    retrieval: Optional[RetrievalResult]
    rca: Optional[RCAResult]
    resolution: Optional[ResolutionResult]
    approval: Optional[HumanApprovalResult]
    metadata: Optional[Dict[str, Any]]

from datetime import datetime, timezone
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.incident import CanonicalIncident
from app.schemas.agent_results import ClassificationResult, RCAResult, ResolutionResult, RetrievedChunk


class HumanApprovalInput(BaseModel):
    """Input payload submitted by human reviewer."""

    status: Literal["approved", "rejected"] = Field(..., description="Approval status decision")
    reviewer: Optional[str] = Field(default=None, description="Reviewer name or email")
    reason: Optional[str] = Field(default=None, description="Reason for decision")
    feedback: Optional[str] = Field(default=None, description="Additional feedback or notes")

    model_config = {"extra": "ignore"}


class HumanApprovalResult(BaseModel):
    """Authoritative result contract for Human Approval."""

    status: Literal["approved", "rejected"] = Field(..., description="Final approval decision")
    reviewer: Optional[str] = Field(default=None, description="Reviewer name or email")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of decision"
    )
    reason: Optional[str] = Field(default=None, description="Reason for decision")
    feedback: Optional[str] = Field(default=None, description="Additional feedback or notes")

    model_config = {"extra": "ignore"}


class ApprovalPackage(BaseModel):
    """Full review package exposed to human reviewers for inspection."""

    incident: CanonicalIncident = Field(..., description="Incident details")
    classification: ClassificationResult = Field(..., description="Classification result")
    rca: RCAResult = Field(..., description="Root cause analysis result")
    evidence: List[RetrievedChunk] = Field(default_factory=list, description="Retrieved evidence chunks")
    resolution: ResolutionResult = Field(..., description="Proposed resolution recommendation")
    risks: List[str] = Field(default_factory=list, description="Identified operational risks")

    model_config = {"extra": "ignore"}


class FinalWorkflowOutput(BaseModel):
    """Final output of the end-to-end ResolveIQ MVP workflow."""

    approval_package: ApprovalPackage
    approval_result: HumanApprovalResult
    jira_updated: bool = Field(default=False, description="Whether Jira was updated with the resolution")
    jira_writeback_response: Optional[Dict[str, Any]] = Field(default=None, description="Response from Jira API if updated")

    model_config = {"extra": "ignore"}

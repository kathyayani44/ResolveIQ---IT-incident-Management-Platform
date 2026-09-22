from datetime import datetime, timezone
from typing import Any, Dict, Optional, Literal
import uuid
from pydantic import BaseModel, Field

StageStatus = Literal[
    "NOT_STARTED",
    "PROCESSING",
    "COMPLETED",
    "FAILED",
    "BLOCKED",
    "INSUFFICIENT_EVIDENCE",
    "AWAITING_APPROVAL",
    "APPROVED",
    "REJECTED",
    "SKIPPED",
    "MUST_REVISE",
]


class CanonicalIncident(BaseModel):
    """Authoritative Internal Incident Schema for ResolveIQ."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique canonical incident ID")
    issue_key: str = Field(..., description="External issue identifier (e.g. 'INC-101')")
    source: str = Field(default="jira", description="Source system of the incident (e.g. 'jira')")
    title: str = Field(..., description="Summary or title of the incident")
    description: Optional[str] = Field(default=None, description="Detailed description of the incident")
    status: str = Field(default="open", description="Normalized incident status (e.g. 'open', 'in_progress', 'resolved')")
    jira_status: Optional[str] = Field(default=None, description="Exact current status reported by Jira (e.g. 'Waiting for support', 'Completed')")
    resolution: Optional[str] = Field(default=None, description="Exact resolution reported by Jira (e.g. 'Done', 'Fixed')")
    workflow_status: str = Field(default="unprocessed", description="Internal ResolveIQ AI processing state (e.g. 'unprocessed', 'awaiting_approval', 'approved', 'rejected')")
    priority: Optional[str] = Field(default=None, description="Priority level (e.g. 'Highest', 'High', 'Medium', 'Low')")
    severity: Optional[str] = Field(default=None, description="Severity level (e.g. 'SEV-1', 'SEV-2', 'SEV-3')")
    reporter: Optional[str] = Field(default=None, description="Reporter email or display name")
    assignee: Optional[str] = Field(default=None, description="Assignee email or display name")
    raw_event_id: Optional[str] = Field(default=None, description="Foreign reference to stored raw event record")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when incident was created")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when incident was last updated")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context and custom fields")

    model_config = {"populate_by_name": True, "extra": "allow"}

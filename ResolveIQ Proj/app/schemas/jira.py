from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class JiraUserSchema(BaseModel):
    account_id: Optional[str] = Field(default=None, alias="accountId")
    display_name: Optional[str] = Field(default=None, alias="displayName")
    email_address: Optional[str] = Field(default=None, alias="emailAddress")

    model_config = {"populate_by_name": True, "extra": "allow"}


class JiraIssueFieldsSchema(BaseModel):
    summary: Optional[str] = None
    description: Optional[Any] = None
    issue_type: Optional[Dict[str, Any]] = Field(default=None, alias="issuetype")
    priority: Optional[Dict[str, Any]] = None
    status: Optional[Dict[str, Any]] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    reporter: Optional[JiraUserSchema] = None
    assignee: Optional[JiraUserSchema] = None

    model_config = {"populate_by_name": True, "extra": "allow"}


class JiraIssueSchema(BaseModel):
    id: str
    key: str
    self_link: Optional[str] = Field(default=None, alias="self")
    fields: Optional[JiraIssueFieldsSchema] = None

    model_config = {"populate_by_name": True, "extra": "allow"}


class JiraWebhookEventSchema(BaseModel):
    timestamp: Optional[int] = None
    webhook_event: Optional[str] = Field(default=None, alias="webhookEvent")
    issue_event_type_name: Optional[str] = Field(default=None, alias="issue_event_type_name")
    issue: Optional[JiraIssueSchema] = None
    user: Optional[JiraUserSchema] = None
    changelog: Optional[Dict[str, Any]] = None

    model_config = {"populate_by_name": True, "extra": "allow"}


class JiraFetchIssueRequest(BaseModel):
    issue_key: str = Field(..., description="Jira issue key, e.g., 'INC-101'")


class IngestionReceiptSchema(BaseModel):
    event_id: str
    source: str = "jira"
    issue_key: Optional[str] = None
    received_at: datetime
    status: str = "stored"

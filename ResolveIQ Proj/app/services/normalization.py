from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.schemas.incident import CanonicalIncident


class NormalizationService:
    """Service for transforming raw Jira payloads into authoritative CanonicalIncident models."""

    @staticmethod
    def _extract_description_text(description_field: Any) -> Optional[str]:
        if isinstance(description_field, str):
            return description_field
        if isinstance(description_field, dict):
            # Parse Atlassian Document Format (ADF) simple text node extraction
            texts = []
            content_nodes = description_field.get("content", [])
            for node in content_nodes:
                if isinstance(node, dict):
                    for sub_node in node.get("content", []):
                        if isinstance(sub_node, dict) and "text" in sub_node:
                            texts.append(sub_node["text"])
            if texts:
                return "\n".join(texts)
        return None

    @staticmethod
    def _normalize_status(raw_status: Optional[str]) -> str:
        if not raw_status:
            return "open"
        status_lower = raw_status.lower().strip()
        if status_lower in ("open", "to do", "new", "created"):
            return "open"
        if status_lower in ("in progress", "in_progress", "investigating", "in review"):
            return "in_progress"
        if status_lower in ("done", "closed", "resolved", "complete", "completed"):
            return "resolved"
        return status_lower.replace(" ", "_")

    def normalize_jira_payload(
        self,
        raw_payload: Dict[str, Any],
        raw_event_id: Optional[str] = None
    ) -> CanonicalIncident:
        """Convert raw Jira payload into CanonicalIncident."""
        issue_dict = raw_payload.get("issue") if isinstance(raw_payload.get("issue"), dict) else raw_payload

        issue_key = (
            issue_dict.get("key")
            or raw_payload.get("issue_key")
            or raw_payload.get("key")
            or "UNKNOWN-KEY"
        )

        fields = issue_dict.get("fields", {}) if isinstance(issue_dict.get("fields"), dict) else {}

        # Summary / Title
        summary = fields.get("summary") or issue_dict.get("summary") or f"Jira Incident ({issue_key})"

        # Description
        raw_desc = fields.get("description") or issue_dict.get("description")
        description = self._extract_description_text(raw_desc)

        # Status
        status_obj = fields.get("status") or {}
        raw_status_name = status_obj.get("name") if isinstance(status_obj, dict) else (str(status_obj) if status_obj else None)
        jira_status = raw_status_name or "Open"
        status = self._normalize_status(raw_status_name)

        # Resolution
        resolution_obj = fields.get("resolution") or {}
        resolution = resolution_obj.get("name") if isinstance(resolution_obj, dict) else (str(resolution_obj) if resolution_obj else None)

        # Priority
        priority_obj = fields.get("priority") or {}
        priority = priority_obj.get("name") if isinstance(priority_obj, dict) else (str(priority_obj) if priority_obj else None)

        # Reporter
        reporter_obj = fields.get("reporter") or {}
        reporter = (
            reporter_obj.get("emailAddress")
            or reporter_obj.get("displayName")
            or (str(reporter_obj) if isinstance(reporter_obj, str) else None)
        )

        # Assignee
        assignee_obj = fields.get("assignee") or {}
        assignee = (
            assignee_obj.get("emailAddress")
            or assignee_obj.get("displayName")
            or (str(assignee_obj) if isinstance(assignee_obj, str) else None)
        )

        # Timestamps
        created_str = fields.get("created")
        created_at = datetime.now(timezone.utc)
        if created_str:
            try:
                created_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        updated_str = fields.get("updated")
        updated_at = datetime.now(timezone.utc)
        if updated_str:
            try:
                updated_at = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        now_iso = datetime.now(timezone.utc).isoformat()
        default_stages = {
            "jira_ingestion": {"status": "COMPLETED", "updated_at": now_iso, "message": "Issue ingested from Jira API"},
            "normalization": {"status": "COMPLETED", "updated_at": now_iso, "message": "Normalized to CanonicalIncident"},
            "classification": {"status": "NOT_STARTED"},
            "rag_retrieval": {"status": "NOT_STARTED"},
            "rca": {"status": "NOT_STARTED"},
            "resolution": {"status": "NOT_STARTED"},
            "awaiting_approval": {"status": "NOT_STARTED"},
            "jira_update": {"status": "NOT_STARTED"},
            "verification": {"status": "NOT_STARTED"},
            "completed": {"status": "NOT_STARTED"}
        }

        return CanonicalIncident(
            issue_key=issue_key,
            source="jira",
            title=summary,
            description=description,
            status=status,
            jira_status=jira_status,
            resolution=resolution,
            workflow_status="unprocessed",
            priority=priority,
            severity=fields.get("severity") or priority,
            reporter=reporter,
            assignee=assignee,
            raw_event_id=raw_event_id,
            created_at=created_at,
            updated_at=updated_at,
            metadata={
                "project": fields.get("project", {}).get("key") if isinstance(fields.get("project"), dict) else None,
                "issue_type": fields.get("issuetype", {}).get("name") if isinstance(fields.get("issuetype"), dict) else None,
                "labels": fields.get("labels", []),
                "stages": default_stages,
                "current_stage": "normalization",
                "stage_status": "completed"
            }
        )


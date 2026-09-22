from typing import Dict, Any, Optional
from app.integrations.jira.client import AbstractJiraClient, JiraClient
from app.services.raw_storage import AbstractRawStorage, raw_storage_instance
from app.services.incident_service import IncidentService
from app.schemas.jira import IngestionReceiptSchema
from app.schemas.incident import CanonicalIncident


class JiraIngestionService:
    """Service layer responsible for ingesting Jira webhooks, fetching Jira incident data, and processing the pipeline."""

    def __init__(
        self,
        storage: Optional[AbstractRawStorage] = None,
        jira_client: Optional[AbstractJiraClient] = None,
        incident_service: Optional[IncidentService] = None
    ):
        self.storage = storage or raw_storage_instance
        self.jira_client = jira_client or JiraClient()
        self.incident_service = incident_service or IncidentService(raw_storage=self.storage)

    async def ingest_webhook_event(self, raw_payload: Dict[str, Any]) -> IngestionReceiptSchema:
        """Ingest raw Jira webhook payload, normalize to CanonicalIncident, execute multi-agent pipeline, and return receipt."""
        canonical_incident: CanonicalIncident = await self.incident_service.process_raw_jira_event(
            raw_payload=raw_payload,
            source="jira_webhook"
        )
        try:
            canonical_incident = await self.incident_service.process_incident_pipeline(canonical_incident.issue_key)
        except Exception as e:
            import logging
            logging.getLogger("resolveiq.ingestion").warning(f"Pipeline execution on webhook failed: {e}")

        return IngestionReceiptSchema(
            event_id=canonical_incident.raw_event_id or canonical_incident.id,
            source="jira_webhook",
            issue_key=canonical_incident.issue_key,
            received_at=canonical_incident.created_at,
            status="normalized_and_stored"
        )

    async def fetch_and_ingest_issue(self, issue_key: str) -> IngestionReceiptSchema:
        """Fetch raw issue payload from Jira API, normalize to CanonicalIncident, execute multi-agent pipeline, and return receipt."""
        raw_payload = await self.jira_client.fetch_issue(issue_key)
        canonical_incident: CanonicalIncident = await self.incident_service.process_raw_jira_event(
            raw_payload=raw_payload,
            source="jira_api"
        )
        try:
            canonical_incident = await self.incident_service.process_incident_pipeline(canonical_incident.issue_key)
        except Exception as e:
            import logging
            logging.getLogger("resolveiq.ingestion").warning(f"Pipeline execution on fetch failed: {e}")

        return IngestionReceiptSchema(
            event_id=canonical_incident.raw_event_id or canonical_incident.id,
            source="jira_api",
            issue_key=canonical_incident.issue_key,
            received_at=canonical_incident.created_at,
            status="normalized_and_stored"
        )

    async def sync_all_jira_issues(self, jql: Optional[str] = None) -> Dict[str, Any]:
        """Fetch all accessible Jira issues via read-only GET requests, normalize, and synchronize into storage."""
        raw_issues = await self.jira_client.fetch_all_issues(jql=jql)
        synced_incidents: list[CanonicalIncident] = []

        for raw_issue in raw_issues:
            issue_key = raw_issue.get("key")
            raw_record = await self.storage.save_raw_event(
                raw_payload=raw_issue,
                source="jira_sync",
                issue_key=issue_key
            )
            raw_event_id = raw_record.get("event_id") or raw_record.get("id")

            normalized = self.incident_service.normalizer.normalize_jira_payload(
                raw_payload=raw_issue,
                raw_event_id=raw_event_id
            )

            # Check if incident already exists to preserve existing workflow metadata
            existing = await self.incident_service.get_incident_by_key(normalized.issue_key)
            if existing:
                # Merge existing AI analysis metadata while keeping Jira fields authoritative
                merged_metadata = dict(existing.metadata or {})
                merged_metadata.update(normalized.metadata or {})
                normalized.metadata = merged_metadata
                normalized.id = existing.id
                normalized.workflow_status = getattr(existing, "workflow_status", "unprocessed")

            saved = await self.incident_service.supabase_client.save_incident(normalized)
            synced_incidents.append(saved)

        return {
            "status": "success",
            "total_synced": len(synced_incidents),
            "issue_keys": [inc.issue_key for inc in synced_incidents]
        }

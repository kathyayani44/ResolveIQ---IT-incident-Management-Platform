from typing import Dict, Any, Optional
from app.schemas.incident import CanonicalIncident
from app.services.raw_storage import AbstractRawStorage, raw_storage_instance
from app.services.normalization import NormalizationService
from app.integrations.supabase.client import AbstractSupabaseClient, SupabaseClient


class IncidentService:
    """End-to-end incident management service: Raw storage -> Normalization -> CanonicalIncident storage."""

    def __init__(
        self,
        raw_storage: Optional[AbstractRawStorage] = None,
        supabase_client: Optional[AbstractSupabaseClient] = None,
        normalizer: Optional[NormalizationService] = None
    ):
        self.raw_storage = raw_storage or raw_storage_instance
        self.supabase_client = supabase_client or SupabaseClient()
        self.normalizer = normalizer or NormalizationService()

    async def process_raw_jira_event(
        self,
        raw_payload: Dict[str, Any],
        source: str = "jira_webhook"
    ) -> CanonicalIncident:
        """Pipeline flow: Raw Storage -> Normalization -> CanonicalIncident Storage."""
        # Step 1: Extract issue key if available
        issue_key = None
        if "issue" in raw_payload and isinstance(raw_payload["issue"], dict):
            issue_key = raw_payload["issue"].get("key")
        elif "key" in raw_payload:
            issue_key = raw_payload.get("key")

        # Step 2: Store raw event
        raw_record = await self.raw_storage.save_raw_event(
            raw_payload=raw_payload,
            source=source,
            issue_key=issue_key
        )
        raw_event_id = raw_record.get("event_id") or raw_record.get("id")

        # Step 3: Normalize to CanonicalIncident
        canonical_incident = self.normalizer.normalize_jira_payload(
            raw_payload=raw_payload,
            raw_event_id=raw_event_id
        )

        # Step 4: Store normalized CanonicalIncident record
        saved_incident = await self.supabase_client.save_incident(canonical_incident)
        return saved_incident

    async def get_incident_by_key(self, issue_key: str) -> Optional[CanonicalIncident]:
        """Fetch normalized CanonicalIncident by issue key."""
        return await self.supabase_client.get_incident(issue_key)

    async def list_incidents(self) -> list[CanonicalIncident]:
        """Fetch all normalized CanonicalIncident records."""
        return await self.supabase_client.list_incidents()

    async def process_incident_pipeline(self, issue_key: str) -> CanonicalIncident:
        """
        Executes Classification -> RAG -> RCA -> Resolution agents on an incident,
        tracks stages with upstream failure blocking, and persists into Supabase.
        """
        incident = await self.get_incident_by_key(issue_key)
        if not incident:
            raise ValueError(f"Incident with issue_key '{issue_key}' not found.")

        from app.services.pipeline import execute_incident_workflow
        updated_incident = await execute_incident_workflow(incident)
        return await self.supabase_client.save_incident(updated_incident)




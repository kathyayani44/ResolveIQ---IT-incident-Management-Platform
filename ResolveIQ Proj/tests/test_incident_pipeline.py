import unittest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.incident_service import IncidentService
from app.services.raw_storage import InMemoryRawStorage
from app.integrations.supabase.client import SupabaseClient
from app.schemas.incident import CanonicalIncident

client = TestClient(app)


class TestIncidentPipeline(unittest.IsolatedAsyncioTestCase):

    async def test_full_pipeline_ingest_and_retrieve(self):
        raw_storage = InMemoryRawStorage()
        supabase_client = SupabaseClient()
        service = IncidentService(raw_storage=raw_storage, supabase_client=supabase_client)

        webhook_payload = {
            "webhookEvent": "jira:issue_created",
            "issue": {
                "id": "20001",
                "key": "PIPE-88",
                "fields": {
                    "summary": "Database Connection Timeout",
                    "description": "Connection pool exhausted under heavy load.",
                    "status": {"name": "Closed"},
                    "priority": {"name": "High"}
                }
            }
        }

        # Run pipeline
        incident: CanonicalIncident = await service.process_raw_jira_event(
            raw_payload=webhook_payload,
            source="jira_webhook"
        )

        self.assertEqual(incident.issue_key, "PIPE-88")
        self.assertEqual(incident.status, "resolved")
        self.assertEqual(incident.title, "Database Connection Timeout")

        # Verify incident retrieval
        retrieved = await service.get_incident_by_key("PIPE-88")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.issue_key, "PIPE-88")
        self.assertEqual(retrieved.status, "resolved")


def test_api_incidents_get_route():
    webhook_payload = {
        "webhookEvent": "jira:issue_created",
        "issue": {
            "id": "30001",
            "key": "API-999",
            "fields": {
                "summary": "Cache Miss Spike",
                "status": {"name": "Open"}
            }
        }
    }

    # First ingest via webhook API
    res = client.post("/api/v1/jira/webhook", json=webhook_payload)
    assert res.status_code == 201

    # Fetch normalized CanonicalIncident from GET route
    res_get = client.get("/api/v1/incidents/API-999")
    assert res_get.status_code == 200
    data = res_get.json()
    assert data["issue_key"] == "API-999"
    assert data["title"] == "Cache Miss Spike"
    assert data["status"] == "open"

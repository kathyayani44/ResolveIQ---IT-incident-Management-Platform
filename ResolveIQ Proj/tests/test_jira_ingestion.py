import unittest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.raw_storage import InMemoryRawStorage
from app.services.jira_ingestion import JiraIngestionService
from app.integrations.jira.client import AbstractJiraClient, JiraClient
from app.api.routes.jira import get_jira_ingestion_service

client = TestClient(app)


class TestJiraIngestion(unittest.IsolatedAsyncioTestCase):

    async def test_in_memory_raw_storage(self):
        storage = InMemoryRawStorage()
        payload = {"issue": {"key": "INC-100", "fields": {"summary": "Database Connection Down"}}}

        record = await storage.save_raw_event(raw_payload=payload, source="test", issue_key="INC-100")
        self.assertIn("event_id", record)
        self.assertEqual(record["issue_key"], "INC-100")
        self.assertEqual(record["status"], "stored")

        retrieved = await storage.get_raw_event(record["event_id"])
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["raw_payload"], payload)

    async def test_jira_ingestion_service_webhook(self):
        storage = InMemoryRawStorage()
        service = JiraIngestionService(storage=storage)
        webhook_payload = {
            "webhookEvent": "jira:issue_created",
            "issue": {
                "id": "10001",
                "key": "INC-101",
                "fields": {"summary": "Payment Service 500 Errors"}
            }
        }

        receipt = await service.ingest_webhook_event(webhook_payload)
        self.assertEqual(receipt.source, "jira_webhook")
        self.assertEqual(receipt.issue_key, "INC-101")
        self.assertIn("stored", receipt.status)

        stored = await storage.get_raw_event(receipt.event_id)
        self.assertIsNotNone(stored)
        self.assertEqual(stored["raw_payload"]["issue"]["key"], "INC-101")

    async def test_jira_ingestion_service_fetch_issue(self):
        storage = InMemoryRawStorage()
        mock_jira_client = MagicMock(spec=AbstractJiraClient)
        mock_jira_client.fetch_issue = AsyncMock(return_value={
            "id": "10002",
            "key": "INC-202",
            "fields": {"summary": "API Gateway Latency Spike"}
        })

        service = JiraIngestionService(storage=storage, jira_client=mock_jira_client)
        receipt = await service.fetch_and_ingest_issue("INC-202")

        self.assertEqual(receipt.source, "jira_api")
        self.assertEqual(receipt.issue_key, "INC-202")
        mock_jira_client.fetch_issue.assert_called_once_with("INC-202")

    def test_jira_client_missing_credentials_raises(self):
        jira_client = JiraClient(domain="example.atlassian.net", email=None, api_token=None)
        with self.assertRaises(ValueError):
            import asyncio
            asyncio.run(jira_client.fetch_issue("INC-101"))


def test_api_jira_webhook_route():
    webhook_payload = {
        "webhookEvent": "jira:issue_created",
        "issue": {
            "id": "10005",
            "key": "INC-505",
            "fields": {"summary": "Test Incident Webhook"}
        }
    }

    response = client.post("/api/v1/jira/webhook", json=webhook_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["source"] == "jira_webhook"
    assert data["issue_key"] == "INC-505"
    assert "stored" in data["status"]


def test_api_jira_fetch_route():
    mock_service = MagicMock(spec=JiraIngestionService)
    mock_service.fetch_and_ingest_issue = AsyncMock(return_value={
        "event_id": "test-uuid-123",
        "source": "jira_api",
        "issue_key": "INC-777",
        "received_at": "2026-09-10T12:00:00Z",
        "status": "stored"
    })

    app.dependency_overrides[get_jira_ingestion_service] = lambda: mock_service

    try:
        response = client.post("/api/v1/jira/fetch/INC-777")
        assert response.status_code == 201
        data = response.json()
        assert data["issue_key"] == "INC-777"
        assert data["source"] == "jira_api"
    finally:
        app.dependency_overrides.clear()

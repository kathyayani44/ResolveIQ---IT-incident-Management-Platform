import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from fastapi.testclient import TestClient
from app.main import app
from app.integrations.jira.client import JiraClient
from app.services.jira_ingestion import JiraIngestionService
from app.services.incident_service import IncidentService
from app.services.raw_storage import InMemoryRawStorage
from app.schemas.incident import CanonicalIncident
from app.schemas.auth import UserLogin, UserRegister
from app.api.routes.jira import get_jira_ingestion_service

client = TestClient(app)


class TestJiraClientAndConnection(unittest.IsolatedAsyncioTestCase):
    """Tests for Jira client authentication, configuration, connection and error handling."""

    def test_jira_client_configuration_missing_credentials(self):
        """Verify Jira client correctly raises ValueError on missing credentials."""
        client_inst = JiraClient()
        client_inst.domain = ""
        with self.assertRaises(ValueError):
            client_inst._get_base_url()

    async def test_jira_client_connection_success(self):
        """Verify Jira client correctly verifies credentials and parses profile."""
        jira = JiraClient(domain="test.atlassian.net", email="user@example.com", api_token="dummy-token")
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "displayName": "Test Engineer",
            "emailAddress": "user@example.com",
            "accountId": "acc-12345",
            "active": True
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            res = await jira.verify_connection()
            self.assertTrue(res["connected"])
            self.assertEqual(res["displayName"], "Test Engineer")
            self.assertEqual(res["emailAddress"], "user@example.com")

    async def test_jira_client_connection_failure_401(self):
        """Verify Jira client handles 401 unauthorized gracefully."""
        jira = JiraClient(domain="test.atlassian.net", email="bad@example.com", api_token="bad-token")
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            res = await jira.verify_connection()
            self.assertFalse(res["connected"])
            self.assertIn("Jira authentication failed", res["error"])

    async def test_jira_client_connection_network_error(self):
        """Verify Jira client handles network connection errors gracefully."""
        jira = JiraClient(domain="test.atlassian.net", email="user@example.com", api_token="token")
        with patch("httpx.AsyncClient.get", side_effect=Exception("DNS resolution failed")):
            res = await jira.verify_connection()
            self.assertFalse(res["connected"])
            self.assertIn("Failed to connect to Jira API", res["error"])

    async def test_jira_client_pagination(self):
        """Verify Jira client correctly fetches multiple pages using token-based pagination."""
        jira = JiraClient(domain="test.atlassian.net", email="user@example.com", api_token="token")

        # Page 1 response
        page1_res = MagicMock(spec=httpx.Response)
        page1_res.status_code = 200
        page1_res.raise_for_status = MagicMock()
        page1_res.json.return_value = {
            "issues": [{"key": "ISSUE-1"}, {"key": "ISSUE-2"}],
            "isLast": False,
            "nextPageToken": "token-page-2"
        }

        # Page 2 response
        page2_res = MagicMock(spec=httpx.Response)
        page2_res.status_code = 200
        page2_res.raise_for_status = MagicMock()
        page2_res.json.return_value = {
            "issues": [{"key": "ISSUE-3"}],
            "isLast": True,
            "nextPageToken": None
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [page1_res, page2_res]
            issues = await jira.fetch_all_issues()
            self.assertEqual(len(issues), 3)
            self.assertEqual([i["key"] for i in issues], ["ISSUE-1", "ISSUE-2", "ISSUE-3"])
            self.assertEqual(mock_get.call_count, 2)


class TestJiraSyncAndStatusAuthoritativeness(unittest.IsolatedAsyncioTestCase):
    """Tests for Jira sync service, status preservation, and non-conflation with AI workflows."""

    async def test_jira_sync_preserves_authoritative_jira_status(self):
        """Verify Jira status is preserved verbatim from Jira fields and never mixed with workflow."""
        storage = InMemoryRawStorage()
        mock_jira = MagicMock(spec=JiraClient)
        mock_jira.fetch_all_issues = AsyncMock(return_value=[
            {
                "key": "OPS-101",
                "fields": {
                    "summary": "Kubernetes worker node disk pressure",
                    "status": {"name": "Waiting for support"},
                    "priority": {"name": "High"},
                    "description": "Disk utilization reached 92%",
                    "reporter": {"displayName": "Ops Bot"},
                    "assignee": {"displayName": "OnCall Engineer"}
                }
            },
            {
                "key": "OPS-102",
                "fields": {
                    "summary": "SSL Certificate renewed",
                    "status": {"name": "Completed"},
                    "priority": {"name": "Low"},
                    "description": "Cert renewal completed by cert-manager",
                    "resolution": {"name": "Done"}
                }
            }
        ])

        service = JiraIngestionService(storage=storage, jira_client=mock_jira)
        result = await service.sync_all_jira_issues()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["total_synced"], 2)
        self.assertIn("OPS-101", result["issue_keys"])
        self.assertIn("OPS-102", result["issue_keys"])

        # Check OPS-101 in incident storage
        inc1 = await service.incident_service.get_incident_by_key("OPS-101")
        self.assertIsNotNone(inc1)
        self.assertEqual(inc1.jira_status, "Waiting for support")
        self.assertEqual(inc1.workflow_status, "unprocessed")

        # Check OPS-102 in incident storage
        inc2 = await service.incident_service.get_incident_by_key("OPS-102")
        self.assertIsNotNone(inc2)
        self.assertEqual(inc2.jira_status, "Completed")
        self.assertEqual(inc2.resolution, "Done")

    async def test_resolveiq_workflow_completion_does_not_change_jira_status(self):
        """Verify that updating AI workflow or human approval never changes the Jira status."""
        storage = InMemoryRawStorage()
        incident_service = IncidentService(raw_storage=storage)

        # Create incident with Jira status 'Waiting for support'
        test_incident = CanonicalIncident(
            issue_key="PAY-505",
            source="jira",
            title="Payment webhook timeout",
            jira_status="Waiting for support",
            status="open",
            workflow_status="unprocessed",
            metadata={}
        )
        await incident_service.supabase_client.save_incident(test_incident)

        # Simulate workflow execution (e.g. classification, RCA, approval)
        saved = await incident_service.get_incident_by_key("PAY-505")
        self.assertEqual(saved.jira_status, "Waiting for support")

        # Mutate workflow metadata to approved
        saved.metadata["current_stage"] = "jira_update"
        saved.metadata["stage_status"] = "completed"
        saved.metadata["approval"] = {"status": "approved", "reviewer": "Lead SRE"}
        saved.workflow_status = "approved"
        updated = await incident_service.supabase_client.save_incident(saved)

        # Authoritative Jira status MUST remain 'Waiting for support'
        retrieved = await incident_service.get_incident_by_key("PAY-505")
        self.assertEqual(retrieved.jira_status, "Waiting for support")
        self.assertEqual(retrieved.workflow_status, "approved")
        self.assertEqual(retrieved.metadata["approval"]["status"], "approved")

    async def test_sync_with_empty_jira_results(self):
        """Verify sync handles empty Jira result gracefully."""
        storage = InMemoryRawStorage()
        mock_jira = MagicMock(spec=JiraClient)
        mock_jira.fetch_all_issues = AsyncMock(return_value=[])

        service = JiraIngestionService(storage=storage, jira_client=mock_jira)
        result = await service.sync_all_jira_issues()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["total_synced"], 0)
        self.assertEqual(result["issue_keys"], [])

    async def test_sync_no_hardcoded_issue_keys(self):
        """Verify dynamic issues with arbitrary issue keys are synchronized without hardcoding."""
        storage = InMemoryRawStorage()
        mock_jira = MagicMock(spec=JiraClient)
        mock_jira.fetch_all_issues = AsyncMock(return_value=[
            {
                "key": "DYNAMIC-88",
                "fields": {
                    "summary": "Dynamic Test Incident",
                    "status": {"name": "In Progress"}
                }
            }
        ])

        service = JiraIngestionService(storage=storage, jira_client=mock_jira)
        result = await service.sync_all_jira_issues()
        self.assertIn("DYNAMIC-88", result["issue_keys"])


class TestApiRoutesForJiraAndAuth(unittest.TestCase):
    """FastAPI route tests for standardized Jira connection and sync endpoints."""

    def test_get_jira_connection_endpoint(self):
        """Verify GET /api/v1/jira/connection returns connection status without exposing secrets."""
        mock_service = MagicMock()
        mock_service.jira_client = MagicMock()
        mock_service.jira_client.verify_connection = AsyncMock(return_value={
            "connected": True,
            "domain": "test.atlassian.net",
            "displayName": "Sravya Ullamgunta",
            "emailAddress": "usravya1@gmail.com"
        })

        app.dependency_overrides[get_jira_ingestion_service] = lambda: mock_service
        try:
            res = client.get("/api/v1/jira/connection")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["connected"])
            self.assertEqual(data["domain"], "test.atlassian.net")
            self.assertEqual(data["displayName"], "Sravya Ullamgunta")
            # Ensure no secret/token is exposed
            self.assertNotIn("api_token", data)
            self.assertNotIn("token", data)
            self.assertNotIn("password", data)
        finally:
            app.dependency_overrides.clear()

    def test_post_jira_sync_endpoint_success(self):
        """Verify POST /api/v1/jira/sync triggers synchronization and returns status."""
        mock_service = MagicMock(spec=JiraIngestionService)
        mock_service.sync_all_jira_issues = AsyncMock(return_value={
            "status": "success",
            "total_synced": 5,
            "issue_keys": ["KEY-1", "KEY-2", "KEY-3", "KEY-4", "KEY-5"]
        })

        app.dependency_overrides[get_jira_ingestion_service] = lambda: mock_service
        try:
            res = client.post("/api/v1/jira/sync")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["total_synced"], 5)
        finally:
            app.dependency_overrides.clear()

    def test_post_jira_sync_endpoint_failure_returns_502(self):
        """Verify POST /api/v1/jira/sync returns 502 Bad Gateway when Jira sync fails."""
        mock_service = MagicMock(spec=JiraIngestionService)
        mock_service.sync_all_jira_issues = AsyncMock(side_effect=Exception("Jira Cloud unreachable"))

        app.dependency_overrides[get_jira_ingestion_service] = lambda: mock_service
        try:
            res = client.post("/api/v1/jira/sync")
            self.assertEqual(res.status_code, 502)
            self.assertIn("Failed to synchronize Jira issues", res.json()["detail"])
        finally:
            app.dependency_overrides.clear()

    def test_auth_login_and_me_endpoints(self):
        """Verify ResolveIQ account login and /me endpoints."""
        # Login with seeded user
        login_res = client.post("/api/v1/auth/login", json={
            "email": "usravya1@gmail.com",
            "password": "password123"
        })
        self.assertEqual(login_res.status_code, 200)
        token = login_res.json()["token"]
        self.assertTrue(token.startswith("riq_"))

        # Verify /me with session token
        me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["email"], "usravya1@gmail.com")

import unittest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealth(unittest.TestCase):

    def test_root_endpoint(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("ResolveIQ Backend", response.json()["message"])

    def test_health_check_endpoint(self):
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["project"], "ResolveIQ Backend")
        self.assertEqual(data["version"], "0.1.0")

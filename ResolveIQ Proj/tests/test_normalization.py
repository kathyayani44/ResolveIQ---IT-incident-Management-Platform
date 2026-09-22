import unittest
from app.services.normalization import NormalizationService
from app.schemas.incident import CanonicalIncident


class TestNormalizationService(unittest.TestCase):

    def setUp(self):
        self.normalizer = NormalizationService()

    def test_normalize_jira_webhook_payload(self):
        raw_payload = {
            "webhookEvent": "jira:issue_created",
            "issue": {
                "id": "10010",
                "key": "PROJ-99",
                "fields": {
                    "summary": "Auth Service Memory Leak",
                    "description": "High memory consumption detected in auth pod.",
                    "status": {"name": "In Progress"},
                    "priority": {"name": "Highest"},
                    "reporter": {"displayName": "Alice Admin", "emailAddress": "alice@example.com"},
                    "assignee": {"displayName": "Bob Builder", "emailAddress": "bob@example.com"},
                    "created": "2026-09-10T12:00:00.000+0000"
                }
            }
        }

        incident: CanonicalIncident = self.normalizer.normalize_jira_payload(
            raw_payload=raw_payload,
            raw_event_id="evt-12345"
        )

        self.assertEqual(incident.issue_key, "PROJ-99")
        self.assertEqual(incident.source, "jira")
        self.assertEqual(incident.title, "Auth Service Memory Leak")
        self.assertEqual(incident.description, "High memory consumption detected in auth pod.")
        self.assertEqual(incident.status, "in_progress")
        self.assertEqual(incident.priority, "Highest")
        self.assertEqual(incident.reporter, "alice@example.com")
        self.assertEqual(incident.assignee, "bob@example.com")
        self.assertEqual(incident.raw_event_id, "evt-12345")

    def test_normalize_adf_description(self):
        raw_payload = {
            "key": "PROJ-100",
            "fields": {
                "summary": "ADF Test",
                "description": {
                    "version": 1,
                    "type": "doc",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Line 1 of incident description"}]
                        },
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Line 2 of incident description"}]
                        }
                    ]
                },
                "status": {"name": "To Do"}
            }
        }

        incident = self.normalizer.normalize_jira_payload(raw_payload=raw_payload)
        self.assertEqual(incident.status, "open")
        self.assertIn("Line 1 of incident description", incident.description)
        self.assertIn("Line 2 of incident description", incident.description)

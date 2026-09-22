import unittest
from unittest.mock import patch, AsyncMock
from app.schemas.incident import CanonicalIncident
from app.schemas.agent_results import RCAResult, RCAEvidence, ResolutionResult, RetrievedChunk
from app.agents.resolution.agent import run_resolution


class TestResolutionAgent(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.incident = CanonicalIncident(
            issue_key="RES-707",
            title="Redis Memory Out of Bounds",
            description="Redis cache node crashed due to maxmemory threshold reached.",
            severity="High"
        )
        self.rca = RCAResult(
            root_cause="Redis cache maxmemory policy set to noeviction under high write load.",
            status="identified",
            evidence=[RCAEvidence(chunk_id="runbook_redis_01", reason="Config dump shows noeviction policy.")]
        )
        self.knowledge = [
            RetrievedChunk(chunk_id="runbook_redis_01", text="Change maxmemory-policy to volatile-lru in redis.conf")
        ]

    @patch("app.core.llm_client._call_groq_http", new_callable=AsyncMock)
    async def test_successful_resolution_generation(self, mock_groq):
        mock_groq.return_value = '''{
            "recommendation": "Update Redis eviction policy and flush expired cache keys.",
            "steps": [
                "1. Update redis.conf maxmemory-policy to volatile-lru.",
                "2. Execute CONFIG REWRITE and restart Redis service."
            ],
            "risks": [
                "Transient cache miss latency spike during restart."
            ],
            "evidence": [
                "runbook_redis_01"
            ]
        }'''

        result = await run_resolution(self.incident, self.rca, self.knowledge)

        self.assertIsInstance(result, ResolutionResult)
        self.assertEqual(result.recommendation, "Update Redis eviction policy and flush expired cache keys.")
        self.assertEqual(len(result.steps), 2)
        self.assertEqual(len(result.risks), 1)
        self.assertEqual(result.evidence, ["runbook_redis_01"])
        mock_groq.assert_called_once()

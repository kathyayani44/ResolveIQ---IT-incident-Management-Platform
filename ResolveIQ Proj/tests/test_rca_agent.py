import unittest
from unittest.mock import patch, AsyncMock
from app.schemas.incident import CanonicalIncident
from app.schemas.agent_results import RCAResult, RetrievedChunk
from app.agents.rca.agent import run_rca


class TestRCAAgent(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.incident = CanonicalIncident(
            issue_key="DB-505",
            title="PostgreSQL Connection Pool Exhaustion",
            description="Database pool exhausted due to unclosed sessions.",
            severity="Critical"
        )
        self.chunks = [
            RetrievedChunk(chunk_id=f"chunk_{i}", text=f"Evidence text content {i}")
            for i in range(10)  # Pass 10 chunks to test 5 max limit rule
        ]

    @patch("app.core.llm_client._call_groq_http", new_callable=AsyncMock)
    async def test_rca_identified_evidence(self, mock_groq):
        mock_groq.return_value = '''{
            "root_cause": "Unclosed database sessions in analytics worker node.",
            "status": "identified",
            "evidence": [
                {"chunk_id": "chunk_0", "reason": "Log entries show unclosed session leakage."}
            ]
        }'''

        result = await run_rca(self.incident, self.chunks)

        self.assertIsInstance(result, RCAResult)
        self.assertEqual(result.status, "identified")
        self.assertEqual(result.root_cause, "Unclosed database sessions in analytics worker node.")
        self.assertEqual(len(result.evidence), 1)
        self.assertEqual(result.evidence[0].chunk_id, "chunk_0")

    @patch("app.core.llm_client._call_groq_http", new_callable=AsyncMock)
    async def test_rca_insufficient_evidence(self, mock_groq):
        mock_groq.return_value = '''{
            "root_cause": null,
            "status": "insufficient_evidence",
            "evidence": []
        }'''

        result = await run_rca(self.incident, self.chunks[:2])

        self.assertEqual(result.status, "insufficient_evidence")
        self.assertIsNone(result.root_cause)
        self.assertEqual(len(result.evidence), 0)

    @patch("app.core.llm_client.clean_json_string")
    @patch("app.core.llm_client._call_groq_http", new_callable=AsyncMock)
    async def test_max_five_chunks_limit(self, mock_groq, mock_clean_json):
        mock_groq.return_value = '{"root_cause": null, "status": "insufficient_evidence", "evidence": []}'
        mock_clean_json.side_effect = lambda x: x

        await run_rca(self.incident, self.chunks)  # 10 chunks passed

        # Inspect prompt passed to LLM
        called_user_prompt = mock_groq.call_args[0][1]
        self.assertIn("chunk_0", called_user_prompt)
        self.assertIn("chunk_4", called_user_prompt)
        self.assertNotIn("chunk_5", called_user_prompt)  # Ensures chunks 5-9 were trimmed out

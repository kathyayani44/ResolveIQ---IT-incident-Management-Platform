import unittest
from unittest.mock import patch, AsyncMock
from app.schemas.incident import CanonicalIncident
from app.schemas.agent_results import ClassificationResult
from app.agents.classification.agent import run_classification
from app.core.llm_client import LLMProviderError


class TestClassificationAgent(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.incident = CanonicalIncident(
            issue_key="NET-101",
            title="Corporate VPN Unreachable",
            description="Users unable to connect to primary VPN gateway in US East region.",
            severity="High",
            metadata={"comments": ["Restarted gateway service at 10:00 AM."]}
        )

    @patch("app.core.llm_client._call_groq_http", new_callable=AsyncMock)
    async def test_successful_classification_groq_primary(self, mock_groq):
        mock_groq.return_value = '{"category": "Network", "service": "VPN"}'

        result = await run_classification(self.incident)

        self.assertIsInstance(result, ClassificationResult)
        self.assertEqual(result.category, "Network")
        self.assertEqual(result.service, "VPN")
        mock_groq.assert_called_once()

    @patch("app.core.llm_client._call_gemini_http", new_callable=AsyncMock)
    @patch("app.core.llm_client._call_groq_http", new_callable=AsyncMock)
    async def test_gemini_fallback_on_groq_failure(self, mock_groq, mock_gemini):
        mock_groq.side_effect = Exception("Groq Rate Limit Exceeded (HTTP 429)")
        mock_gemini.return_value = '{"category": "Database", "service": "PostgreSQL"}'

        result = await run_classification(self.incident)

        self.assertEqual(result.category, "Database")
        self.assertEqual(result.service, "PostgreSQL")
        mock_groq.assert_called_once()
        mock_gemini.assert_called_once()

    @patch("app.core.llm_client._call_gemini_http", new_callable=AsyncMock)
    @patch("app.core.llm_client._call_groq_http", new_callable=AsyncMock)
    async def test_invalid_malformed_llm_output(self, mock_groq, mock_gemini):
        mock_groq.return_value = "Invalid Non-JSON response text"
        mock_gemini.return_value = "Also invalid JSON text"

        with self.assertRaises(LLMProviderError):
            await run_classification(self.incident)

    @patch("app.core.llm_client._call_gemini_http", new_callable=AsyncMock)
    @patch("app.core.llm_client._call_groq_http", new_callable=AsyncMock)
    async def test_secrets_are_not_exposed_in_error(self, mock_groq, mock_gemini):
        secret_key = "gsk_secret_key_12345"
        with patch("app.core.config.settings.GROQ_API_KEY", secret_key):
            mock_groq.side_effect = Exception(f"Failed with key {secret_key}")
            mock_gemini.side_effect = Exception("Gemini down")

            try:
                await run_classification(self.incident)
            except LLMProviderError as err:
                self.assertNotIn(secret_key, str(err))
                self.assertIn("gsk_***MASKED***", str(err))

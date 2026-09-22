import unittest
from unittest.mock import patch, AsyncMock
from app.schemas.incident import CanonicalIncident
from app.schemas.agent_results import ClassificationResult, RCAResult, ResolutionResult, RetrievedChunk
from app.schemas.rag import RetrievalResult
from app.services.pipeline import run_full_incident_pipeline, PipelineResult
from app.agents.rag.agent import run_rag_retrieval


class TestFullIncidentPipeline(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.incident = CanonicalIncident(
            issue_key="INC-9999",
            title="PostgreSQL Primary Memory Out of Bounds",
            description="Database instance crashed due to OOM killer terminating postgres process.",
            severity="Critical",
            metadata={"comments": ["Happened during scheduled ETL job batch run."]}
        )

    @patch("app.core.llm_client._call_groq_http", new_callable=AsyncMock)
    @patch("app.services.pipeline.run_rag_retrieval", new_callable=AsyncMock)
    async def test_end_to_end_pipeline(self, mock_rag_retrieval, mock_groq):
        # 1. Mock Classification response
        classification_json = '{"category": "Database", "service": "PostgreSQL"}'

        # 2. Mock RAG retrieval response
        mock_rag_retrieval.return_value = RetrievalResult(
            query="PostgreSQL Primary Memory Out of Bounds Database PostgreSQL Critical",
            retrieved_chunks=[
                RetrievedChunk(
                    chunk_id="postmortem_pg_oom_01",
                    text="Increase work_mem and shared_buffers or scale instance RAM when running heavy JOINs.",
                    source="postmortem_pg_oom.json",
                    document_type="postmortems",
                    score=0.96
                ),
                RetrievedChunk(
                    chunk_id="runbook_pg_restart_02",
                    text="Restart postgresql service via systemctl restart postgresql-14",
                    source="runbook_pg.json",
                    document_type="runbooks",
                    score=0.88
                )
            ]
        )

        # 3. Mock RCA response
        rca_json = '''{
            "root_cause": "PostgreSQL process killed by Linux OOM killer during ETL job due to excessive work_mem allocation.",
            "status": "identified",
            "evidence": [
                {"chunk_id": "postmortem_pg_oom_01", "reason": "Matches memory threshold exceeded pattern during heavy JOINs."}
            ]
        }'''

        # 4. Mock Resolution response
        resolution_json = '''{
            "recommendation": "Tune work_mem configuration and restart PostgreSQL instance.",
            "steps": [
                "1. Reduce work_mem in postgresql.conf to 64MB.",
                "2. Execute systemctl restart postgresql."
            ],
            "risks": [
                "Temporary query latency increase for large analytical queries."
            ],
            "evidence": [
                "postmortem_pg_oom_01",
                "runbook_pg_restart_02"
            ]
        }'''

        # Set sequential side-effect for Groq LLM calls (1: Classification, 2: RCA, 3: Resolution)
        mock_groq.side_effect = [classification_json, rca_json, resolution_json]

        # Execute full pipeline
        pipeline_result: PipelineResult = await run_full_incident_pipeline(self.incident)

        # Assert PipelineResult structure
        self.assertIsInstance(pipeline_result, PipelineResult)

        # Verify Classification stage
        self.assertEqual(pipeline_result.classification.category, "Database")
        self.assertEqual(pipeline_result.classification.service, "PostgreSQL")

        # Verify RAG stage
        self.assertEqual(len(pipeline_result.rag_result.retrieved_chunks), 2)
        self.assertEqual(pipeline_result.rag_result.retrieved_chunks[0].chunk_id, "postmortem_pg_oom_01")

        # Verify RCA stage
        self.assertEqual(pipeline_result.rca.status, "identified")
        self.assertIn("Linux OOM killer", pipeline_result.rca.root_cause)

        # Verify Resolution stage
        self.assertEqual(len(pipeline_result.resolution.steps), 2)
        self.assertEqual(pipeline_result.resolution.evidence, ["postmortem_pg_oom_01", "runbook_pg_restart_02"])

        # Verify Groq LLM was called 3 times (Classification -> RCA -> Resolution)
        self.assertEqual(mock_groq.call_count, 3)

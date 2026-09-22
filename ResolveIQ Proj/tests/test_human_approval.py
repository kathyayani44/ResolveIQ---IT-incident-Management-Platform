import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.incident import CanonicalIncident
from app.schemas.agent_results import ClassificationResult, RCAResult, RCAEvidence, ResolutionResult, RetrievedChunk
from app.schemas.approval import ApprovalPackage, HumanApprovalInput, HumanApprovalResult, FinalWorkflowOutput
from app.services.approval_service import ApprovalService
from app.services.pipeline import run_full_incident_pipeline, PipelineResult
from app.integrations.jira.client import AbstractJiraClient
import app.agents.resolution.agent as resolution_agent_module

client = TestClient(app)


class TestHumanApprovalAndWriteback(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.incident = CanonicalIncident(
            issue_key="JIRA-101",
            title="Redis Memory Out of Bounds",
            description="Redis process crashed on cache node 3.",
            severity="Critical",
            workflow_status="awaiting_approval",
            metadata={
                "stages": {
                    "jira_ingestion": {"status": "COMPLETED"},
                    "normalization": {"status": "COMPLETED"},
                    "classification": {"status": "COMPLETED"},
                    "rag_retrieval": {"status": "COMPLETED"},
                    "rca": {"status": "COMPLETED"},
                    "resolution": {"status": "COMPLETED"},
                    "awaiting_approval": {"status": "AWAITING_APPROVAL"},
                    "jira_update": {"status": "NOT_STARTED"},
                    "verification": {"status": "NOT_STARTED"},
                    "completed": {"status": "NOT_STARTED"},
                }
            }
        )
        self.classification = ClassificationResult(category="Database", service="Redis")
        self.rca = RCAResult(
            root_cause="Maxmemory threshold reached without eviction policy.",
            status="identified",
            evidence=[RCAEvidence(chunk_id="chunk_1", reason="Config shows maxmemory-policy noeviction.")]
        )
        self.evidence = [
            RetrievedChunk(chunk_id="chunk_1", text="Fix: set maxmemory-policy volatile-lru", source="redis_runbook.json", document_type="runbooks", score=0.95)
        ]
        self.resolution = ResolutionResult(
            recommendation="Change Redis maxmemory policy to volatile-lru.",
            steps=["1. Edit redis.conf.", "2. Restart redis-server."],
            risks=["Transient cache miss spike."],
            evidence=["chunk_1"],
            is_grounded=True,
            grounding_type="rag_grounded"
        )
        self.package = ApprovalPackage(
            incident=self.incident,
            classification=self.classification,
            rca=self.rca,
            evidence=self.evidence,
            resolution=self.resolution,
            risks=self.resolution.risks
        )

    async def test_1_approval_triggers_jira_update(self):
        mock_jira_client = MagicMock(spec=AbstractJiraClient)
        mock_jira_client.add_comment_to_issue = AsyncMock(return_value={"id": "comment-1000", "body": "Approved"})
        mock_jira_client.get_transitions = AsyncMock(return_value=[
            {"id": "761", "name": "Resolve this issue", "to": {"id": "5", "name": "Resolved", "statusCategory": {"key": "done"}}}
        ])
        mock_jira_client.transition_issue = AsyncMock(return_value={"status": "success"})
        mock_jira_client.fetch_issue = AsyncMock(return_value={"fields": {"status": {"name": "Resolved"}, "resolution": {"name": "Done"}}})

        service = ApprovalService(jira_client=mock_jira_client)
        user_input = HumanApprovalInput(
            status="approved",
            reviewer="Alice SRE Lead",
            reason="Verified recovery steps."
        )


        output: FinalWorkflowOutput = await service.process_approval(self.package, user_input)

        self.assertTrue(output.jira_updated)
        self.assertEqual(output.approval_result.status, "approved")
        self.assertEqual(output.approval_result.reviewer, "Alice SRE Lead")
        mock_jira_client.add_comment_to_issue.assert_called_once()
        called_args = mock_jira_client.add_comment_to_issue.call_args
        self.assertEqual(called_args[1]["issue_key"], "JIRA-101")
        self.assertIn("APPROVED by Alice SRE Lead", called_args[1]["comment"])

    async def test_2_rejection_does_not_trigger_jira_update(self):
        mock_jira_client = MagicMock(spec=AbstractJiraClient)
        mock_jira_client.add_comment_to_issue = AsyncMock()

        service = ApprovalService(jira_client=mock_jira_client)
        user_input = HumanApprovalInput(
            status="rejected",
            reviewer="Bob Lead",
            reason="Unacceptable risk of cache drop."
        )

        output: FinalWorkflowOutput = await service.process_approval(self.package, user_input)

        self.assertFalse(output.jira_updated)
        self.assertEqual(output.approval_result.status, "rejected")
        mock_jira_client.add_comment_to_issue.assert_not_called()

    async def test_3_jira_failure_handling(self):
        mock_jira_client = MagicMock(spec=AbstractJiraClient)
        mock_jira_client.add_comment_to_issue = AsyncMock(side_effect=Exception("HTTP 500 Internal Server Error"))

        service = ApprovalService(jira_client=mock_jira_client)
        user_input = HumanApprovalInput(status="approved", reviewer="Charlie Admin")

        # Approval processing should gracefully catch Jira failure without raising exception
        output: FinalWorkflowOutput = await service.process_approval(self.package, user_input)

        self.assertFalse(output.jira_updated)
        self.assertEqual(output.approval_result.status, "approved")
        self.assertIn("error", output.jira_writeback_response)
        self.assertIn("HTTP 500", output.jira_writeback_response["error"])

    def test_4_resolution_agent_never_calls_jira(self):
        # Verify Resolution Agent source code has zero references to JiraClient or Jira API calls
        import inspect
        source_code = inspect.getsource(resolution_agent_module)
        self.assertNotIn("jira", source_code.lower())
        self.assertNotIn("JiraClient", source_code)

    def test_5_approval_result_schema_compliance(self):
        result = HumanApprovalResult(
            status="approved",
            reviewer="Dave SRE",
            reason="Valid solution",
            feedback="LGTM"
        )

        data = result.model_dump()
        self.assertEqual(data["status"], "approved")
        self.assertEqual(data["reviewer"], "Dave SRE")
        self.assertEqual(data["reason"], "Valid solution")
        self.assertEqual(data["feedback"], "LGTM")
        self.assertIn("timestamp", data)

    @patch("app.core.llm_client._call_groq_http", new_callable=AsyncMock)
    @patch("app.services.pipeline.run_rag_retrieval", new_callable=AsyncMock)
    async def test_6_complete_mocked_end_to_end_mvp_workflow(self, mock_rag, mock_groq):
        mock_jira_client = MagicMock(spec=AbstractJiraClient)
        mock_jira_client.add_comment_to_issue = AsyncMock(return_value={"id": "comment-555"})
        mock_jira_client.get_transitions = AsyncMock(return_value=[
            {"id": "761", "name": "Resolve this issue", "to": {"id": "5", "name": "Resolved", "statusCategory": {"key": "done"}}}
        ])
        mock_jira_client.transition_issue = AsyncMock(return_value={"status": "success"})
        mock_jira_client.fetch_issue = AsyncMock(return_value={"fields": {"status": {"name": "Resolved"}, "resolution": {"name": "Done"}}})

        # Mock agent responses
        mock_groq.side_effect = [
            '{"category": "Database", "service": "Redis"}',  # Classification
            '{"root_cause": "OOM", "status": "identified", "evidence": [{"chunk_id": "c1", "reason": "r1"}]}',  # RCA
            '{"recommendation": "Restart node", "steps": ["1. Restart"], "risks": ["Latency"], "evidence": ["c1"]}'  # Resolution
        ]

        from app.schemas.rag import RetrievalResult
        mock_rag.return_value = RetrievalResult(
            query="Redis test",
            retrieved_chunks=[RetrievedChunk(chunk_id="c1", text="Restart snippet", source="runbook.json", document_type="runbooks", score=0.9)]
        )

        # 1. Pipeline Execution
        pipeline_result: PipelineResult = await run_full_incident_pipeline(self.incident)
        approval_pkg: ApprovalPackage = pipeline_result.to_approval_package()

        # 2. Human Approval Processing
        approval_service = ApprovalService(jira_client=mock_jira_client)
        final_output = await approval_service.process_approval(
            package=approval_pkg,
            user_input=HumanApprovalInput(status="approved", reviewer="Elena SRE", reason="Approved for writeback")
        )

        self.assertTrue(final_output.jira_updated)
        self.assertEqual(final_output.approval_result.status, "approved")
        mock_jira_client.add_comment_to_issue.assert_called_once()

    async def test_7_approval_rejected_if_stage_not_awaiting_approval(self):
        service = ApprovalService(jira_client=MagicMock(spec=AbstractJiraClient))
        # Set stage to NOT_STARTED
        self.package.incident.metadata["stages"]["awaiting_approval"]["status"] = "NOT_STARTED"
        user_input = HumanApprovalInput(status="approved", reviewer="Alice")
        with self.assertRaises(ValueError) as ctx:
            await service.process_approval(self.package, user_input)
        self.assertIn("not currently awaiting approval", str(ctx.exception))

    async def test_8_approval_rejected_if_not_grounded(self):
        service = ApprovalService(jira_client=MagicMock(spec=AbstractJiraClient))
        self.package.resolution.is_grounded = False
        user_input = HumanApprovalInput(status="approved", reviewer="Alice")
        with self.assertRaises(ValueError) as ctx:
            await service.process_approval(self.package, user_input)
        self.assertIn("Resolution is not grounded", str(ctx.exception))

    async def test_9_approval_rejected_if_grounding_type_not_rag_grounded(self):
        service = ApprovalService(jira_client=MagicMock(spec=AbstractJiraClient))
        self.package.resolution.grounding_type = "insufficient_evidence"
        user_input = HumanApprovalInput(status="approved", reviewer="Alice")
        with self.assertRaises(ValueError) as ctx:
            await service.process_approval(self.package, user_input)
        self.assertIn("Resolution is not grounded", str(ctx.exception))

    async def test_10_approval_rejected_if_chunk_id_invalid(self):
        service = ApprovalService(jira_client=MagicMock(spec=AbstractJiraClient))
        # Resolution references a chunk ID not in evidence
        self.package.resolution.evidence = ["non_existent_chunk_999"]
        user_input = HumanApprovalInput(status="approved", reviewer="Alice")
        with self.assertRaises(ValueError) as ctx:
            await service.process_approval(self.package, user_input)
        self.assertIn("Resolution evidence does not reference valid knowledge base chunk IDs", str(ctx.exception))


def test_api_approval_submit_endpoint_rejection():
    pkg = {
        "incident": {
            "issue_key": "API-100",
            "source": "jira",
            "title": "API Gateway 502 Bad Gateway",
            "status": "open"
        },
        "classification": {"category": "Network", "service": "API Gateway"},
        "rca": {"root_cause": "Upstream timeout", "status": "identified", "evidence": []},
        "evidence": [],
        "resolution": {"recommendation": "Increase timeout threshold.", "steps": ["Step 1"], "risks": [], "evidence": []},
        "risks": []
    }
    decision = {
        "status": "rejected",
        "reviewer": "Frank Ops",
        "reason": "Needs further investigation"
    }

    response = client.post(
        "/api/v1/approval/submit",
        json={"package": pkg, "decision": decision},
        headers={"Authorization": "Bearer riq_default"}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["approval_result"]["status"] == "rejected"
    assert data["jira_updated"] is False


def test_api_approval_submit_endpoint_ungrounded_rejection():
    """Verify that submitting an ungrounded approval via API returns HTTP 400."""
    pkg = {
        "incident": {
            "issue_key": "API-101",
            "source": "jira",
            "title": "API Gateway Timeout",
            "status": "open",
            "metadata": {
                "stages": {
                    "awaiting_approval": {"status": "AWAITING_APPROVAL"}
                }
            }
        },
        "classification": {"category": "Network", "service": "API Gateway"},
        "rca": {"root_cause": "Upstream timeout", "status": "identified", "evidence": []},
        "evidence": [],
        "resolution": {
            "recommendation": "Increase timeout threshold.",
            "steps": ["Step 1"],
            "risks": [],
            "evidence": [],
            "is_grounded": False,
            "grounding_type": "insufficient_evidence"
        },
        "risks": []
    }
    decision = {
        "status": "approved",
        "reviewer": "Frank Ops",
        "reason": "Force approve ungrounded"
    }

    response = client.post(
        "/api/v1/approval/submit",
        json={"package": pkg, "decision": decision},
        headers={"Authorization": "Bearer riq_default"}
    )
    assert response.status_code == 400
    assert "Resolution is not grounded" in response.json()["detail"]

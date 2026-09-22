import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.incident import CanonicalIncident
from app.schemas.agent_results import (
    ClassificationResult,
    RCAResult,
    RCAEvidence,
    ResolutionResult,
    RetrievedChunk,
)
from app.schemas.rag import RetrievalResult
from app.schemas.approval import ApprovalPackage, HumanApprovalInput, FinalWorkflowOutput
from app.services.pipeline import execute_incident_workflow
from app.services.approval_service import ApprovalService
from app.integrations.jira.client import AbstractJiraClient

client = TestClient(app)


def make_test_incident(issue_key="TEST-101", status="open", jira_status="Waiting for support"):
    return CanonicalIncident(
        issue_key=issue_key,
        title="Payment gateway connection timeout",
        description="Checkout service failing with timeouts to payment gateway.",
        status=status,
        jira_status=jira_status,
        workflow_status="unprocessed",
        metadata={
            "stages": {
                "jira_ingestion": {"status": "COMPLETED"},
                "normalization": {"status": "COMPLETED"},
                "classification": {"status": "NOT_STARTED"},
                "rag_retrieval": {"status": "NOT_STARTED"},
                "rca": {"status": "NOT_STARTED"},
                "resolution": {"status": "NOT_STARTED"},
                "awaiting_approval": {"status": "NOT_STARTED"},
                "jira_update": {"status": "NOT_STARTED"},
                "verification": {"status": "NOT_STARTED"},
                "completed": {"status": "NOT_STARTED"},
            }
        }
    )


def make_test_approval_package(incident=None):
    inc = incident or make_test_incident()
    classification = ClassificationResult(category="Payment", service="Gateway")
    rca = RCAResult(
        root_cause="Connection pool exhaustion",
        status="identified",
        evidence=[RCAEvidence(chunk_id="chk-1", reason="Pool at capacity")]
    )
    evidence = [
        RetrievedChunk(chunk_id="chk-1", text="Increase pool size", source="runbook.md", score=0.9)
    ]
    resolution = ResolutionResult(
        recommendation="Scale connection pool max_size from 50 to 200.",
        steps=["1. Edit config", "2. Deploy patch"],
        risks=["Higher memory usage"],
        evidence=["chk-1"],
        is_grounded=True,
        grounding_type="rag_grounded"
    )
    inc.metadata["classification"] = classification.model_dump(mode="json")
    inc.metadata["rca"] = rca.model_dump(mode="json")
    inc.metadata["resolution"] = resolution.model_dump(mode="json")
    inc.metadata["evidence"] = [c.model_dump(mode="json") for c in evidence]
    if "stages" in inc.metadata:
        inc.metadata["stages"]["classification"]["status"] = "COMPLETED"
        inc.metadata["stages"]["rag_retrieval"]["status"] = "COMPLETED"
        inc.metadata["stages"]["rca"]["status"] = "COMPLETED"
        inc.metadata["stages"]["resolution"]["status"] = "COMPLETED"
        inc.metadata["stages"]["awaiting_approval"]["status"] = "AWAITING_APPROVAL"
    inc.workflow_status = "awaiting_approval"
    inc.current_stage = "awaiting_approval"

    return ApprovalPackage(
        incident=inc,
        classification=classification,
        rca=rca,
        evidence=evidence,
        resolution=resolution,
        risks=resolution.risks
    )


# =====================================================================
# 1. Successful Classification stage
# =====================================================================
@pytest.mark.anyio
@patch("app.services.pipeline.run_classification", new_callable=AsyncMock)
@patch("app.services.pipeline.run_rag_retrieval", new_callable=AsyncMock)
@patch("app.services.pipeline.run_rca", new_callable=AsyncMock)
@patch("app.services.pipeline.run_resolution", new_callable=AsyncMock)
async def test_1_successful_classification_stage(mock_res, mock_rca, mock_rag, mock_cls):
    mock_cls.return_value = ClassificationResult(category="Database", service="PostgreSQL")
    mock_rag.return_value = RetrievalResult(query="test", retrieved_chunks=[])
    mock_rca.return_value = RCAResult(root_cause="Lock contention", status="identified")
    mock_res.return_value = ResolutionResult(recommendation="Kill locking pid", steps=[], risks=[])

    incident = make_test_incident()
    result = await execute_incident_workflow(incident)

    assert result.metadata["stages"]["classification"]["status"] == "COMPLETED"
    assert result.metadata["classification"]["category"] == "Database"
    assert result.metadata["classification"]["service"] == "PostgreSQL"


# =====================================================================
# 2. Classification failure
# =====================================================================
@pytest.mark.anyio
@patch("app.services.pipeline.run_classification", new_callable=AsyncMock)
async def test_2_classification_failure(mock_cls):
    mock_cls.side_effect = RuntimeError("Classification model API rate limit exceeded")

    incident = make_test_incident()
    result = await execute_incident_workflow(incident)

    assert result.metadata["stages"]["classification"]["status"] == "FAILED"
    assert "rate limit exceeded" in result.metadata["stages"]["classification"]["error"]
    assert result.workflow_status == "failed"
    assert result.current_stage == "classification"
    assert result.stage_status == "failed"


# =====================================================================
# 3. RAG success & failure
# =====================================================================
@pytest.mark.anyio
@patch("app.services.pipeline.run_classification", new_callable=AsyncMock)
@patch("app.services.pipeline.run_rag_retrieval", new_callable=AsyncMock)
async def test_3_rag_failure(mock_rag, mock_cls):
    mock_cls.return_value = ClassificationResult(category="Database", service="PostgreSQL")
    mock_rag.side_effect = ConnectionError("Knowledge base vector store unreachable")

    incident = make_test_incident()
    result = await execute_incident_workflow(incident)

    assert result.metadata["stages"]["classification"]["status"] == "COMPLETED"
    assert result.metadata["stages"]["rag_retrieval"]["status"] == "FAILED"
    assert "unreachable" in result.metadata["stages"]["rag_retrieval"]["error"]
    assert result.workflow_status == "failed"
    assert result.metadata["stages"]["rca"]["status"] == "BLOCKED"


# =====================================================================
# 4. RCA success & failure
# =====================================================================
@pytest.mark.anyio
@patch("app.services.pipeline.run_classification", new_callable=AsyncMock)
@patch("app.services.pipeline.run_rag_retrieval", new_callable=AsyncMock)
@patch("app.services.pipeline.run_rca", new_callable=AsyncMock)
async def test_4_rca_failure(mock_rca, mock_rag, mock_cls):
    mock_cls.return_value = ClassificationResult(category="Network", service="DNS")
    mock_rag.return_value = RetrievalResult(query="test", retrieved_chunks=[])
    mock_rca.side_effect = ValueError("Corrupted diagnostic payload")

    incident = make_test_incident()
    result = await execute_incident_workflow(incident)

    assert result.metadata["stages"]["rag_retrieval"]["status"] == "COMPLETED"
    assert result.metadata["stages"]["rca"]["status"] == "FAILED"
    assert result.metadata["stages"]["resolution"]["status"] == "BLOCKED"
    assert result.workflow_status == "failed"


# =====================================================================
# 5. Resolution success & failure
# =====================================================================
@pytest.mark.anyio
@patch("app.services.pipeline.run_classification", new_callable=AsyncMock)
@patch("app.services.pipeline.run_rag_retrieval", new_callable=AsyncMock)
@patch("app.services.pipeline.run_rca", new_callable=AsyncMock)
@patch("app.services.pipeline.run_resolution", new_callable=AsyncMock)
async def test_5_resolution_failure(mock_res, mock_rca, mock_rag, mock_cls):
    mock_cls.return_value = ClassificationResult(category="Compute", service="K8s")
    mock_rag.return_value = RetrievalResult(query="test", retrieved_chunks=[
        RetrievedChunk(chunk_id="chk-k8s", text="Node disk pressure runbook", score=0.9)
    ])
    mock_rca.return_value = RCAResult(root_cause="Node disk pressure", status="identified")
    mock_res.side_effect = TimeoutError("Resolution generator timed out")

    incident = make_test_incident()
    result = await execute_incident_workflow(incident)

    assert result.metadata["stages"]["rca"]["status"] == "COMPLETED"
    assert result.metadata["stages"]["resolution"]["status"] == "FAILED"
    assert result.metadata["stages"]["awaiting_approval"]["status"] == "BLOCKED"
    assert result.workflow_status == "failed"


# =====================================================================
# 6. Workflow blocking after an upstream failure
# =====================================================================
@pytest.mark.anyio
@patch("app.services.pipeline.run_classification", new_callable=AsyncMock)
async def test_6_workflow_blocking_downstream(mock_cls):
    mock_cls.side_effect = Exception("Upstream crash")

    incident = make_test_incident()
    result = await execute_incident_workflow(incident)

    # All downstream stages must be explicitly BLOCKED
    for downstream in ["rag_retrieval", "rca", "resolution", "awaiting_approval", "jira_update", "verification", "completed"]:
        assert result.metadata["stages"][downstream]["status"] == "BLOCKED", f"{downstream} should be BLOCKED"


# =====================================================================
# 7. Correct transition to "AWAITING_APPROVAL"
# =====================================================================
@pytest.mark.anyio
@patch("app.services.pipeline.run_classification", new_callable=AsyncMock)
@patch("app.services.pipeline.run_rag_retrieval", new_callable=AsyncMock)
@patch("app.services.pipeline.run_rca", new_callable=AsyncMock)
@patch("app.services.pipeline.run_resolution", new_callable=AsyncMock)
async def test_7_transition_to_awaiting_approval(mock_res, mock_rca, mock_rag, mock_cls):
    mock_cls.return_value = ClassificationResult(category="Auth", service="OAuth")
    mock_rag.return_value = RetrievalResult(query="test", retrieved_chunks=[
        RetrievedChunk(chunk_id="auth-1", text="OAuth token runbook", score=0.9)
    ])
    mock_rca.return_value = RCAResult(root_cause="Token expiry mismatch", status="identified")
    mock_res.return_value = ResolutionResult(
        recommendation="Refresh token",
        steps=["Step 1"],
        risks=[],
        evidence=["auth-1"],
        is_grounded=True,
        grounding_type="rag_grounded"
    )

    incident = make_test_incident()
    result = await execute_incident_workflow(incident)

    assert result.workflow_status == "awaiting_approval"
    assert result.current_stage == "awaiting_approval"
    assert result.stage_status == "awaiting_approval"
    assert result.metadata["stages"]["awaiting_approval"]["status"] == "AWAITING_APPROVAL"
    assert result.metadata["stages"]["jira_update"]["status"] == "NOT_STARTED"
    assert result.metadata["stages"]["completed"]["status"] == "NOT_STARTED"


# =====================================================================
# 8. Approval required before Jira writeback
# =====================================================================
@pytest.mark.anyio
async def test_8_approval_required_before_jira_writeback():
    mock_jira = MagicMock(spec=AbstractJiraClient)
    mock_jira.add_comment_to_issue = AsyncMock()
    mock_jira.transition_issue = AsyncMock()

    service = ApprovalService(jira_client=mock_jira)
    pkg = make_test_approval_package()

    # When decision is REJECTED
    decision = HumanApprovalInput(status="rejected", reviewer="Ops Lead", reason="Inadequate evidence")
    output = await service.process_approval(pkg, decision)

    # Zero Jira write calls must occur
    mock_jira.add_comment_to_issue.assert_not_called()
    mock_jira.transition_issue.assert_not_called()
    assert output.jira_updated is False
    assert output.approval_result.status == "rejected"
    # Stage completed must NOT be COMPLETED; incident remains open in must_revise
    assert pkg.incident.metadata["stages"]["completed"]["status"] in ("NOT_STARTED", "MUST_REVISE", "REJECTED")
    assert pkg.incident.current_stage == "must_revise"
    assert pkg.incident.workflow_status == "must_revise"
    assert pkg.incident.status == "open"


# =====================================================================
# 9. Jira comment/writeback
# =====================================================================
@pytest.mark.anyio
async def test_9_jira_comment_writeback():
    mock_jira = MagicMock(spec=AbstractJiraClient)
    mock_jira.add_comment_to_issue = AsyncMock(return_value={"id": "comment-999"})
    mock_jira.get_transitions = AsyncMock(return_value=[
        {"id": "761", "name": "Resolve this issue", "to": {"id": "5", "name": "Resolved", "statusCategory": {"key": "done"}}}
    ])
    mock_jira.transition_issue = AsyncMock(return_value={"status": "success"})
    mock_jira.fetch_issue = AsyncMock(return_value={
        "fields": {"status": {"name": "Resolved"}, "resolution": {"name": "Fixed"}}
    })

    service = ApprovalService(jira_client=mock_jira)
    pkg = make_test_approval_package()

    decision = HumanApprovalInput(status="approved", reviewer="DevOps Engineer", reason="Verified steps")
    output = await service.process_approval(pkg, decision)

    mock_jira.add_comment_to_issue.assert_called_once()
    call_args = mock_jira.add_comment_to_issue.call_args[1]
    assert call_args["issue_key"] == "TEST-101"
    assert "APPROVED by DevOps Engineer" in call_args["comment"]
    assert "Recommended Recovery Steps" in call_args["comment"]


# =====================================================================
# 10. Jira transition handling
# =====================================================================
@pytest.mark.anyio
async def test_10_jira_transition_selection():
    mock_jira = MagicMock(spec=AbstractJiraClient)
    mock_jira.add_comment_to_issue = AsyncMock(return_value={"id": "comment-1"})
    # Provide multiple transitions; should pick the Done/Resolved transition
    mock_jira.get_transitions = AsyncMock(return_value=[
        {"id": "891", "name": "In progress", "to": {"id": "3", "name": "In Progress", "statusCategory": {"key": "indeterminate"}}},
        {"id": "761", "name": "Resolve this issue", "to": {"id": "5", "name": "Resolved", "statusCategory": {"key": "done"}}},
        {"id": "851", "name": "Respond to customer", "to": {"id": "4", "name": "Waiting for customer", "statusCategory": {"key": "indeterminate"}}}
    ])
    mock_jira.transition_issue = AsyncMock(return_value={"status": "success"})
    mock_jira.fetch_issue = AsyncMock(return_value={
        "fields": {"status": {"name": "Resolved"}, "resolution": {"name": "Done"}}
    })

    service = ApprovalService(jira_client=mock_jira)
    pkg = make_test_approval_package()

    decision = HumanApprovalInput(status="approved", reviewer="Lead SRE")
    await service.process_approval(pkg, decision)

    # Should select transition id 761 ('Resolve this issue' -> 'Resolved')
    mock_jira.transition_issue.assert_called_once_with("TEST-101", "761")


# =====================================================================
# 11. Jira write failure
# =====================================================================
@pytest.mark.anyio
async def test_11_jira_write_failure_preserves_approval():
    mock_jira = MagicMock(spec=AbstractJiraClient)
    mock_jira.add_comment_to_issue = AsyncMock(side_effect=Exception("Jira Cloud 503 Service Unavailable"))

    service = ApprovalService(jira_client=mock_jira)
    pkg = make_test_approval_package()

    decision = HumanApprovalInput(status="approved", reviewer="Jane Engineer", reason="Looks solid")
    output = await service.process_approval(pkg, decision)

    assert output.jira_updated is False
    assert pkg.incident.workflow_status == "failed"
    assert pkg.incident.metadata["stages"]["jira_update"]["status"] == "FAILED"
    # User adjustment 1 & 16: approval remains APPROVED and resolution is preserved
    assert pkg.incident.metadata["stages"]["awaiting_approval"]["status"] == "APPROVED"
    assert pkg.incident.metadata["resolution"] is not None


# =====================================================================
# 12. Jira verification after writeback
# =====================================================================
@pytest.mark.anyio
async def test_12_jira_verification_after_writeback():
    mock_jira = MagicMock(spec=AbstractJiraClient)
    mock_jira.add_comment_to_issue = AsyncMock(return_value={"id": "comment-12"})
    mock_jira.get_transitions = AsyncMock(return_value=[
        {"id": "761", "name": "Resolve this issue", "to": {"id": "5", "name": "Resolved", "statusCategory": {"key": "done"}}}
    ])
    mock_jira.transition_issue = AsyncMock(return_value={"status": "success"})
    mock_jira.fetch_issue = AsyncMock(return_value={
        "fields": {"status": {"name": "Resolved"}, "resolution": {"name": "Done"}}
    })

    service = ApprovalService(jira_client=mock_jira)
    pkg = make_test_approval_package()

    decision = HumanApprovalInput(status="approved", reviewer="Auditor SRE")
    output = await service.process_approval(pkg, decision)

    # Re-fetch must have been called to verify
    mock_jira.fetch_issue.assert_called_once_with("TEST-101")
    assert pkg.incident.jira_status == "Resolved"
    assert pkg.incident.resolution == "Done"
    assert pkg.incident.metadata["stages"]["verification"]["status"] == "COMPLETED"
    assert pkg.incident.metadata["stages"]["completed"]["status"] == "COMPLETED"
    assert pkg.incident.workflow_status == "completed"


# =====================================================================
# 13. Verification mismatch does not produce "COMPLETED"
# =====================================================================
@pytest.mark.anyio
async def test_13_verification_mismatch_no_completion():
    mock_jira = MagicMock(spec=AbstractJiraClient)
    mock_jira.add_comment_to_issue = AsyncMock(return_value={"id": "comment-13"})
    mock_jira.get_transitions = AsyncMock(return_value=[
        {"id": "761", "name": "Resolve this issue", "to": {"id": "5", "name": "Resolved", "statusCategory": {"key": "done"}}}
    ])
    mock_jira.transition_issue = AsyncMock(return_value={"status": "success"})
    # Re-fetch returns unexpected status (e.g. still 'Open' due to Jira async lag or permission block)
    mock_jira.fetch_issue = AsyncMock(return_value={
        "fields": {"status": {"name": "Open"}, "resolution": None}
    })

    service = ApprovalService(jira_client=mock_jira)
    pkg = make_test_approval_package()

    decision = HumanApprovalInput(status="approved", reviewer="Operator")
    output = await service.process_approval(pkg, decision)

    # Verification must fail and workflow MUST NOT be completed
    assert pkg.incident.metadata["stages"]["verification"]["status"] == "FAILED"
    assert pkg.incident.metadata["stages"]["completed"]["status"] == "FAILED"
    assert pkg.incident.workflow_status != "completed"
    assert pkg.incident.workflow_status == "failed"


# =====================================================================
# 14. Successful end-to-end workflow
# =====================================================================
@pytest.mark.anyio
@patch("app.core.llm_client._call_groq_http", new_callable=AsyncMock)
@patch("app.services.pipeline.run_rag_retrieval", new_callable=AsyncMock)
async def test_14_successful_end_to_end_workflow(mock_rag, mock_groq):
    mock_groq.side_effect = [
        '{"category": "Network", "service": "Firewall"}',
        '{"root_cause": "Blocked port 443", "status": "identified", "evidence": [{"chunk_id": "c1", "reason": "Rule 12"}]}',
        '{"recommendation": "Open egress 443", "steps": ["Allow port"], "risks": [], "evidence": ["c1"]}'
    ]
    mock_rag.return_value = RetrievalResult(query="test", retrieved_chunks=[
        RetrievedChunk(chunk_id="c1", text="Firewall rule", source="rules.txt", score=0.95)
    ])

    incident = make_test_incident(issue_key="E2E-100")
    # Step A: Run AI Pipeline
    incident = await execute_incident_workflow(incident)
    assert incident.workflow_status == "awaiting_approval"

    # Step B: Human Approval
    mock_jira = MagicMock(spec=AbstractJiraClient)
    mock_jira.add_comment_to_issue = AsyncMock(return_value={"id": "comm-e2e"})
    mock_jira.get_transitions = AsyncMock(return_value=[
        {"id": "761", "name": "Resolve this issue", "to": {"id": "5", "name": "Resolved", "statusCategory": {"key": "done"}}}
    ])
    mock_jira.transition_issue = AsyncMock(return_value={"status": "success"})
    mock_jira.fetch_issue = AsyncMock(return_value={
        "fields": {"status": {"name": "Resolved"}, "resolution": {"name": "Fixed"}}
    })

    service = ApprovalService(jira_client=mock_jira)
    pkg = ApprovalPackage(
        incident=incident,
        classification=ClassificationResult(**incident.metadata["classification"]),
        rca=RCAResult(**incident.metadata["rca"]),
        evidence=[RetrievedChunk(**c) for c in incident.metadata["evidence"]],
        resolution=ResolutionResult(**incident.metadata["resolution"]),
        risks=[]
    )

    decision = HumanApprovalInput(status="approved", reviewer="Principal SRE")
    output = await service.process_approval(pkg, decision)

    assert output.jira_updated is True
    assert incident.workflow_status == "completed"
    assert incident.jira_status == "Resolved"
    assert incident.metadata["stages"]["completed"]["status"] == "COMPLETED"


# =====================================================================
# 15. Jira status remains separate from ResolveIQ workflow status
# =====================================================================
@pytest.mark.anyio
async def test_15_jira_status_separate_from_workflow_status():
    incident = make_test_incident(jira_status="Waiting for customer")
    incident.workflow_status = "awaiting_approval"

    # External Jira status is "Waiting for customer", ResolveIQ workflow status is "awaiting_approval"
    assert incident.jira_status == "Waiting for customer"
    assert incident.workflow_status == "awaiting_approval"
    assert incident.jira_status != incident.workflow_status


# =====================================================================
# 16. Approved resolution is preserved when Jira writeback fails
# =====================================================================
@pytest.mark.anyio
async def test_16_approved_resolution_preserved_on_writeback_failure():
    mock_jira = MagicMock(spec=AbstractJiraClient)
    mock_jira.add_comment_to_issue = AsyncMock(return_value={"id": "comment-ok"})
    # Transition fails
    mock_jira.get_transitions = AsyncMock(return_value=[])  # No transitions available

    service = ApprovalService(jira_client=mock_jira)
    pkg = make_test_approval_package()

    decision = HumanApprovalInput(status="approved", reviewer="Operator", reason="Approved")
    output = await service.process_approval(pkg, decision)

    # Writeback failed due to no transitions
    assert output.jira_updated is False
    assert pkg.incident.workflow_status == "failed"
    # Approved resolution and classification data MUST be preserved intact
    assert pkg.incident.metadata["stages"]["awaiting_approval"]["status"] == "APPROVED"
    assert pkg.incident.metadata["resolution"]["recommendation"] == "Scale connection pool max_size from 50 to 200."
    assert pkg.incident.metadata["classification"]["category"] == "Payment"
    # Comment was posted, so comment_posted flag is True (safe against duplicate on retry)
    assert pkg.incident.metadata["jira_update"]["comment_posted"] is True


# =====================================================================
# 17. Authentication Required on Approval & Retry Endpoints (Adjustment 8)
# =====================================================================
def test_17_unauthenticated_requests_rejected():
    # Calling approval submit without Authorization header must return 401
    res = client.post("/api/v1/approval/submit", json={
        "package": make_test_approval_package().model_dump(mode="json"),
        "decision": {"status": "approved", "reviewer": "Hacker"}
    })
    assert res.status_code == 401
    assert "Authentication required" in res.text

    # Calling retry-writeback without Authorization header must return 401
    res2 = client.post("/api/v1/incidents/TEST-101/retry-writeback")
    assert res2.status_code == 401
    assert "Authentication required" in res2.text


# =====================================================================
# 18. Zero RAG evidence blocks resolution LLM & blocks approval gate
# =====================================================================
@pytest.mark.anyio
@patch("app.services.pipeline.run_classification", new_callable=AsyncMock)
@patch("app.services.pipeline.run_rag_retrieval", new_callable=AsyncMock)
@patch("app.services.pipeline.run_rca", new_callable=AsyncMock)
@patch("app.services.pipeline.run_resolution", new_callable=AsyncMock)
async def test_18_zero_rag_evidence_blocks_resolution_and_approval(mock_res, mock_rca, mock_rag, mock_cls):
    mock_cls.return_value = ClassificationResult(category="VPN", service="Network")
    mock_rag.return_value = RetrievalResult(query="vpn drops", retrieved_chunks=[])
    mock_rca.return_value = RCAResult(root_cause=None, status="insufficient_evidence", evidence=[])

    incident = make_test_incident(issue_key="RESIQ-2")
    result = await execute_incident_workflow(incident)

    # Resolution LLM must NOT be called
    mock_res.assert_not_called()

    # Stages must reflect INSUFFICIENT_EVIDENCE and BLOCKED
    assert result.metadata["stages"]["rca"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert result.metadata["stages"]["resolution"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert result.metadata["stages"]["awaiting_approval"]["status"] == "BLOCKED"
    assert result.workflow_status == "insufficient_evidence"
    assert result.stage_status == "insufficient_evidence"

    # Resolution result metadata must be explicitly ungrounded
    res_meta = result.metadata["resolution"]
    assert res_meta["is_grounded"] is False
    assert res_meta["grounding_type"] == "insufficient_evidence"
    assert res_meta["evidence_sources"] == []

    # Backend approval attempt must be blocked
    service = ApprovalService(jira_client=MagicMock(spec=AbstractJiraClient))
    pkg = ApprovalPackage(
        incident=result,
        classification=mock_cls.return_value,
        rca=mock_rca.return_value,
        evidence=[],
        resolution=ResolutionResult(**res_meta),
        risks=[]
    )
    with pytest.raises(ValueError, match="Resolution is not grounded"):
        await service.process_approval(pkg, HumanApprovalInput(status="approved", reviewer="Operator"))


# =====================================================================
# 19. Valid RAG evidence enables grounded resolution & approval
# =====================================================================
@pytest.mark.anyio
@patch("app.services.pipeline.run_classification", new_callable=AsyncMock)
@patch("app.services.pipeline.run_rag_retrieval", new_callable=AsyncMock)
@patch("app.services.pipeline.run_rca", new_callable=AsyncMock)
@patch("app.services.pipeline.run_resolution", new_callable=AsyncMock)
async def test_19_valid_rag_evidence_enables_grounded_approval(mock_res, mock_rca, mock_rag, mock_cls):
    chunk = RetrievedChunk(
        chunk_id="rb-vpn-01",
        text="VPN gateway lease timeout set to 600s. Update to 3600s.",
        source="vpn_runbook.md",
        document_type="runbook",
        score=0.94
    )
    mock_cls.return_value = ClassificationResult(category="VPN", service="Gateway")
    mock_rag.return_value = RetrievalResult(query="vpn timeout", retrieved_chunks=[chunk])
    mock_rca.return_value = RCAResult(
        root_cause="Lease renewal timeout in gateway daemon",
        status="identified",
        evidence=[RCAEvidence(chunk_id="rb-vpn-01", reason="Matches lease interval")]
    )
    mock_res.return_value = ResolutionResult(
        recommendation="Update VPN gateway lease timeout in config to 3600s and reload service.",
        steps=["1. Edit gateway config", "2. Reload daemon"],
        risks=["Transient reconnection during reload"],
        evidence=["rb-vpn-01"],
        is_grounded=True,
        grounding_type="rag_grounded",
        evidence_sources=[{
            "chunk_id": "rb-vpn-01",
            "source": "vpn_runbook.md",
            "document_type": "runbook",
            "score": 0.94,
            "snippet": chunk.text[:100]
        }]
    )

    incident = make_test_incident(issue_key="RESIQ-G1")
    result = await execute_incident_workflow(incident)

    # Resolution LLM was called
    mock_res.assert_called_once()

    # Stages must reflect COMPLETED and AWAITING_APPROVAL
    assert result.metadata["stages"]["rca"]["status"] == "COMPLETED"
    assert result.metadata["stages"]["resolution"]["status"] == "COMPLETED"
    assert result.metadata["stages"]["awaiting_approval"]["status"] == "AWAITING_APPROVAL"
    assert result.workflow_status == "awaiting_approval"

    # Evidence provenance is preserved
    res_meta = result.metadata["resolution"]
    assert res_meta["is_grounded"] is True
    assert res_meta["grounding_type"] == "rag_grounded"
    assert len(res_meta["evidence_sources"]) == 1
    assert res_meta["evidence_sources"][0]["chunk_id"] == "rb-vpn-01"


# =====================================================================
# 20. Resolution referencing invalid/missing chunk IDs is not grounded
# =====================================================================
@pytest.mark.anyio
@patch("app.core.llm_client._call_groq_http", new_callable=AsyncMock)
async def test_20_resolution_agent_verifies_evidence_references(mock_groq):
    from app.agents.resolution.agent import run_resolution

    incident = make_test_incident()
    rca = RCAResult(root_cause="Known issue", status="identified")
    chunks = [RetrievedChunk(chunk_id="valid-1", text="Valid fix text", source="runbook.md", score=0.9)]

    # Case A: LLM returns hallucinated chunk ID not in retrieved chunks
    mock_groq.return_value = '''{
        "recommendation": "Do something ungrounded",
        "steps": ["Step 1"],
        "risks": [],
        "evidence": ["hallucinated-chunk-99"]
    }'''
    res_a = await run_resolution(incident, rca, chunks)
    assert res_a.is_grounded is False
    assert res_a.grounding_type == "insufficient_evidence"
    assert res_a.evidence_sources == []

    # Case B: LLM returns valid chunk ID that matches
    mock_groq.return_value = '''{
        "recommendation": "Do verified recovery",
        "steps": ["Step 1"],
        "risks": [],
        "evidence": ["valid-1"]
    }'''
    res_b = await run_resolution(incident, rca, chunks)
    assert res_b.is_grounded is True
    assert res_b.grounding_type == "rag_grounded"
    assert len(res_b.evidence_sources) == 1
    assert res_b.evidence_sources[0]["chunk_id"] == "valid-1"


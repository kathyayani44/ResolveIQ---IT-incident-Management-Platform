from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.schemas.incident import CanonicalIncident
from app.schemas.agent_results import ClassificationResult, RCAResult, ResolutionResult
from app.schemas.rag import RetrievalResult
from app.schemas.approval import ApprovalPackage
from app.agents.classification import run_classification
from app.agents.rag import run_rag_retrieval
from app.agents.rca import run_rca
from app.agents.resolution import run_resolution


class PipelineResult(BaseModel):
    """End-to-end incident resolution pipeline result."""

    incident: CanonicalIncident
    classification: ClassificationResult
    rag_result: RetrievalResult
    rca: RCAResult
    resolution: ResolutionResult

    def to_approval_package(self) -> ApprovalPackage:
        """Convert PipelineResult into an ApprovalPackage ready for human review."""
        return ApprovalPackage(
            incident=self.incident,
            classification=self.classification,
            rca=self.rca,
            evidence=self.rag_result.retrieved_chunks[:5],
            resolution=self.resolution,
            risks=self.resolution.risks
        )

    model_config = {"extra": "ignore"}


async def run_full_incident_pipeline(incident: CanonicalIncident) -> PipelineResult:
    """
    Executes the complete ResolveIQ incident resolution pipeline:
    CanonicalIncident
      ↓
    Classification
      ↓
    RAG retrieval
      ↓
    top 3–5 relevant chunks
      ↓
    RCA
      ↓
    Resolution
    """
    # 1. Classification Agent
    classification: ClassificationResult = await run_classification(incident)

    # 2. RAG Retrieval (top 5 chunks)
    rag_result: RetrievalResult = await run_rag_retrieval(
        incident=incident,
        classification=classification,
        top_k=5
    )

    # 3. Select top 3-5 chunks for downstream agents
    relevant_chunks = rag_result.retrieved_chunks[:5]

    # 4. RCA Agent
    rca_result: RCAResult = await run_rca(
        incident=incident,
        retrieved_chunks=relevant_chunks
    )

    # 5. Resolution Agent
    resolution_result: ResolutionResult = await run_resolution(
        incident=incident,
        rca=rca_result,
        relevant_knowledge=relevant_chunks
    )

    return PipelineResult(
        incident=incident,
        classification=classification,
        rag_result=rag_result,
        rca=rca_result,
        resolution=resolution_result
    )


async def execute_incident_workflow(incident: CanonicalIncident) -> CanonicalIncident:
    """
    Executes the multi-agent incident resolution stages sequentially:
    Classification -> RAG Retrieval -> RCA -> Resolution -> Awaiting Human Approval.
    
    If any upstream stage fails:
    - Failing stage is marked 'FAILED'.
    - All downstream stages are marked 'BLOCKED'.
    - Workflow status is set to 'failed'.
    - Structured error is stored.
    
    Only after all AI stages succeed does the workflow enter 'AWAITING_APPROVAL'.
    """
    from datetime import datetime, timezone
    now_iso = lambda: datetime.now(timezone.utc).isoformat()

    meta = dict(incident.metadata or {})
    stages = dict(meta.get("stages") or {})

    # Ensure all 10 standard stages are present
    stage_names = [
        "jira_ingestion",
        "normalization",
        "classification",
        "rag_retrieval",
        "rca",
        "resolution",
        "awaiting_approval",
        "jira_update",
        "verification",
        "completed"
    ]
    for s in stage_names:
        if s not in stages:
            stages[s] = {"status": "NOT_STARTED"}

    # Jira Ingestion & Normalization are already complete for synchronized incidents
    stages["jira_ingestion"] = stages.get("jira_ingestion") or {"status": "COMPLETED", "updated_at": now_iso()}
    if stages["jira_ingestion"].get("status") == "NOT_STARTED":
        stages["jira_ingestion"] = {"status": "COMPLETED", "updated_at": now_iso()}
    
    stages["normalization"] = stages.get("normalization") or {"status": "COMPLETED", "updated_at": now_iso()}
    if stages["normalization"].get("status") == "NOT_STARTED":
        stages["normalization"] = {"status": "COMPLETED", "updated_at": now_iso()}

    # Helper to block downstream stages
    def block_downstream(from_index: int, error_msg: str):
        for downstream in stage_names[from_index:]:
            stages[downstream] = {
                "status": "BLOCKED",
                "reason": f"Blocked due to upstream failure: {error_msg}",
                "updated_at": now_iso()
            }

    # 1. Classification Stage
    stages["classification"] = {"status": "PROCESSING", "updated_at": now_iso()}
    incident.current_stage = "classification"
    incident.stage_status = "processing"
    incident.workflow_status = "processing"
    try:
        classification = await run_classification(incident)
        stages["classification"] = {
            "status": "COMPLETED",
            "category": classification.category,
            "service": classification.service,
            "updated_at": now_iso()
        }
        meta["classification"] = classification.model_dump(mode="json")
    except Exception as exc:
        stages["classification"] = {
            "status": "FAILED",
            "error": str(exc),
            "updated_at": now_iso()
        }
        block_downstream(stage_names.index("rag_retrieval"), str(exc))
        incident.workflow_status = "failed"
        incident.current_stage = "classification"
        incident.stage_status = "failed"
        meta["stages"] = stages
        incident.metadata = meta
        return incident

    # 2. RAG Retrieval Stage
    stages["rag_retrieval"] = {"status": "PROCESSING", "updated_at": now_iso()}
    incident.current_stage = "rag_retrieval"
    incident.stage_status = "processing"
    try:
        rag_result = await run_rag_retrieval(
            incident=incident,
            classification=classification,
            top_k=5
        )
        relevant_chunks = rag_result.retrieved_chunks[:5]
        stages["rag_retrieval"] = {
            "status": "COMPLETED",
            "chunks_retrieved": len(relevant_chunks),
            "updated_at": now_iso()
        }
        meta["evidence"] = [c.model_dump(mode="json") for c in relevant_chunks]
    except Exception as exc:
        stages["rag_retrieval"] = {
            "status": "FAILED",
            "error": str(exc),
            "updated_at": now_iso()
        }
        block_downstream(stage_names.index("rca"), str(exc))
        incident.workflow_status = "failed"
        incident.current_stage = "rag_retrieval"
        incident.stage_status = "failed"
        meta["stages"] = stages
        incident.metadata = meta
        return incident

    # 3. RCA Stage
    stages["rca"] = {"status": "PROCESSING", "updated_at": now_iso()}
    incident.current_stage = "rca"
    incident.stage_status = "processing"
    try:
        rca_result = await run_rca(
            incident=incident,
            retrieved_chunks=relevant_chunks
        )
        if rca_result.status == "insufficient_evidence":
            stages["rca"] = {
                "status": "INSUFFICIENT_EVIDENCE",
                "root_cause": None,
                "reason": "Insufficient knowledge base evidence to identify root cause.",
                "updated_at": now_iso()
            }
        else:
            stages["rca"] = {
                "status": "COMPLETED",
                "root_cause": rca_result.root_cause,
                "updated_at": now_iso()
            }
        meta["rca"] = rca_result.model_dump(mode="json")
    except Exception as exc:
        stages["rca"] = {
            "status": "FAILED",
            "error": str(exc),
            "updated_at": now_iso()
        }
        block_downstream(stage_names.index("resolution"), str(exc))
        incident.workflow_status = "failed"
        incident.current_stage = "rca"
        incident.stage_status = "failed"
        meta["stages"] = stages
        incident.metadata = meta
        return incident

    # 4. Resolution Stage
    stages["resolution"] = {"status": "PROCESSING", "updated_at": now_iso()}
    incident.current_stage = "resolution"
    incident.stage_status = "processing"

    # Rule 4 & 7: If RAG returns zero evidence or RCA reports INSUFFICIENT_EVIDENCE,
    # do NOT invoke the Resolution LLM. Mark Resolution as INSUFFICIENT_EVIDENCE and block approval.
    if len(relevant_chunks) == 0 or rca_result.status == "insufficient_evidence":
        resolution_result = ResolutionResult(
            recommendation="Resolution blocked: No verified knowledge base runbook or postmortem evidence found for this incident.",
            steps=[],
            risks=["Ungrounded resolution: Action without verified runbook risks operational disruption."],
            evidence=[],
            is_grounded=False,
            grounding_type="insufficient_evidence",
            evidence_sources=[]
        )
        stages["resolution"] = {
            "status": "INSUFFICIENT_EVIDENCE",
            "reason": "Resolution blocked: No verified runbook evidence available to formulate grounded recovery steps.",
            "recommendation": resolution_result.recommendation,
            "steps": [],
            "risks": resolution_result.risks,
            "is_grounded": False,
            "updated_at": now_iso()
        }
        # Human approval gate is BLOCKED
        stages["awaiting_approval"] = {
            "status": "BLOCKED",
            "reason": "Approval blocked: Incident resolution lacks supporting runbook evidence.",
            "updated_at": now_iso()
        }
        stages["jira_update"] = {"status": "NOT_STARTED"}
        stages["verification"] = {"status": "NOT_STARTED"}
        stages["completed"] = {"status": "NOT_STARTED"}

        incident.workflow_status = "insufficient_evidence"
        incident.current_stage = "resolution"
        incident.stage_status = "insufficient_evidence"
        meta["resolution"] = resolution_result.model_dump(mode="json")
        meta["stages"] = stages
        incident.metadata = meta
        return incident

    try:
        resolution_result = await run_resolution(
            incident=incident,
            rca=rca_result,
            relevant_knowledge=relevant_chunks
        )

        if resolution_result.is_grounded:
            stages["resolution"] = {
                "status": "COMPLETED",
                "recommendation": resolution_result.recommendation,
                "steps": resolution_result.steps,
                "risks": resolution_result.risks,
                "is_grounded": True,
                "evidence_sources": resolution_result.evidence_sources,
                "updated_at": now_iso()
            }
            meta["resolution"] = resolution_result.model_dump(mode="json")

            # 5. Enter Human Approval Gate
            stages["awaiting_approval"] = {
                "status": "AWAITING_APPROVAL",
                "message": "AI analysis complete and ready for human review.",
                "updated_at": now_iso()
            }
            stages["jira_update"] = {"status": "NOT_STARTED"}
            stages["verification"] = {"status": "NOT_STARTED"}
            stages["completed"] = {"status": "NOT_STARTED"}

            incident.workflow_status = "awaiting_approval"
            incident.current_stage = "awaiting_approval"
            incident.stage_status = "awaiting_approval"
            meta["approval"] = meta.get("approval") or {"status": "pending"}
            meta["jira_update"] = meta.get("jira_update") or {"status": "pending"}
            meta["stages"] = stages
            incident.metadata = meta
            return incident
        else:
            # Resolution returned but was not grounded in retrieved evidence
            stages["resolution"] = {
                "status": "INSUFFICIENT_EVIDENCE",
                "reason": "Generated recovery recommendation did not reference valid retrieved runbook evidence.",
                "recommendation": resolution_result.recommendation,
                "steps": resolution_result.steps,
                "risks": resolution_result.risks,
                "is_grounded": False,
                "updated_at": now_iso()
            }
            stages["awaiting_approval"] = {
                "status": "BLOCKED",
                "reason": "Approval blocked: Generated resolution lacks verified grounding references.",
                "updated_at": now_iso()
            }
            stages["jira_update"] = {"status": "NOT_STARTED"}
            stages["verification"] = {"status": "NOT_STARTED"}
            stages["completed"] = {"status": "NOT_STARTED"}

            incident.workflow_status = "insufficient_evidence"
            incident.current_stage = "resolution"
            incident.stage_status = "insufficient_evidence"
            meta["resolution"] = resolution_result.model_dump(mode="json")
            meta["stages"] = stages
            incident.metadata = meta
            return incident

    except Exception as exc:
        stages["resolution"] = {
            "status": "FAILED",
            "error": str(exc),
            "updated_at": now_iso()
        }
        block_downstream(stage_names.index("awaiting_approval"), str(exc))
        incident.workflow_status = "failed"
        incident.current_stage = "resolution"
        incident.stage_status = "failed"
        meta["stages"] = stages
        incident.metadata = meta
        return incident


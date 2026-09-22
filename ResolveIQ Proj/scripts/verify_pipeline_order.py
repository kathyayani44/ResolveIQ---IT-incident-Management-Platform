import asyncio
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.schemas.incident import CanonicalIncident
from app.services.pipeline import run_full_incident_pipeline, execute_incident_workflow


async def test_pipeline_order():
    print("=" * 70)
    print("RESOLVEIQ: PIPELINE ORDER & INTEGRATION VERIFICATION")
    print("=" * 70)

    # 1. Setup sample incident RESIQ-2
    incident = CanonicalIncident(
        id="RESIQ-2",
        issue_key="RESIQ-2",
        title="vpn failed to start",
        description="VPN client reports routing error and failed to start connection on port 1194",
        category="Network",
        service="Network VPN",
        severity="Medium",
        status="open",
        current_stage="normalization",
        stage_status="completed",
        workflow_status="pending",
        metadata={
            "stages": {
                "jira_ingestion": {"status": "COMPLETED"},
                "normalization": {"status": "COMPLETED"},
            }
        }
    )

    print(f"\n[1] Starting Pipeline for Incident: {incident.id} - '{incident.title}'")
    print(f"    Category: {incident.category} | Service: {incident.service} | Severity: {incident.severity}")

    # 2. Execute full pipeline workflow
    print("\n[2] Executing workflow stages...")
    updated_incident = await execute_incident_workflow(incident)

    print("\n[3] Stage Status Results:")
    meta = updated_incident.metadata or {}
    stages = meta.get("stages", {})
    
    order = [
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

    for stage_name in order:
        stage_info = stages.get(stage_name, {})
        status = stage_info.get("status", "MISSING")
        details = ""
        if stage_name == "classification":
            details = f"(Category: {stage_info.get('category')}, Service: {stage_info.get('service')})"
        elif stage_name == "rag_retrieval":
            details = f"(Chunks retrieved: {stage_info.get('chunks_retrieved')})"
        elif stage_name == "rca":
            root_cause = str(stage_info.get('root_cause', ''))[:60]
            details = f"(Root Cause: {root_cause}...)"
        elif stage_name == "resolution":
            grounded = stage_info.get('is_grounded', False)
            steps_cnt = len(stage_info.get('steps', []))
            details = f"(Grounded: {grounded}, Steps: {steps_cnt})"
        elif stage_name == "awaiting_approval":
            details = f"({stage_info.get('message', stage_info.get('reason', ''))})"

        print(f"    - {stage_name:<20}: {status:<22} {details}")

    print(f"\n[4] Overall Incident State:")
    print(f"    Workflow Status : {updated_incident.workflow_status}")
    print(f"    Current Stage   : {updated_incident.current_stage}")
    print(f"    Stage Status    : {updated_incident.stage_status}")

    # Evidence details
    evidence = meta.get("evidence", [])
    print(f"\n[5] Retrieved Evidence Chunks ({len(evidence)}):")
    for i, chunk in enumerate(evidence, 1):
        print(f"    {i}. [{chunk.get('document_type')}] chunk_id={chunk.get('chunk_id')} (score: {chunk.get('score')})")
        print(f"       text snippet: {str(chunk.get('text', ''))[:80]}...")

    print(f"\n[5b] RCA Details: {meta.get('rca')}")
    print(f"[5c] Resolution Details: {meta.get('resolution')}")

    # Verify intended order assertions
    assert stages["classification"]["status"] == "COMPLETED", "Classification should be COMPLETED"
    assert stages["rag_retrieval"]["status"] == "COMPLETED", "RAG Retrieval should be COMPLETED"
    assert stages["rag_retrieval"]["chunks_retrieved"] > 0, "RAG Retrieval should return chunks"
    assert stages["rca"]["status"] in ("COMPLETED", "INSUFFICIENT_EVIDENCE"), "RCA should execute"
    assert stages["resolution"]["status"] in ("COMPLETED", "INSUFFICIENT_EVIDENCE"), "Resolution should execute"
    
    print("\n[6] Intended Order Verification: ALL CHECKS PASSED")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_pipeline_order())

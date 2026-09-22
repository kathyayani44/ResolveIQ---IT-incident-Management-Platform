import asyncio
import json
from app.services.incident_service import IncidentService
from app.services.approval_service import ApprovalService
from app.schemas.approval import HumanApprovalInput, ApprovalPackage
from app.schemas.agent_results import ClassificationResult, RCAResult, ResolutionResult, RetrievedChunk
from app.integrations.jira.client import JiraClient

async def main():
    print("=================================================================")
    print("STEP 1: Run ResolveIQ Pipeline on DEMO-6")
    print("=================================================================")
    incident_service = IncidentService()
    incident = await incident_service.process_incident_pipeline("DEMO-6")

    print(f"Incident Key: {incident.issue_key}")
    print(f"Workflow Status: {incident.workflow_status}")
    print(f"Current Stage: {incident.current_stage}")
    print(f"Stage Status: {incident.stage_status}")
    print(f"Classification: {incident.metadata.get('classification')}")
    print(f"RCA: {incident.metadata.get('rca', {}).get('root_cause')}")
    print(f"Resolution Recommendation: {incident.metadata.get('resolution', {}).get('recommendation')}")
    print(f"Stages awaiting_approval status: {incident.metadata.get('stages', {}).get('awaiting_approval', {}).get('status')}")

    assert incident.workflow_status == "awaiting_approval"
    assert incident.metadata.get('stages', {}).get('awaiting_approval', {}).get('status') == "AWAITING_APPROVAL"
    assert incident.metadata.get('stages', {}).get('jira_update', {}).get('status') == "NOT_STARTED"
    assert incident.metadata.get('stages', {}).get('completed', {}).get('status') == "NOT_STARTED"

    print("\n=================================================================")
    print("STEP 2: Deliberate Human Review & Approval")
    print("=================================================================")
    approval_service = ApprovalService()
    
    # Construct package from incident
    meta = incident.metadata or {}
    pkg = ApprovalPackage(
        incident=incident,
        classification=ClassificationResult(**meta["classification"]),
        rca=RCAResult(**meta["rca"]),
        evidence=[RetrievedChunk(**c) for c in meta.get("evidence", [])],
        resolution=ResolutionResult(**meta["resolution"]),
        risks=meta["resolution"].get("risks", [])
    )

    decision = HumanApprovalInput(
        status="approved",
        reviewer="Sravya Ullamgunta (Live Verification)",
        reason="Verified navigation light recovery steps against diagnostic runbook."
    )

    print("Submitting approval decision to ApprovalService...")
    output = await approval_service.process_approval(package=pkg, user_input=decision)

    print(f"Jira Updated: {output.jira_updated}")
    print(f"Approval Result: {output.approval_result.status} by {output.approval_result.reviewer}")
    print(f"Jira Response: {json.dumps(output.jira_writeback_response, indent=2)}")

    print("\n=================================================================")
    print("STEP 3: Verify Jira Source of Truth directly from Jira API")
    print("=================================================================")
    jira_client = JiraClient()
    fresh_issue = await jira_client.fetch_issue("DEMO-6")
    fields = fresh_issue.get("fields", {})
    live_status = fields.get("status", {}).get("name")
    live_resolution = fields.get("resolution", {}).get("name") if fields.get("resolution") else None
    comments = fields.get("comment", {}).get("comments", [])
    latest_comment = comments[-1]["body"]["content"][0]["content"][0]["text"] if comments else "No comment"

    print(f"Authoritative Live Jira Status: '{live_status}'")
    print(f"Authoritative Live Jira Resolution: '{live_resolution}'")
    print(f"Total Comments on DEMO-6: {len(comments)}")
    safe_comment = latest_comment[:100].encode('ascii', errors='replace').decode('ascii')
    print(f"Latest Comment snippet: {safe_comment}...")


    # Fetch stored incident to confirm ResolveIQ persisted the verified Jira state
    updated_incident = await incident_service.get_incident_by_key("DEMO-6")
    print(f"\nResolveIQ Incident Record:")
    print(f"  Jira Status: '{updated_incident.jira_status}' (matches live: {updated_incident.jira_status == live_status})")
    print(f"  Workflow Status: '{updated_incident.workflow_status}'")
    print(f"  Stage Completed: '{updated_incident.metadata.get('stages', {}).get('completed', {}).get('status')}'")
    print(f"  Verification Stage: '{updated_incident.metadata.get('stages', {}).get('verification', {}).get('status')}'")

    assert updated_incident.jira_status == live_status
    assert updated_incident.workflow_status == "completed"
    assert updated_incident.metadata.get('stages', {}).get('completed', {}).get('status') == "COMPLETED"
    print("\n[SUCCESS] LIVE VERIFICATION OF DEMO-6 PASSED WITH 100% SUCCESS!")

if __name__ == "__main__":
    asyncio.run(main())

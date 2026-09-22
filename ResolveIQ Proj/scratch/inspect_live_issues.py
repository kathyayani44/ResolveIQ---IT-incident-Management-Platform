import json
import asyncio
from app.integrations.jira.client import JiraClient
from app.services.incident_service import IncidentService
from app.services.approval_service import ApprovalService
from app.schemas.approval import HumanApprovalInput

async def inspect_issues():
    with open('data/incidents_cache.json', 'r') as f:
        data = json.load(f)
    print(f"Total cached incidents: {len(data)}")
    for inc in data:
        print(f"  {inc.get('issue_key')}: title='{inc.get('title')[:40]}', jira_status='{inc.get('jira_status')}', workflow_status='{inc.get('workflow_status')}'")


    # Let's inspect DEMO-6 transitions
    client = JiraClient()
    issue = await client.fetch_issue("DEMO-6")
    fields = issue.get("fields", {})
    print(f"\nLive DEMO-6 status: {fields.get('status', {}).get('name')}")
    print(f"Live DEMO-6 summary: {fields.get('summary')}")
    transitions = await client.get_transitions("DEMO-6")
    print("Available transitions for DEMO-6:")
    for t in transitions:
        print(f"  ID: {t.get('id')} - Name: '{t.get('name')}' -> To: '{t.get('to', {}).get('name')}' (Category: {t.get('to', {}).get('statusCategory', {}).get('key')})")

if __name__ == "__main__":
    asyncio.run(inspect_issues())

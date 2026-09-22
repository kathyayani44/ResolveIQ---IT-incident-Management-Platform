Prompt 2 — ResolveIQ AI Workflow, Human Approval & Jira Writeback

Continue from the current ResolveIQ implementation after Prompt 1. Prompt 1 has already established real Jira issue synchronization, exact Jira status as the source of truth, ResolveIQ authentication, removal of mock incidents, and read-only Jira integration.

Now implement the end-to-end incident resolution workflow and controlled Jira writeback.

1. Core Workflow

For each synchronized Jira incident, implement and track these stages independently:

Jira Ingestion → Normalization → Classification → RAG Retrieval → RCA → Resolution → Awaiting Human Approval → Jira Update → Verification → Completed

Each stage must have an explicit state such as:

- "NOT_STARTED"
- "PROCESSING"
- "COMPLETED"
- "FAILED"
- "BLOCKED" / "AWAITING_APPROVAL"

Do not mark the overall workflow as completed simply because an agent function executed. Each stage must have a meaningful structured result.

2. Agent Execution

Use the existing ResolveIQ agent architecture and LangGraph orchestration.

For each incident:

1. Classification agent determines the incident category.
2. RAG/retrieval agent retrieves relevant knowledge/evidence.
3. RCA agent determines the likely root cause.
4. Resolution agent generates a proposed resolution.
5. Store the structured outputs and evidence for the incident.
6. Only after all required AI stages successfully complete should the incident enter "AWAITING_APPROVAL".

If an upstream stage fails, downstream stages must not be falsely marked as completed.

Preserve the existing agent implementations where possible and integrate them safely rather than unnecessarily rewriting them.

3. Human Approval Gate

Add a clear human approval step to the incident UI.

The user should be able to review:

- Incident details
- Jira status
- Classification
- Retrieved evidence
- Root cause analysis
- Proposed resolution
- Confidence/relevant supporting information

Provide an explicit action such as:

Approve Resolution

Approval must be a deliberate human action.

Important:

Human approval does NOT mean the Jira issue is already resolved.

After approval, the incident should move to:

"JIRA_UPDATE"

and only then should Jira write operations be attempted.

4. Jira Writeback

After human approval, implement controlled Jira writeback using the existing backend Jira client.

The writeback should support the appropriate Jira actions required by the existing ResolveIQ workflow, such as:

1. Add the approved resolution/comment to the Jira issue.
2. Transition the Jira issue to the intended final status where appropriate.
3. Do not assume transition IDs or status names. Inspect the available transitions for the specific issue and select the appropriate existing transition.
4. Do not create new Jira workflows, statuses, projects, or configuration.

All Jira write operations must happen only after explicit human approval.

Keep Jira credentials strictly backend-side.

5. Verify the Actual Jira Result

Do not assume a successful HTTP response means the Jira issue is actually in the desired final state.

After writeback:

1. Re-fetch the Jira issue using the existing read API.
2. Verify the actual Jira status.
3. Verify the resolution/comment as applicable.
4. Persist the verified Jira result.
5. Update the ResolveIQ workflow state only after successful verification.

The final state should therefore represent:

AI resolution generated → human approved → Jira updated → Jira re-fetched → actual Jira state verified

If Jira writeback succeeds but verification fails, do not mark the workflow as completed.

6. Failure & Retry Handling

Handle failures explicitly.

Examples:

- AI agent failure → stage "FAILED"
- Human has not approved → "AWAITING_APPROVAL"
- Jira update failure → "FAILED"
- Jira transition unavailable → "FAILED"
- Jira verification mismatch → "FAILED"

When writeback fails, preserve the approved resolution and incident state so the operation can be retried without rerunning the entire AI pipeline unnecessarily.

Do not silently report success.

7. Frontend

Update the incident details UI to clearly distinguish:

Jira State

- Current Jira status
- Jira resolution
- Jira update/verification state

ResolveIQ Workflow

- Current processing stage
- Stage status
- Classification
- RAG evidence
- RCA
- Proposed resolution
- Human approval state

The UI must never display an AI workflow state as the Jira status.

For example:

Jira Status: Waiting for support

ResolveIQ Workflow:
Resolution Generated
Awaiting Human Approval

[ Review Resolution ] [ Approve Resolution ]

After approval:

Jira Status: In Progress

ResolveIQ Workflow:
Jira Update → Verifying Jira → Completed

The Jira status shown after writeback must come from the actual re-fetched Jira issue.

8. Backend/API

Add or update the necessary APIs for:

- Starting/resuming the AI workflow for an incident
- Retrieving workflow/stage status
- Retrieving AI results
- Approving a proposed resolution
- Performing the approved Jira writeback
- Returning the verified Jira result

Keep the API structure consistent with the existing application.

Do not expose Jira credentials or tokens through API responses.

9. Persistence

Persist enough workflow information to survive backend restarts, including:

- Current stage
- Stage status
- Classification
- RAG evidence
- RCA
- Proposed resolution
- Approval state
- Approval timestamp/user where appropriate
- Jira update state
- Verified Jira status
- Verified Jira resolution

Do not create a conflicting source of truth for Jira status. Whenever a Jira sync/re-fetch occurs, the actual Jira response remains authoritative.

10. Tests

Add automated tests covering at minimum:

1. Successful Classification stage
2. Classification failure
3. RAG success/failure
4. RCA success/failure
5. Resolution success/failure
6. Workflow blocking after an upstream failure
7. Correct transition to "AWAITING_APPROVAL"
8. Approval required before Jira writeback
9. Jira comment/writeback
10. Jira transition handling
11. Jira write failure
12. Jira verification after writeback
13. Verification mismatch does not produce "COMPLETED"
14. Successful end-to-end workflow
15. Jira status remains separate from ResolveIQ workflow status
16. Approved resolution is preserved when Jira writeback fails

Use mocks/stubs for automated Jira write tests. Do not use the live Jira account for destructive test scenarios.

11. Live Verification

After automated tests pass, perform a controlled live verification using an existing Jira issue.

Do not create a new Jira issue just for testing.

Use one appropriate existing test issue and:

1. Run the ResolveIQ pipeline.
2. Review the generated classification/RAG/RCA/resolution.
3. Require explicit human approval.
4. Perform the minimum necessary Jira writeback.
5. Re-fetch the issue.
6. Confirm the actual Jira status/resolution matches the intended result.
7. Confirm ResolveIQ displays the verified Jira state.

Do not modify unrelated Jira issues.

12. Important Scope

Prompt 1's read-only synchronization is already implemented. Prompt 2 is now responsible for:

AI processing → human review → approval → controlled Jira writeback → Jira verification

Do not redesign the existing Jira synchronization or authentication unnecessarily.

Do not add Jira OAuth yet. The MVP should continue using the existing backend-configured Jira credentials. Per-user Jira OAuth can be implemented later.

13. Implementation Safety

Before changing anything, inspect the existing project and understand the current implementation from Prompt 1.

Make changes incrementally and preserve the existing working functionality.

Do not delete, reset, clean, overwrite, move, or replace existing project/system files unless I explicitly authorize the exact target.

Do not perform destructive Jira operations. Do not create/delete projects, workflows, permissions, or unrelated Jira data.

If an operation requires a destructive change that is not explicitly part of this prompt, stop and report it instead of performing it.

After implementation, run the existing test suite as well as the new tests and verify that the existing Prompt 1 functionality still works.
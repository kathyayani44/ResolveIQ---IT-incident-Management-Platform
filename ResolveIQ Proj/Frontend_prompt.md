You are building the ResolveIQ frontend from scratch.

IMPORTANT:
This is NOT a redesign of the existing frontend.

Completely IGNORE the existing frontend/ folder and its contents.
Do not use its components, pages, styling, layouts, routes, or design as the basis for the new UI.

Create a NEW frontend implementation from scratch based ONLY on the specification below.

============================================================
1. CRITICAL SAFETY RULE
============================================================

NON-DESTRUCTIVE WORK ONLY.

- Do NOT delete any files or folders.
- Do NOT move any files or folders.
- Do NOT rename existing files or folders.
- Do NOT overwrite existing backend files.
- Do NOT modify the backend.
- Do NOT delete or modify the existing frontend folder.
- Do NOT run destructive filesystem commands.
- Do NOT run git reset, git clean, recursive delete commands, or equivalent commands.
- Do NOT replace the project with a downloaded template.
- Do NOT modify unrelated project files.

The existing frontend folder must remain completely untouched.

Create the new frontend in its own clearly identified frontend location.

Before creating anything:
1. Inspect the project root.
2. Inspect the backend API structure only to understand API contracts.
3. Confirm where the new frontend will be created.
4. Then build the frontend.

If there is any ambiguity, do NOT delete or overwrite anything.
Create a new file/path instead.

============================================================
2. PRODUCT
============================================================

Product name:

ResolveIQ

ResolveIQ is an AI-powered multi-agent IT incident troubleshooting and resolution system.

The frontend is designed for:

IT support engineers / incident operators.

The primary user question should always be:

"What needs my attention right now?"

The frontend is NOT a chatbot.

It is an incident operations and decision-making interface.

============================================================
3. CORE WORKFLOW
============================================================

The MVP workflow is:

Jira Incident
      ↓
Incident Retrieval
      ↓
Normalization
      ↓
Classification
      ↓
RAG / Knowledge Retrieval
      ↓
Root Cause Analysis
      ↓
Resolution Recommendation
      ↓
Human Approval
      ↓
Approved
      ↓
Jira Update
      ↓
END

If rejected:

Human Approval
      ↓
Rejected
      ↓
END

IMPORTANT:

Jira Update IS part of the MVP.

Do NOT represent Jira Update as a future feature.

Revision Agent is NOT part of the current MVP.

Do NOT show Revision anywhere in the main workflow.

Also do NOT show:
- Revision Agent
- SOP Generation
- KB Generation
- Audit page
- detailed execution logs
- agent logs
- chatbot interface

============================================================
4. FRONTEND ARCHITECTURE
============================================================

Use React.

The frontend communicates ONLY with FastAPI.

Architecture:

React Frontend
      ↓
FastAPI Backend
      ↓
Backend Services
      ↓
Supabase/PostgreSQL
      ↓
LangGraph / Agents
      ↓
Jira / Qdrant

React must NEVER directly connect to:

- Supabase
- PostgreSQL
- Qdrant
- Jira
- LangGraph
- individual AI agents

All backend communication must go through FastAPI.

============================================================
5. BACKEND API INTEGRATION — USE THE ACTUAL BACKEND
============================================================

IMPORTANT:

The coding agent has access to the existing ResolveIQ backend.

DO NOT create mock API endpoints or assume that the endpoint
list below exactly matches the current backend implementation.

Before building the frontend API layer:

1. Inspect the existing FastAPI backend.
2. Inspect the actual route definitions.
3. Inspect the request/response schemas used by those routes.
4. Identify the real endpoint paths, HTTP methods, request bodies,
   response structures, status fields, and error responses.
5. Use the EXISTING BACKEND API as the source of truth.

The frontend must be built against the REAL implemented FastAPI
endpoints.

Do NOT invent, duplicate, or mock backend endpoints.

Do NOT modify the backend just to make the frontend easier to build.

If the backend endpoint differs from the suggested endpoint below,
USE THE ACTUAL BACKEND ENDPOINT and adapt the frontend accordingly.

------------------------------------------------------------
EXPECTED MVP API CAPABILITIES
------------------------------------------------------------

The frontend needs backend functionality for:

GET incidents
→ Load incidents for Dashboard and Incidents page.

GET one incident by issue key
→ Load complete information for Incident Details.

POST/process an incident
→ Start/process the ResolveIQ workflow.

POST/approve an incident
→ Submit human approval.
→ Backend should continue to Jira Update.

POST/reject an incident
→ Submit human rejection and feedback.
→ Workflow ends for the current MVP.

The expected paths may be:

GET  /api/incidents
GET  /api/incidents/{issue_key}
POST /api/incidents/{issue_key}/process
POST /api/incidents/{issue_key}/approve
POST /api/incidents/{issue_key}/reject

BUT THESE ARE NOT TO BE ASSUMED.

Inspect the backend and use whatever paths and schemas are
actually implemented.

------------------------------------------------------------
API SERVICE LAYER
------------------------------------------------------------

Put ALL frontend API communication inside:

src/services/api.js

Components and pages must NOT contain scattered fetch/axios calls.

The API layer should provide clean functions such as:

getIncidents()
getIncident(issueKey)
processIncident(issueKey)
approveIncident(issueKey, data)
rejectIncident(issueKey, data)

Adapt the exact function parameters and response handling to
the actual backend contracts.

------------------------------------------------------------
NO FAKE DATA WHEN REAL API EXISTS
------------------------------------------------------------

Do NOT fabricate incident data if the real backend endpoint
already exists.

Connect the UI directly to the real FastAPI backend.

If the backend currently returns zero incidents:

→ show the designed empty states.

If an endpoint is not yet implemented:

→ do NOT invent a fake backend implementation.
→ do NOT modify the backend.
→ clearly report the missing endpoint/contract at the end.

Only use temporary mock data if absolutely necessary for a
specific UI that cannot yet be connected, and isolate it clearly
so it can be removed easily.

------------------------------------------------------------
BACKEND SAFETY
------------------------------------------------------------

The backend is READ/INSPECT ONLY during this frontend task.

Do NOT:
- modify backend files
- create new backend routes
- change backend schemas
- change database code
- change Jira integration
- change agents
- change LangGraph
- change Supabase/Qdrant implementation

The goal is to make the NEW frontend consume the EXISTING
ResolveIQ backend correctly.

============================================================
6. DATA THE FRONTEND SHOULD REPRESENT
============================================================

The UI should be designed around these concepts:

Incident:
- issue_key
- title
- description
- severity
- service
- category
- created_at
- updated_at

Classification:
- category
- service

RAG:
- query
- retrieved_chunks
- source
- document_type
- chunk_id
- score
- text

RCA:
- root_cause
- status
- evidence

Resolution:
- recommendation
- steps
- risks
- evidence

Approval:
- status
- reviewer
- timestamp
- reason
- feedback

Workflow:
- current_stage
- stage status
- started_at
- completed_at

Jira:
- jira_update_status
- jira_update_completed_at
- jira_update_message if failed

Do not expose raw backend state.

Do not expose:
- prompts
- LangGraph nodes
- internal state objects
- Qdrant implementation
- database internals
- raw execution logs

============================================================
7. NEW FRONTEND STRUCTURE
============================================================

Create a clean structure similar to:

frontend/
│
├── src/
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar
│   │   │   ├── Header
│   │   │   └── PageContainer
│   │   │
│   │   ├── dashboard/
│   │   │   ├── StatCard
│   │   │   ├── LiveOperations
│   │   │   ├── NeedsAttention
│   │   │   ├── WorkflowOverview
│   │   │   ├── IncidentTable
│   │   │   └── JiraUpdates
│   │   │
│   │   ├── incident/
│   │   │   ├── IncidentHeader
│   │   │   ├── CurrentStatusPanel
│   │   │   ├── WorkflowTimeline
│   │   │   ├── IncidentInformation
│   │   │   ├── ClassificationSection
│   │   │   ├── EvidenceSection
│   │   │   ├── RCASection
│   │   │   └── ResolutionSection
│   │   │
│   │   ├── approval/
│   │   │   ├── ApprovalQueue
│   │   │   ├── ApprovalReview
│   │   │   ├── ApprovalPanel
│   │   │   ├── ApproveButton
│   │   │   ├── RejectButton
│   │   │   └── RejectDialog
│   │   │
│   │   └── common/
│   │       ├── StatusBadge
│   │       ├── SeverityBadge
│   │       ├── LoadingState
│   │       ├── EmptyState
│   │       ├── ErrorState
│   │       └── SectionHeader
│   │
│   ├── pages/
│   │   ├── Dashboard.jsx
│   │   ├── Incidents.jsx
│   │   ├── IncidentDetails.jsx
│   │   └── Approvals.jsx
│   │
│   ├── services/
│   │   └── api.js
│   │
│   ├── hooks/
│   │   ├── useIncidents.js
│   │   └── useIncident.js
│   │
│   ├── types/
│   │   └── incident.js
│   │
│   ├── router/
│   │   └── index.jsx
│   │
│   ├── App.jsx
│   ├── main.jsx
│   └── styles/
│
├── public/
├── package.json
└── README.md

You may adjust this structure if a better React architecture is appropriate.

Do not create unnecessary files.

============================================================
8. GLOBAL DESIGN DIRECTION
============================================================

The UI should look like a real engineering operations product.

NOT:

"generic AI dashboard"

NOT:

"ChatGPT clone"

NOT:

"template with 20 cards"

NOT:

"purple gradient SaaS landing page"

The visual personality should be:

- intelligent
- technical
- calm
- modern
- operational
- trustworthy
- slightly creative
- eye-catching without being childish
- professional enough for enterprise use

Use a neutral base with a sophisticated accent system.

Do not make everything colorful.

Use color primarily to communicate meaning.

Suggested semantic language:

PROCESSING
→ amber/orange

AWAITING APPROVAL
→ violet/indigo

SUCCESS / JIRA UPDATED
→ green

FAILED
→ red/coral

PENDING
→ muted gray

CRITICAL
→ red

HIGH
→ orange

MEDIUM
→ amber

LOW
→ muted/cool

Use lightly tinted backgrounds rather than giant bright boxes.

============================================================
9. GLOBAL LAYOUT
============================================================

Use a persistent left sidebar.

Suggested navigation:

ResolveIQ

Overview
Incidents
Approvals

----------------

System
Settings

Do NOT add an Audit page.

Header should contain:

Page title
Short contextual description
Search / useful controls
System status

The main content should have generous spacing.

Use moderate corner radius.

Do not make every element a rounded card.

Use:
- panels
- dividers
- timelines
- tables
- status strips
- highlighted areas
- split layouts

============================================================
10. DASHBOARD DESIGN
============================================================

The Dashboard is the most important page.

It should feel like:

"Incident Command Center"

Suggested composition:

------------------------------------------------------------

RESOLVEIQ
Incident Operations

Monitor, investigate and resolve incidents.

                         [ Search ]    ● System Operational

------------------------------------------------------------

LIVE OPERATIONS

┌─────────────────────────────────────────────────────────────┐
│ ● LIVE OPERATIONS                                           │
│                                                             │
│ INC-1042   RCA completed        → Awaiting approval         │
│ INC-1041   Resolution generated → Processing                │
│ INC-1038   Jira update          → ✓ Completed               │
│                                                             │
│ Last updated 12 seconds ago                                 │
└─────────────────────────────────────────────────────────────┘

This should be a slightly colored/tinted horizontal panel.

It should visually communicate that the system is currently doing work.

Use a subtle animated indicator for active processing.

Do not make the animation distracting.


------------------------------------------------------------

OVERVIEW

Do NOT make five identical cards.

Create a varied visual composition.

Example:

┌─────────────────────────┐
│ ACTIVE INCIDENTS         │
│                          │
│ 12                       │
│ incidents                │
│                          │
│ 4 currently processing   │
└─────────────────────────┘


┌────────────────────────────────────────────────┐
│ ⚠ NEEDS ATTENTION                              │
│                                                │
│ 3 incidents awaiting human approval             │
│                                                │
│ INC-1042   Payment API latency    HIGH         │
│ INC-1035   DB connection issue    CRITICAL     │
│                                                │
│                 Review approvals →             │
└────────────────────────────────────────────────┘


Then a smaller row:

┌───────────────┐
│ PROCESSING    │
│      4        │
│ ● Running     │
└───────────────┘

┌───────────────┐
│ RESOLVED      │
│     18        │
│ ✓ Complete    │
└───────────────┘

┌───────────────┐
│ JIRA UPDATED  │
│     16        │
│ ✓ Synced      │
└───────────────┘

Make these visually different but part of the same design system.


------------------------------------------------------------

WORKFLOW OVERVIEW

Create a compact visual representation:

                 RESOLVING NOW

Retrieved → Classify → RAG → RCA → Resolution
                                      ↓
                                  Approval
                                      ↓
                                  Jira ✓

Under/around each stage show how many incidents currently occupy it.

Example:

Retrieved  2
Classify   1
RAG        2
RCA        3
Resolution 2
Approval   3
Jira ✓    16

This should feel like an operational pipeline, not a technical architecture diagram.


------------------------------------------------------------

RECENT INCIDENTS

Create a clean table:

ID
Incident
Severity
Service
Stage
Status
Updated
Action

Example:

INC-1042
Payment API latency
HIGH
Payments
RCA
● Processing
2m ago
View →

INC-1041
Database connection pool
CRITICAL
Database
Approval
⚠ Review
5m ago
View →

INC-1038
Authentication timeout
MEDIUM
Auth
Jira
✓ Updated
12m ago
View →


------------------------------------------------------------

RECENT JIRA UPDATES

Create a dedicated section.

┌─────────────────────────────────────────────────────────────┐
│ RECENTLY UPDATED IN JIRA                                    │
│                                                             │
│ ✓ INC-1038   Authentication timeout       2 min ago         │
│ ✓ INC-1035   Database connection issue    8 min ago         │
│ ✓ INC-1029   Payment retry failure       15 min ago         │
│                                                             │
│ View incidents →                                            │
└─────────────────────────────────────────────────────────────┘

This is important because Jira writeback is part of the MVP.


============================================================
11. EMPTY DASHBOARD STATE
============================================================

IMPORTANT:

Even if there are ZERO incidents when the application first loads,
the dashboard must still look intentional and complete.

Do NOT show a blank page.

Keep the page structure visible.

For example:

ACTIVE INCIDENTS
0

PROCESSING
0

AWAITING APPROVAL
0

RESOLVED
0

JIRA UPDATED
0


LIVE OPERATIONS

┌─────────────────────────────────────────────────────────────┐
│ ● SYSTEM READY                                              │
│                                                             │
│ No incidents are currently being processed.                 │
│ New incidents will appear here as they enter ResolveIQ.     │
└─────────────────────────────────────────────────────────────┘


NEEDS ATTENTION

No approvals waiting for review.

Keep the section itself visible.


WORKFLOW

Retrieved → Classification → RAG → RCA → Resolution
                                      ↓
                                  Approval
                                      ↓
                                  Jira

Show the pipeline even when counts are zero.

This makes the UI feel complete from the first launch.

============================================================
12. INCIDENTS PAGE
============================================================

Create a dedicated Incidents page.

Include:

Page heading:

Incidents

"Monitor every incident moving through ResolveIQ."

Include:
- search
- severity filter
- status filter
- service/category filter if supported

Main table:

Incident ID
Title
Severity
Service
Category
Workflow Stage
Status
Last Updated
Action

Use clear status badges.

Rows should be clickable.

Empty state:

"No incidents yet"

Supporting text:

"Incidents retrieved from Jira will appear here."

Do not make an empty table look broken.

============================================================
13. INCIDENT DETAILS PAGE
============================================================

This page should tell the COMPLETE STORY of one incident.

Layout:

------------------------------------------------------------

← Back to incidents

INC-1042

Payment API latency spike

[ HIGH ] [ Payments ] [ Awaiting Approval ]

Created 12:42 PM
Updated 12:48 PM

------------------------------------------------------------

CURRENT STATUS

Create a prominent slightly colored status panel.

Example:

┌─────────────────────────────────────────────────────────────┐
│ ● CURRENTLY RUNNING                                         │
│                                                             │
│ Waiting for human approval                                  │
│                                                             │
│ ResolveIQ completed RCA and generated a resolution          │
│ recommendation.                                             │
│                                                             │
│ Next action: Review recommendation                           │
└─────────────────────────────────────────────────────────────┘

If RCA is processing:

┌─────────────────────────────────────────────────────────────┐
│ ● CURRENTLY PROCESSING                                      │
│                                                             │
│ Root Cause Analysis                                         │
│                                                             │
│ ResolveIQ is analyzing retrieved evidence...                │
└─────────────────────────────────────────────────────────────┘

If Jira was successfully updated:

┌─────────────────────────────────────────────────────────────┐
│ ✓ RESOLVED                                                  │
│                                                             │
│ Jira updated successfully                                   │
│                                                             │
│ Updated at 12:49 PM                                         │
└─────────────────────────────────────────────────────────────┘

This status panel is one of the main visual elements of the page.


------------------------------------------------------------

WORKFLOW TIMELINE

Show:

✓ Incident Retrieved
  12:42 PM

│

✓ Normalized
  12:42 PM

│

✓ Classification
  12:43 PM

│

✓ Knowledge Retrieved
  12:44 PM

│

✓ Root Cause Analysis
  12:46 PM

│

✓ Resolution
  12:47 PM

│

● Human Approval
  Currently waiting

│

○ Jira Update
  Waiting for approval

Clearly distinguish:

COMPLETED
PROCESSING
PENDING
FAILED

Use subtle colors and visual indicators.


------------------------------------------------------------

INCIDENT INFORMATION

Show:

Title
Description
Severity
Service
Category
Created
Updated


------------------------------------------------------------

CLASSIFICATION

Show:

Category
Service

Keep it concise.


------------------------------------------------------------

KNOWLEDGE / EVIDENCE

Create an evidence workspace.

Example:

KNOWLEDGE USED

4 relevant sources

┌─────────────────────────────────────────────────────────────┐
│ Runbook: Payment API Latency                                │
│ Operational Runbook                                         │
│                                                             │
│ "Relevant knowledge snippet..."                             │
│                                                             │
│ Relevance                                      92%          │
│ ████████████████████░                                      │
│                                                             │
│ View source →                                               │
└─────────────────────────────────────────────────────────────┘

Allow evidence to expand/collapse.

Show:
- source
- document type
- chunk ID
- relevance score
- snippet

Do not show raw Qdrant internals.


------------------------------------------------------------

ROOT CAUSE ANALYSIS

Make the root cause visually prominent.

Example:

ROOT CAUSE

Database connection pool exhaustion

The RCA result should be easy to understand.

Show:
- RCA status
- root cause
- supporting evidence

Do not present unexplained internal reasoning.


------------------------------------------------------------

PROPOSED RESOLUTION

Show:

RECOMMENDATION

Increase database connection pool capacity and
restart affected payment workers.

STEPS

01 Increase connection pool limit
02 Restart affected workers
03 Monitor database utilization
04 Verify payment latency

RISKS

⚠ Temporary increase in database resource usage

EVIDENCE

Based on retrieved knowledge.


------------------------------------------------------------

HUMAN APPROVAL

Show approval state.

If pending:

Awaiting your decision

[ APPROVE ]    [ REJECT ]

If approved:

✓ Approved
Reviewer
Timestamp

Then immediately show:

JIRA UPDATE

● Updating Jira...

or:

✓ Jira Updated
Updated at 12:49 PM

If Jira fails:

! Jira Update Failed

Show only a clean backend-provided failure message.

Do not show stack traces.


============================================================
14. APPROVAL PAGE
============================================================

This is a HUMAN DECISION CENTER.

Header:

Approval Queue

"Review AI-generated resolutions before they are applied to Jira."

At the top, create a dedicated status area:

------------------------------------------------------------

APPROVAL OVERVIEW

3 awaiting review

12 resolved

16 Jira updates completed

2 failed workflows

------------------------------------------------------------

Even when there are ZERO approvals:

┌─────────────────────────────────────────────────────────────┐
│ ✓ ALL CAUGHT UP                                             │
│                                                             │
│ No incidents are waiting for human approval.               │
│                                                             │
│ ResolveIQ will surface new recommendations here.            │
└─────────────────────────────────────────────────────────────┘

BUT KEEP THE PAGE STRUCTURE VISIBLE.

Also show dedicated sections/headings for:

Awaiting Approval
Recently Approved
Jira Updates

Do not make the page look empty.


------------------------------------------------------------

APPROVAL QUEUE

Example:

┌─────────────────────────────────────────────────────────────┐
│ INC-1042                                                    │
│ Payment API latency                                         │
│                                                             │
│ HIGH       Payments                                         │
│                                                             │
│ RCA: Database connection pool exhaustion                    │
│                                                             │
│ Resolution recommendation ready                             │
│                                                             │
│                                  Review →                   │
└─────────────────────────────────────────────────────────────┘


------------------------------------------------------------

APPROVAL REVIEW

When reviewing:

Use a two-column layout.

LEFT:

INCIDENT
Classification
RCA
Evidence

RIGHT:

┌─────────────────────────────────────────────────────────────┐
│ PROPOSED RESOLUTION                                         │
│                                                             │
│ Increase connection pool capacity...                        │
│                                                             │
│ RISKS                                                       │
│ ⚠ Temporary resource increase                               │
│                                                             │
│ ----------------------------------------------------------- │
│                                                             │
│ HUMAN DECISION                                               │
│                                                             │
│ [ ✓ APPROVE ]        [ REJECT ]                             │
└─────────────────────────────────────────────────────────────┘


------------------------------------------------------------

AFTER APPROVAL

The approval page MUST continue showing Jira status.

Show:

✓ RESOLUTION APPROVED

Approved by:
Reviewer

Approved at:
12:48 PM


Then:

● JIRA UPDATE
Updating Jira...


Then:

✓ JIRA UPDATED
Successfully updated in Jira
12:49 PM

This should remain visible after approval.

If Jira update fails:

! JIRA UPDATE FAILED

Resolution approved, but Jira could not be updated.

Status:
Failed

Jira message:
<backend-provided message>

Do not expose internal API traces.


============================================================
15. APPROVAL REJECTION
============================================================

Clicking REJECT opens a dialog.

Title:

Reject Resolution

Question:

Why are you rejecting this recommendation?

Textarea:

Feedback

Buttons:

Cancel
Reject Resolution

Send the rejection to:

POST /api/incidents/{issue_key}/reject

Do not create an LLM call.

============================================================
16. LIVE WORKFLOW UPDATES
============================================================

For the MVP use polling if live updates are required.

Use:

GET /api/incidents/{issue_key}

while an incident is processing.

The UI should update when the workflow moves:

pending
→ processing
→ completed

and show timestamps where available.

Do NOT implement WebSockets.

Do NOT connect directly to agents.

Do NOT connect directly to Jira.

============================================================
17. INTERACTION DESIGN
============================================================

Make the interface interactive and polished.

Use:

- subtle hover states
- expandable evidence
- clickable incidents
- workflow transitions
- loading skeletons
- smooth status changes
- subtle processing indicators
- confirmation states
- useful tooltips where necessary

Avoid:
- excessive animation
- bouncing elements
- flashy transitions
- decorative effects with no purpose

The UI should feel alive because of its DATA and STATUS,
not because of unnecessary animation.


============================================================
18. DESIGN SYSTEM
============================================================

Choose the final palette yourself, but follow these principles:

Neutral foundation.

One primary brand accent.

Semantic status colors.

Slightly tinted status panels.

Strong typography.

Moderate corner radius.

Subtle borders.

No excessive gradients.

No neon.

No excessive shadows.

No glassmorphism.

No huge decorative illustrations.

Use icons sparingly and consistently.

The result should feel designed by a professional product designer.


============================================================
19. RESPONSIVENESS
============================================================

Desktop-first.

This is an engineering operations platform.

Support:
- desktop
- tablet
- mobile

Avoid horizontal overflow.

Tables should adapt on smaller screens.


============================================================
20. ACCESSIBILITY
============================================================

Use:

- semantic HTML
- accessible buttons
- keyboard navigation
- visible focus states
- sufficient contrast
- meaningful labels
- accessible dialogs
- accessible status indicators


============================================================
21. EMPTY / LOADING / ERROR STATES
============================================================

Every major page must have intentional states.

EMPTY:

Do not show blank white space.

Show:
- section heading
- zero state
- explanation
- useful next action if appropriate

LOADING:

Use skeletons or subtle loading indicators.

ERROR:

Show a clean explanation.

Never show:
- stack traces
- raw API errors
- database errors
- internal implementation details


============================================================
22. IMPORTANT MVP BOUNDARIES
============================================================

DO NOT implement:

- Revision Agent
- revision workflow
- SOP generation
- KB generation
- audit page
- detailed audit logs
- agent execution logs
- chatbot
- WebSockets
- direct Supabase connection
- direct Jira connection
- direct Qdrant connection

Jira Update MUST be represented as a real MVP workflow stage.

The user must be able to visually understand:

AI analyzes
      ↓
AI recommends
      ↓
Human approves/rejects
      ↓
Approved
      ↓
Jira updated


============================================================
23. BUILD ORDER
============================================================

Build in this order:

STEP 1
Inspect the existing backend and identify the REAL API contracts.

STEP 2
Create frontend foundation and routing.

STEP 3
Create the API service layer using the REAL backend endpoints.

STEP 4
Create global layout and design system.

STEP 5
Build Dashboard.

STEP 6
Build Incidents page.

STEP 7
Build Incident Details.

STEP 8
Build Approvals page.

STEP 9
Connect and verify all pages against the REAL FastAPI responses.

STEP 10
Implement polling if supported/required by the backend.

STEP 11
Implement loading/empty/error states.

STEP 12
Test responsive behavior.

STEP 13
Run build/lint/tests.

Do NOT attempt to implement everything as one giant component.

============================================================
24. IMPORTANT DATA BEHAVIOR
============================================================

Do not fabricate real incident data.

If the backend currently returns no incidents,
render the designed zero states.

For development visualization only, if mock data is absolutely
necessary, isolate it clearly in a mock-data module and make
it trivial to remove when real APIs are connected.

Do not mix fake data into the API layer.

============================================================
25. FINAL QUALITY CHECK
============================================================

Before finishing, inspect every page.

Ask:

Does this look like a real incident operations platform?

Does the Dashboard immediately answer:

"What needs my attention?"

Can I clearly see:
- active incidents?
- processing incidents?
- approvals waiting?
- resolved incidents?
- Jira updates?
- failed workflows?

Can I open an incident and understand its entire journey?

Can I understand the RCA evidence?

Can I understand the proposed resolution and risks?

Can I approve/reject?

After approval, can I clearly see:

Approved
↓
Updating Jira
↓
Jira Updated

Does the Approval page still show Jira status after approval?

Does the application still look complete when there are ZERO incidents?

Does the UI look creative and distinctive without becoming flashy?

Does it look intentionally designed rather than AI-generated?

============================================================
26. FINAL REPORT
============================================================

After implementation, report:

1. New frontend folder location
2. Pages created
3. Routes created
4. Components created
5. API endpoints integrated
6. API service architecture
7. Empty states implemented
8. Loading states implemented
9. Error states implemented
10. Polling implementation
11. Design system / color language
12. How Jira status is represented
13. Build result
14. Lint result
15. Test result
16. Any backend contract assumptions

IMPORTANT:

The existing frontend folder was intentionally ignored.

Do NOT modify it.

Do NOT delete it.

Do NOT replace it.

The new frontend must be independently structured and built
from this specification.

NON-DESTRUCTIVE CHANGES ONLY.
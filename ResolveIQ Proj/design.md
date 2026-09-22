I want you to completely redesign and improve the existing ResolveIQ frontend.

IMPORTANT SAFETY RULE:
Do NOT delete the existing frontend project.
Do NOT delete, move, rename, overwrite, replace, or restructure files unnecessarily.
Do NOT run destructive commands.
Do NOT replace the project with a template.
First inspect the entire existing frontend structure, routes, components, styles, assets, and current pages.
Then make targeted modifications.
Preserve working functionality and API integrations.

PROJECT CONTEXT

ResolveIQ is an AI-assisted incident resolution platform.

The core workflow is:

Jira Incident
    ↓
Incident Ingestion
    ↓
Classification
    ↓
Knowledge/RAG
    ↓
Root Cause Analysis
    ↓
Resolution Recommendation
    ↓
Human Approval
    ↓
Approved → Jira Writeback
Rejected → End

The current frontend is too shallow and incomplete. Some pages/routes are missing and the current visual design does not feel like a finished product.

Your task is to redesign the frontend into a polished, distinctive, production-quality interface.

IMPORTANT:
Do NOT simply add more cards or make everything rounded.
Do NOT use a generic "AI SaaS dashboard" template.
Do NOT use excessive purple/blue gradients, glowing effects, glassmorphism, robot imagery, or stereotypical AI visuals.
The product should look like a serious modern engineering/incident-management platform.

DESIGN DIRECTION

Create a strong visual identity for ResolveIQ.

The design should feel:

- modern
- technical
- intelligent
- trustworthy
- operational
- clean
- slightly distinctive/creative
- professional enough for an enterprise engineering team

Use a thoughtful color system rather than random colors.

Use color meaningfully for:
- severity
- incident status
- workflow stages
- confidence
- approval/rejection
- successful Jira synchronization
- warnings/errors

Do not make the entire interface colorful.
Use a neutral foundation with carefully chosen accent colors.

LAYOUT PRINCIPLES

Do not make every page follow the same:

Title
↓
3 cards
↓
table

pattern.

Use different layouts depending on the purpose of the page.

Use:
- strong typography
- whitespace
- visual hierarchy
- subtle borders
- dividers
- timeline/progress elements
- split panels
- contextual side panels
- expandable evidence sections
- meaningful status indicators

Avoid excessive cards.

The interface should feel intentionally designed rather than generated from a component library.

CORE PAGES

Inspect the existing frontend first.

Ensure the application has properly designed pages for at least:

1. Dashboard
2. Incidents
3. Incident Details
4. Classification
5. RCA / Root Cause Analysis
6. Resolution
7. Approval
8. Knowledge / Evidence
9. Settings or system configuration if appropriate

If some of these pages do not currently exist, create them using the existing frontend architecture.

Do not create meaningless pages just to increase the page count.

DASHBOARD

Design the dashboard around operational awareness.

It should communicate:
- active incidents
- severity distribution
- incidents currently being analyzed
- resolved incidents
- approval-required incidents
- recent activity
- workflow health

Use appropriate visualizations or compact data representations where useful.

Do not fill the dashboard with decorative statistics that are not backed by actual application data.

INCIDENT LIST

Create a useful incident-management interface.

Show information such as:
- incident ID
- title
- severity
- service
- status
- created/updated time
- current workflow stage

Make filtering/searching easy to understand.

INCIDENT DETAILS

This should be one of the strongest pages in the application.

Design it around the actual incident-resolution workflow.

Show:

Incident information
↓
Classification
↓
Retrieved knowledge/evidence
↓
Root cause analysis
↓
Resolution recommendation
↓
Human approval
↓
Jira writeback status

Make the workflow visually understandable.

Use a timeline, stepper, progress indicator, or another thoughtful representation.

RCA PAGE

Make evidence a first-class part of the UI.

Show:
- root cause
- RCA status
- supporting evidence
- source/chunk IDs
- evidence relevance/confidence where available

The user should be able to understand WHY the system reached the RCA conclusion.

Do not present AI-generated reasoning as unexplained magic.

RESOLUTION PAGE

Clearly separate:

Recommendation
Steps
Risks
Evidence

Make the recommended resolution easy to scan.

Approval should be visually prominent but not aggressive.

APPROVAL PAGE

Human approval is a critical part of ResolveIQ.

Make it obvious that:

AI recommends → Human decides → Jira is updated only after approval.

Show:
- incident
- RCA
- evidence
- recommended resolution
- risks
- approval status
- reviewer
- timestamp
- reason/feedback

Approved and rejected states should be visually distinct.

KNOWLEDGE / EVIDENCE

Design retrieved knowledge so it feels trustworthy.

Show:
- source
- document type
- chunk ID
- relevance score
- content/snippet

Avoid presenting raw technical data in an ugly JSON-like interface unless it is specifically useful.

MICROINTERACTIONS

Use subtle animations and transitions.

Examples:
- workflow stage transitions
- expanding evidence
- hover states
- loading states
- status changes
- approval state changes

Do not over-animate.

TYPOGRAPHY

Use a strong, readable typography system.

Create clear hierarchy between:
- page titles
- section titles
- incident titles
- metadata
- labels
- body text
- technical information

Do not use oversized headings everywhere.

COMPONENT SYSTEM

Create reusable components where appropriate:

- StatusBadge
- SeverityBadge
- WorkflowStepper/Timeline
- IncidentHeader
- EvidenceCard/Panel
- RCASection
- ResolutionSection
- ApprovalPanel
- ActivityTimeline
- DataTable
- EmptyState
- LoadingState
- ErrorState

But do not componentize everything unnecessarily.

FUNCTIONALITY

Preserve all existing API calls and working functionality.

Do not create fake backend data unless the existing frontend already uses mock data.

If backend endpoints are not available yet:
- create sensible loading/empty states
- keep the UI ready for real API integration
- clearly isolate mock data if absolutely necessary

Do not invent backend functionality.

RESPONSIVENESS

Make the application responsive.

Desktop is the primary target because ResolveIQ is an engineering operations platform, but tablet/mobile layouts should remain usable.

ACCESSIBILITY

Use:
- sufficient contrast
- keyboard-friendly controls
- semantic HTML
- visible focus states
- accessible buttons/forms
- meaningful labels

FINAL QUALITY BAR

Before finishing, inspect the application as a whole.

Ask:

"Does this look like a real incident-resolution product designed by a product designer, or does it look like an AI-generated dashboard?"

If it looks generic, improve the visual hierarchy, spacing, composition, typography, and color system.

Do not stop after changing colors.

I want an actual redesign of the experience, not just cosmetic CSS changes.

IMPORTANT:
Do not touch backend code.
Do not change API contracts unless absolutely necessary for frontend compatibility.
Do not implement Revision Agent functionality.
Do not modify the ResolveIQ backend architecture.

At the end, provide:

1. Pages created
2. Pages redesigned
3. Components created
4. Existing functionality preserved
5. API integrations preserved
6. Files modified
7. Files created
8. Any missing backend functionality preventing a page from being fully functional
9. A short explanation of the new visual design system
10. Run the frontend build/lint/tests and report the results.

Remember:
NON-DESTRUCTIVE CHANGES ONLY.
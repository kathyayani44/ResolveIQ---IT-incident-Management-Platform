Work only on the **ResolveIQ account ↔ actual Jira account integration and incident synchronization** first. Do not redesign the frontend or modify the AI agents yet.

The goal is: when I log into my ResolveIQ account, it must be connected to my actual Jira account, and ResolveIQ must show the **real Jira requests/issues from my account with their actual current Jira status**.

Please inspect the existing implementation before changing anything.

## STRICT SAFETY / GUARDRAIL RULES

These rules are mandatory:

1. **READ-ONLY Jira access during this task**

   * This task is primarily for authentication, synchronization, retrieval, and display.
   * Do NOT create Jira issues.
   * Do NOT create projects.
   * Do NOT delete Jira issues, projects, comments, users, attachments, or any Jira data.
   * Do NOT modify, transition, resolve, close, reopen, assign, or edit existing Jira issues.
   * Do NOT change Jira workflows, permissions, project settings, fields, schemes, or configurations.
   * Do NOT add/remove Jira users or permissions.
   * Do NOT create test/sample incidents in my actual Jira project.
   * Do NOT send comments or other write requests to Jira.
   * Do NOT trigger Jira webhooks manually if doing so would modify data.
   * Jira API calls for this task should be **GET/read-only operations wherever possible**.

2. **Protect the existing ResolveIQ project**

   * Do NOT delete files or folders.
   * Do NOT overwrite existing working files unnecessarily.
   * Do NOT reset, clean, recreate, replace, or reinitialize the project.
   * Do NOT remove existing database tables, records, migrations, configuration, tests, or working code.
   * Do NOT run destructive commands such as `git reset --hard`, `git clean`, database drops, table drops, or mass deletes.
   * Do NOT replace the current implementation with a new architecture.
   * Make changes incrementally and preserve the existing working implementation.

3. **No fake data**

   * Do not create fake Jira issues just to test the UI.
   * Do not hardcode `RESIQ-1`, `RESIQ-2`, or any other issue key.
   * Do not use mock/sample incidents as a fallback when real Jira data is expected.
   * If real Jira data cannot be retrieved, show a clear error instead of inventing data.

4. **Before changing anything**

   * Inspect the existing Jira integration, authentication, API routes, database/storage, frontend API calls, and incident list logic.
   * Identify exactly where the current incident list and Jira status are coming from.
   * Identify the root cause of incorrect/missing Jira issues or incorrect statuses.
   * Only then make the minimum necessary changes.

---

## 1. ResolveIQ Authentication & Jira Connection

Create/verify a simple ResolveIQ authentication flow:

* User should be able to create/login to a ResolveIQ account.
* The ResolveIQ account must have a clear connection to the user's Jira account.
* Do not hardcode Jira users, issue keys, credentials, or sample incidents.
* Store credentials/secrets safely using environment variables or the appropriate secure mechanism.
* Never expose Jira API tokens or secrets in the frontend.
* The frontend must communicate with the ResolveIQ backend, not directly with Jira using secrets.

The Jira connection should be associated with the authenticated ResolveIQ user rather than being a global hardcoded account.

## 2. Fix Jira Integration Completely

Verify:

* Jira REST API authentication.
* Jira base URL/domain configuration.
* Jira account/user being authenticated.
* Jira project/account being accessed.
* API permissions required to read the issues.
* Correct Jira REST endpoints.
* Pagination behavior.

Fetch the **actual issues/requests accessible to the authenticated Jira account**.

Do not use hardcoded issue keys such as `RESIQ-1` or `RESIQ-2`.

Do not use mock/sample data as a fallback.

If Jira authentication fails, return a clear authentication/connection error.

## 3. Proper Backend Incident Endpoint

Implement or verify a backend endpoint that retrieves the user's actual Jira incidents/issues.

The endpoint should return real Jira data and include at minimum:

* Issue key
* Summary
* Description
* Priority
* Jira status
* Created timestamp
* Updated timestamp
* Assignee, where available
* Reporter, where available
* Resolution, where available

Keep these two concepts completely separate:

**Jira issue status**
→ The actual status reported by Jira.

**ResolveIQ workflow status**
→ The internal AI processing state.

Never mix them.

## 4. Jira Status Must Be the Source of Truth

Jira is the source of truth for the actual Jira issue status.

Never infer Jira status from:

* AI workflow completion
* Classification completion
* RAG completion
* RCA completion
* Resolution generation
* Human approval
* ResolveIQ frontend state
* Database processing state

For example:

If Jira reports:

`Open`

ResolveIQ must show:

`Open`

If Jira reports:

`In Progress`

ResolveIQ must show:

`In Progress`

If Jira reports:

`Resolved`

ResolveIQ must show:

`Resolved`

If Jira reports:

`Done`

ResolveIQ must show:

`Done`

Do not convert an Open/In Progress Jira issue into Completed merely because ResolveIQ finished processing it.

## 5. Frontend Must Display Real Jira Issues

Make the frontend dynamically retrieve the incidents from the backend.

Requirements:

* Display all available real Jira issues for the connected account.
* Remove hardcoded incident keys.
* Do not silently substitute fake data.
* Do not display stale hardcoded incident data.
* Refresh/reload should retrieve the current Jira state.
* If Jira cannot be reached, clearly display something like:

**"Unable to retrieve incidents from Jira."**

Do not display incorrect completed/resolved incidents when the Jira request failed.

## 6. Pagination

Verify that the Jira API pagination is handled correctly.

If the Jira account has more issues than one API response:

* Continue fetching subsequent pages.
* Do not stop after a small hardcoded number.
* Do not accidentally display only `RESIQ-1`, `RESIQ-2`, etc.
* Ensure the ResolveIQ incident list represents all issues accessible to the connected Jira account, subject to the intended project/filter scope.

## 7. Synchronization / Refresh

Refreshing ResolveIQ should retrieve the current Jira state.

Do not rely only on:

* frontend local state
* hardcoded JSON
* stale database values
* previously loaded sample incidents

The system should be able to re-fetch Jira and reflect the current Jira status.

If cached/synchronized data is used for performance, clearly define when it is refreshed and ensure Jira remains authoritative for current issue status.

## 8. Tests

Add or update tests for:

* Jira authentication/configuration
* Jira connection failure
* Fetching real issue data
* Multiple Jira issues
* Empty Jira result
* Jira API failure
* Jira authentication failure
* Correct Jira status mapping
* Open → remains Open
* In Progress → remains In Progress
* Resolved → remains Resolved
* Done → remains Done
* ResolveIQ workflow completion must NOT change Jira status
* No hardcoded issue keys
* Pagination
* Frontend/API handling of Jira errors

Tests must not create or modify data in my real Jira project.

Use mocks/stubs for destructive/write scenarios if needed. For real Jira verification, use **read-only API requests only**.

## 9. No Destructive Testing

When testing against my actual Jira account:

**Allowed:**

* Authenticate
* Read current user/account information
* Read projects
* Read accessible issues
* Read issue details
* Read statuses
* Read resolutions
* Read pagination results

**Not allowed:**

* Create
* Update
* Delete
* Transition
* Resolve
* Close
* Reopen
* Assign
* Comment
* Edit
* Move
* Bulk modify
* Change project settings
* Change permissions

If a test requires a write operation, do NOT perform it against my real Jira account. Use a mock/unit test instead.

## 10. Final Verification

Before declaring the task complete, verify this complete **read-only** flow:

ResolveIQ Login
→ Connected Jira Account
→ Authenticate with Jira
→ Jira REST API
→ Fetch ALL accessible Jira issues
→ Synchronize/store safely
→ FastAPI
→ React frontend
→ Display real Jira issues
→ Display exact current Jira status

Use my actual Jira account/data for **read-only verification**.

Do not create any test issues or modify my Jira project.

## 11. Final Report

At the end, report:

1. Where the incident list was previously coming from.
2. Where the Jira status was previously coming from.
3. Exact root cause of the incorrect/missing data.
4. Files changed.
5. What was changed.
6. Tests added/updated.
7. Test results.
8. Number of real Jira issues successfully retrieved.
9. Confirmation that pagination works.
10. Confirmation that Jira status is treated as the source of truth.
11. Confirmation that no Jira issues/projects/data were created, deleted, or modified.
12. Any remaining limitations.

**Most important:** do not assume the task is successful merely because the frontend displays incidents. Verify that the incidents originate from the authenticated Jira account and that their displayed statuses match the current values returned by Jira's API.

Do not proceed to workflow-stage fixes, AI-agent changes, Jira writeback, or frontend redesign in this task. This task is only about **ResolveIQ authentication, Jira connection, real Jira issue retrieval, synchronization, and accurate Jira status display**.

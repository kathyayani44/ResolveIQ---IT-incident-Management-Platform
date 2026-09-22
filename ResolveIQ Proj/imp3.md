# Implementation Plan: ResolveIQ Workflow Enhancements & Registration/Login System

Implement the requirements from `imp3.md`:
1. **Part 1 — Workflow & Grounding Enhancements**:
   - Explicit `INSUFFICIENT_EVIDENCE` stage status across backend and frontend.
   - Safe grounding default (`is_grounded=False`, `grounding_type="insufficient_evidence"`).
   - Strict evidence verification (chunk ID validation) before grounding.
   - Zero RAG evidence prevents Resolution LLM invocation.
   - Backend authoritative gate: approval strictly rejected unless grounded and at `AWAITING_APPROVAL`.
   - Evidence provenance persistence (`evidence_sources`).
   - Consistent RCA/Resolution semantics: `insufficient_evidence` blocks downstream completion.
   - Precise UI status messaging distinguishing successful grounded analysis, insufficient evidence, and pipeline failures.
   - Proven automated tests for both zero-evidence and valid-evidence branches.

2. **Part 2 — User Registration & Login System**:
   - Dedicated clean, minimal **Login** and **Register** views in the frontend (collecting only Name, Email, Password; strictly no Jira fields).
   - Secure password hashing using PBKDF2 HMAC SHA-256 with 100,000 iterations and per-user salt; zero plaintext storage.
   - User account persistence in Supabase `users` table with file cache backup for restart resilience.
   - Unauthenticated redirection: users cannot access the dashboard or incident views without logging in.
   - Authenticated session maintenance (`localStorage` token + `GET /auth/me`).
   - Current account display in header and sidebar with a clear Sign Out action.
   - Full automated test suite for registration, duplicate emails, login verification, invalid credentials, and authenticated access.

---

## User Review Required

> [!NOTE]
> Authentication is strictly separated from Jira credentials. Jira credentials remain backend-configured for the MVP as specified in `imp3.md`. Registration will only request Name, Email, and Password.

> [!NOTE]
> When unauthenticated, the frontend will present the clean, minimal Login/Register screen directly instead of showing the dashboard or incident management controls.

---

## Proposed Changes

### Backend: Schemas, Pipeline, Approval Gate & Auth

#### [MODIFY] [app/schemas/incident.py](file:///c:/Users/usrav/Downloads/ResolveIQ%20Proj/ResolveIQ%20Proj/app/schemas/incident.py)
- Define `StageStatus` Literal type explicitly:
  `Literal["NOT_STARTED", "PROCESSING", "COMPLETED", "FAILED", "BLOCKED", "INSUFFICIENT_EVIDENCE", "AWAITING_APPROVAL", "APPROVED", "REJECTED", "SKIPPED"]`.

#### [MODIFY] [app/services/approval_service.py](file:///c:/Users/usrav/Downloads/ResolveIQ%20Proj/ResolveIQ%20Proj/app/services/approval_service.py)
- Enforce strict backend validation in `process_approval`:
  - Verify that `awaiting_approval` stage is specifically `"AWAITING_APPROVAL"`.
  - Verify that `package.resolution.is_grounded` is `True` AND `package.resolution.grounding_type == "rag_grounded"`.
  - Verify that `package.resolution.evidence` contains valid chunk IDs from `package.evidence`.
  - Reject approval with a clear `ValueError` if any check fails.

#### [MODIFY] [app/api/routes/auth.py](file:///c:/Users/usrav/Downloads/ResolveIQ%20Proj/ResolveIQ%20Proj/app/api/routes/auth.py)
- Clean up unused unauthenticated fallback in `get_current_user` to ensure strict security.
- Verify `require_authenticated_user` dependency is consistently applied to `/me`.

---

### Frontend: AuthPage, Protected Routing & UI Status Messaging

#### [NEW] [frontend_app/src/pages/AuthPage.jsx](file:///c:/Users/usrav/Downloads/ResolveIQ%20Proj/ResolveIQ%20Proj/frontend_app/src/pages/AuthPage.jsx)
- Clean, minimal, full-page ResolveIQ Authentication interface.
- Supports switching between **Sign In** and **Create Account**.
- Collects:
  - **Login**: Email, Password.
  - **Register**: Full Name, Email, Password.
  - Zero Jira fields or Jira configuration clutter.
- Responsive, dark-themed styling aligned with ResolveIQ aesthetics.
- Clear error alerts for invalid credentials, duplicate email, or connection issues.

#### [MODIFY] [frontend_app/src/App.jsx](file:///c:/Users/usrav/Downloads/ResolveIQ%20Proj/ResolveIQ%20Proj/frontend_app/src/App.jsx)
- Implement authenticated session routing:
  - If initial authentication is loading: display a minimal loading indicator.
  - If unauthenticated (`!currentUser`): render `AuthPage` exclusively (redirecting unauthenticated users from the dashboard).
  - Once authenticated: render main layout shell with `Sidebar`, `Header`, and protected pages.

#### [MODIFY] [frontend_app/src/components/layout/Sidebar.jsx](file:///c:/Users/usrav/Downloads/ResolveIQ%20Proj/ResolveIQ%20Proj/frontend_app/src/components/layout/Sidebar.jsx)
- Display current logged-in user name and email prominently in the account footer.
- Add an explicit **Sign Out** button that clears the session token and redirects to `AuthPage`.

#### [MODIFY] [frontend_app/src/hooks/useIncidents.js](file:///c:/Users/usrav/Downloads/ResolveIQ%20Proj/ResolveIQ%20Proj/frontend_app/src/hooks/useIncidents.js)
- Add `authLoading` state so the app doesn't flash the login screen while checking `localStorage` token against `/auth/me`.
- Ensure `logoutUser` removes the token and resets state.

#### [MODIFY] [frontend_app/src/hooks/useIncident.js](file:///c:/Users/usrav/Downloads/ResolveIQ%20Proj/ResolveIQ%20Proj/frontend_app/src/hooks/useIncident.js)
- Standardize banner notification messages per item 8:
  - `AI analysis completed and is ready for human review`
  - `AI analysis completed with insufficient evidence`
  - `AI analysis failed`

#### [MODIFY] [frontend_app/src/pages/IncidentDetails.jsx](file:///c:/Users/usrav/Downloads/ResolveIQ%20Proj/ResolveIQ%20Proj/frontend_app/src/pages/IncidentDetails.jsx)
- Enforce that human approval button is enabled ONLY when:
  - Resolution exists,
  - Resolution `is_grounded === true`,
  - Workflow stage is explicitly `awaiting_approval` / `AWAITING_APPROVAL`.

---

### Automated Tests

#### [NEW] [tests/test_auth.py](file:///c:/Users/usrav/Downloads/ResolveIQ%20Proj/ResolveIQ%20Proj/tests/test_auth.py)
- Complete automated test suite testing:
  1. User registration with Name, Email, Password.
  2. PBKDF2 password hashing verification (with salt, no plaintext).
  3. Duplicate email registration rejection (HTTP 400).
  4. Short password rejection (HTTP 422/400).
  5. Successful login with correct credentials (returns session token & user info).
  6. Login failure with wrong password (HTTP 401).
  7. Login failure with unknown email (HTTP 401).
  8. Authenticated access to `/api/v1/auth/me` with valid Bearer token.
  9. Unauthenticated rejection on `/api/v1/auth/me` (HTTP 401).
  10. Invalid/expired Bearer token rejection on `/api/v1/auth/me` (HTTP 401).
  11. Verification that Jira connection status does not expose secrets.

---

## Verification Plan

### Automated Tests
- Run the full pytest suite including the new `test_auth.py`:
  ```powershell
  pytest
  ```
- Run the workflow and approval tests:
  ```powershell
  pytest tests/test_auth.py tests/test_prompt2_workflow.py tests/test_human_approval.py
  ```

### Manual / Browser Verification
- Build frontend to ensure zero syntax or compilation issues:
  ```powershell
  cd frontend_app
  npm run build
  ```
- Test unauthenticated redirection: Open `http://localhost:5173` without token -> Verify redirect to `AuthPage`.
- Test user registration -> Verify user created, logged in, and dashboard accessed.
- Test sign out -> Verify user logged out and returned to `AuthPage`.
- Test login with created credentials -> Verify successful login and session persistence.

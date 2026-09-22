import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.schemas.approval import ApprovalPackage, HumanApprovalInput, HumanApprovalResult, FinalWorkflowOutput
from app.schemas.agent_results import ClassificationResult, RCAResult, ResolutionResult, RetrievedChunk
from app.schemas.incident import CanonicalIncident
from app.integrations.jira.client import AbstractJiraClient, JiraClient

logger = logging.getLogger("resolveiq.approval")


class ApprovalService:
    """Deliberate Human Approval Gate, Idempotent Jira Writeback & Post-Writeback Verification."""

    def __init__(self, jira_client: Optional[AbstractJiraClient] = None):
        self.jira_client = jira_client or JiraClient()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _format_jira_writeback_comment(
        self,
        package: ApprovalPackage,
        approval_result: HumanApprovalResult
    ) -> str:
        """Formats an official ResolveIQ AI Incident Resolution comment for Jira."""
        lines = [
            "🤖 [ResolveIQ AI Incident Resolution Report]",
            f"Reviewer Status: APPROVED by {approval_result.reviewer or 'Human Operator'}",
            f"Approval Timestamp: {approval_result.timestamp}",
            ""
        ]

        if approval_result.reason:
            lines.append(f"Approval Reason: {approval_result.reason}")

        lines.extend([
            f"Category: {package.classification.category} | Affected Service: {package.classification.service or 'N/A'}",
            "",
            "📌 Identified Root Cause (RCA):",
            f"{package.rca.root_cause or 'No definitive root cause identified.'}",
            "",
            "🛠️ Recommended Recovery Steps:",
            package.resolution.recommendation,
        ])

        for step in package.resolution.steps:
            lines.append(f"- {step}")

        if package.resolution.risks:
            lines.extend(["", "⚠️ Operational Risks:"])
            for risk in package.resolution.risks:
                lines.append(f"- {risk}")

        if package.evidence:
            citations = [c.chunk_id for c in package.evidence]
            lines.extend(["", f"📚 Knowledge Citations: {', '.join(citations)}"])

        return "\n".join(lines)

    def select_intended_transition(
        self,
        available_transitions: List[Dict[str, Any]],
        current_status: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Selects the intended transition from the transitions actually available for this issue.
        Does NOT assume IDs or arbitrary status names.
        
        Business logic:
        1. If issue is already in a 'Resolved' / 'Done' state, return already_at_target.
        2. Prefer transitions targeting 'Done' / 'Resolved' / 'Closed'.
        3. If no 'Done' transition is available from current state, look for progression transition ('In Progress').
        4. If no appropriate transition exists, return None (do not pick an arbitrary transition).
        """
        cur = (current_status or "").strip().lower()
        if cur in ("resolved", "done", "closed", "completed"):
            return {
                "already_at_target": True,
                "target_status": current_status,
                "name": "Already Resolved"
            }

        # 1. Search for Done / Resolved transition
        done_candidates = []
        for t in available_transitions:
            to_obj = t.get("to") or {}
            to_name = (to_obj.get("name") or "").strip().lower()
            category_key = (to_obj.get("statusCategory", {}).get("key") or "").strip().lower()
            trans_name = (t.get("name") or "").strip().lower()

            if (
                category_key == "done"
                or to_name in ("resolved", "done", "closed", "completed", "complete")
                or "resolve" in trans_name
                or trans_name in ("done", "mark done", "close", "close issue", "complete")
            ):
                done_candidates.append({
                    "id": t.get("id"),
                    "name": t.get("name"),
                    "to": to_obj,
                    "target_status": to_obj.get("name") or "Resolved",
                    "priority": 1 if to_name in ("resolved", "done") else 2
                })

        if done_candidates:
            done_candidates.sort(key=lambda x: x["priority"])
            return done_candidates[0]

        # 2. Search for In Progress transition if resolution transition is not directly available
        progress_candidates = []
        for t in available_transitions:
            to_obj = t.get("to") or {}
            to_name = (to_obj.get("name") or "").strip().lower()
            category_key = (to_obj.get("statusCategory", {}).get("key") or "").strip().lower()
            trans_name = (t.get("name") or "").strip().lower()

            if (
                category_key == "indeterminate"
                or to_name in ("in progress", "in_progress", "investigating", "work in progress")
                or "progress" in trans_name
                or trans_name in ("start progress", "start work", "investigate")
            ):
                progress_candidates.append({
                    "id": t.get("id"),
                    "name": t.get("name"),
                    "to": to_obj,
                    "target_status": to_obj.get("name") or "In Progress"
                })

        if progress_candidates:
            return progress_candidates[0]

        return None

    async def _execute_jira_writeback_and_verification(
        self,
        incident: CanonicalIncident,
        package: ApprovalPackage,
        approval_result: HumanApprovalResult
    ) -> FinalWorkflowOutput:
        """
        Executes controlled, idempotent Jira writeback (comment + transition)
        followed by verification against the live Jira read API.
        """
        from app.integrations.supabase.client import SupabaseClient
        supabase = SupabaseClient()

        issue_key = incident.issue_key
        meta = dict(incident.metadata or {})
        stages = dict(meta.get("stages") or {})
        jira_meta = dict(meta.get("jira_update") or {})

        # Ensure stages are initialized
        for s in ["awaiting_approval", "jira_update", "verification", "completed"]:
            if s not in stages:
                stages[s] = {"status": "NOT_STARTED"}

        # Idempotency flags
        comment_posted = jira_meta.get("comment_posted", False)
        transition_applied = jira_meta.get("transition_applied", False)

        stages["jira_update"] = {"status": "PROCESSING", "updated_at": self._now_iso()}
        incident.current_stage = "jira_update"
        incident.stage_status = "processing"

        # 1. Post Comment (if not already posted)
        if not comment_posted:
            comment_text = self._format_jira_writeback_comment(package, approval_result)
            try:
                comment_res = await self.jira_client.add_comment_to_issue(
                    issue_key=issue_key,
                    comment=comment_text
                )
                comment_posted = True
                jira_meta["comment_posted"] = True
                jira_meta["comment_id"] = comment_res.get("id") if isinstance(comment_res, dict) else None
                jira_meta["comment_posted_at"] = self._now_iso()
            except Exception as exc:
                logger.error(f"Jira comment writeback failed for '{issue_key}': {exc}")
                stages["jira_update"] = {
                    "status": "FAILED",
                    "error": f"Failed to post comment to Jira: {str(exc)}",
                    "updated_at": self._now_iso()
                }
                stages["verification"] = {"status": "NOT_STARTED"}
                stages["completed"] = {"status": "FAILED"}
                incident.workflow_status = "failed"
                incident.current_stage = "jira_update"
                incident.stage_status = "failed"
                jira_meta["status"] = "failed"
                jira_meta["error"] = str(exc)
                meta["jira_update"] = jira_meta
                meta["stages"] = stages
                incident.metadata = meta
                await supabase.save_incident(incident)

                return FinalWorkflowOutput(
                    approval_package=package,
                    approval_result=approval_result,
                    jira_updated=False,
                    jira_writeback_response={"error": str(exc), "comment_posted": False}
                )
        else:
            logger.info(f"Comment already posted for '{issue_key}'; skipping duplicate comment write.")

        # 2. Inspect and Apply Jira Transition (if not already applied)
        if not transition_applied:
            try:
                available_transitions = await self.jira_client.get_transitions(issue_key)
                selected = self.select_intended_transition(available_transitions, incident.jira_status)
                
                if not selected:
                    trans_descriptions = [
                        f"'{t.get('name')}' -> '{(t.get('to') or {}).get('name')}'"
                        for t in available_transitions
                    ]
                    raise ValueError(
                        f"No appropriate resolution transition found for issue '{issue_key}'. "
                        f"Available transitions: [{', '.join(trans_descriptions)}]"
                    )

                if not selected.get("already_at_target"):
                    trans_id = selected["id"]
                    await self.jira_client.transition_issue(issue_key, trans_id)
                    target_status_name = selected.get("target_status")
                    jira_meta["transition_id"] = trans_id
                    jira_meta["transition_name"] = selected.get("name")
                    jira_meta["target_status"] = target_status_name
                    jira_meta["transition_applied_at"] = self._now_iso()
                else:
                    target_status_name = selected.get("target_status")
                    jira_meta["target_status"] = target_status_name
                    jira_meta["note"] = "Already at target status"

                transition_applied = True
                jira_meta["transition_applied"] = True

            except Exception as exc:
                logger.error(f"Jira transition failed for '{issue_key}': {exc}")
                stages["jira_update"] = {
                    "status": "FAILED",
                    "error": f"Failed to transition Jira issue: {str(exc)}",
                    "updated_at": self._now_iso()
                }
                stages["verification"] = {"status": "NOT_STARTED"}
                stages["completed"] = {"status": "FAILED"}
                incident.workflow_status = "failed"
                incident.current_stage = "jira_update"
                incident.stage_status = "failed"
                jira_meta["status"] = "failed"
                jira_meta["error"] = str(exc)
                meta["jira_update"] = jira_meta
                meta["stages"] = stages
                incident.metadata = meta
                await supabase.save_incident(incident)

                return FinalWorkflowOutput(
                    approval_package=package,
                    approval_result=approval_result,
                    jira_updated=False,
                    jira_writeback_response={
                        "error": str(exc),
                        "comment_posted": comment_posted,
                        "transition_applied": False
                    }
                )
        else:
            logger.info(f"Transition already applied for '{issue_key}'; skipping duplicate transition.")

        # Jira Update stage is now complete
        stages["jira_update"] = {
            "status": "COMPLETED",
            "comment_posted": True,
            "transition_applied": True,
            "updated_at": self._now_iso()
        }
        jira_meta["status"] = "completed"
        jira_meta["message"] = "Resolution comment and transition applied to Jira."
        meta["jira_update"] = jira_meta

        # 3. Post-Writeback Verification (Re-fetch issue from Jira API)
        stages["verification"] = {"status": "PROCESSING", "updated_at": self._now_iso()}
        incident.current_stage = "verification"
        incident.stage_status = "processing"

        try:
            fresh_issue = await self.jira_client.fetch_issue(issue_key)
            if not fresh_issue or not isinstance(fresh_issue, dict):
                raise ValueError(f"Failed to re-fetch issue '{issue_key}' from Jira read API.")

            fields = fresh_issue.get("fields", {})
            actual_jira_status = (
                fields.get("status", {}).get("name")
                if isinstance(fields.get("status"), dict)
                else (str(fields.get("status")) if fields.get("status") else None)
            )
            actual_resolution = (
                fields.get("resolution", {}).get("name")
                if isinstance(fields.get("resolution"), dict)
                else None
            )

            if not actual_jira_status:
                raise ValueError(f"Re-fetched issue '{issue_key}' response is missing status.")

            # Update authoritative Jira status and resolution from actual Jira response
            incident.jira_status = actual_jira_status
            if actual_resolution:
                incident.resolution = actual_resolution

            # Check verification against intended target
            expected_target = jira_meta.get("target_status")
            if expected_target and actual_jira_status.strip().lower() != expected_target.strip().lower():
                # Allow if both represent resolved/done
                resolved_synonyms = ("resolved", "done", "closed", "completed")
                if not (actual_jira_status.strip().lower() in resolved_synonyms and expected_target.strip().lower() in resolved_synonyms):
                    raise ValueError(
                        f"Verification mismatch: expected Jira status '{expected_target}', "
                        f"but Jira reported '{actual_jira_status}'."
                    )

            # Verification succeeded!
            stages["verification"] = {
                "status": "COMPLETED",
                "verified_jira_status": actual_jira_status,
                "verified_resolution": actual_resolution,
                "updated_at": self._now_iso()
            }
            stages["completed"] = {
                "status": "COMPLETED",
                "message": "AI resolution approved, written back to Jira, and verified against Jira source of truth.",
                "updated_at": self._now_iso()
            }
            incident.workflow_status = "completed"
            incident.current_stage = "completed"
            incident.stage_status = "completed"

            jira_meta["verified"] = True
            jira_meta["verified_jira_status"] = actual_jira_status
            jira_meta["verified_resolution"] = actual_resolution
            meta["jira_update"] = jira_meta
            meta["stages"] = stages
            incident.metadata = meta
            await supabase.save_incident(incident)

            return FinalWorkflowOutput(
                approval_package=package,
                approval_result=approval_result,
                jira_updated=True,
                jira_writeback_response={
                    "status": "success",
                    "comment_posted": True,
                    "transition_applied": True,
                    "verified_jira_status": actual_jira_status,
                    "verified_resolution": actual_resolution
                }
            )

        except Exception as exc:
            logger.error(f"Post-writeback verification failed for '{issue_key}': {exc}")
            stages["verification"] = {
                "status": "FAILED",
                "error": f"Verification failed: {str(exc)}",
                "updated_at": self._now_iso()
            }
            stages["completed"] = {
                "status": "FAILED",
                "reason": "Verification failed",
                "updated_at": self._now_iso()
            }
            incident.workflow_status = "failed"
            incident.current_stage = "verification"
            incident.stage_status = "failed"

            jira_meta["verified"] = False
            jira_meta["verification_error"] = str(exc)
            meta["jira_update"] = jira_meta
            meta["stages"] = stages
            incident.metadata = meta
            await supabase.save_incident(incident)

            return FinalWorkflowOutput(
                approval_package=package,
                approval_result=approval_result,
                jira_updated=True,
                jira_writeback_response={
                    "error": f"Verification failed: {str(exc)}",
                    "verification_failed": True
                }
            )

    async def process_approval(
        self,
        package: ApprovalPackage,
        user_input: HumanApprovalInput
    ) -> FinalWorkflowOutput:
        """
        Processes human approval decision:
        - If approved:
            - awaiting_approval is explicitly marked APPROVED (not COMPLETED yet).
            - Triggers controlled, idempotent Jira writeback and post-writeback verification.
            - Only after successful verification is completed marked COMPLETED and workflow_status = "completed".
        - If rejected:
            - awaiting_approval is marked REJECTED.
            - completed is marked REJECTED (terminal state, never COMPLETED).
            - workflow_status = "rejected".
            - Jira writeback is skipped.
        """
        from app.integrations.supabase.client import SupabaseClient
        supabase = SupabaseClient()

        approval_result = HumanApprovalResult(
            status=user_input.status,
            reviewer=user_input.reviewer,
            reason=user_input.reason,
            feedback=user_input.feedback
        )

        incident = package.incident
        meta = dict(incident.metadata or {})
        stages = dict(meta.get("stages") or {})

        # Ensure all 10 stages exist
        all_stage_keys = [
            "jira_ingestion", "normalization", "classification",
            "rag_retrieval", "rca", "resolution",
            "awaiting_approval", "jira_update", "verification", "completed"
        ]
        for s in all_stage_keys:
            if s not in stages:
                stages[s] = {"status": "NOT_STARTED"}

        # Handle Rejection (Must Revise state - DO NOT mark completed, keep incident open)
        if user_input.status in ("rejected", "must_revise"):
            logger.info(f"Human approval REJECTED for issue '{incident.issue_key}'. Status set to 'must_revise'. Incident remains open.")
            stages["awaiting_approval"] = {
                "status": "MUST_REVISE",
                "decision": "rejected",
                "reviewer": user_input.reviewer,
                "reason": user_input.reason,
                "feedback": user_input.feedback,
                "updated_at": self._now_iso()
            }
            stages["jira_update"] = {
                "status": "SKIPPED",
                "message": "Writeback skipped because resolution was rejected and must be revised",
                "updated_at": self._now_iso()
            }
            stages["verification"] = {
                "status": "SKIPPED",
                "message": "Verification skipped because incident requires revision",
                "updated_at": self._now_iso()
            }
            stages["completed"] = {
                "status": "NOT_STARTED",
                "message": "Incident remains open and must be revised.",
                "updated_at": self._now_iso()
            }

            incident.workflow_status = "must_revise"
            incident.current_stage = "must_revise"
            incident.stage_status = "must_revise"
            incident.status = "open"  # Do not close the incident!
            meta["approval"] = approval_result.model_dump(mode="json")
            meta["jira_update"] = {
                "status": "skipped",
                "message": "Workflow paused for revision without Jira closure."
            }
            meta["stages"] = stages
            incident.metadata = meta
            await supabase.save_incident(incident)

            return FinalWorkflowOutput(
                approval_package=package,
                approval_result=approval_result,
                jira_updated=False,
                jira_writeback_response={
                    "status": "must_revise",
                    "message": "Resolution rejected by human reviewer. Incident status set to must_revise and remains open."
                }
            )

        # Handle Approval (Explicit APPROVED state before writeback)
        # Rule 5: Backend is authoritative for approval. Verify grounding before allowing approval.
        awaiting_stage = (stages.get("awaiting_approval", {}).get("status") or "").upper()
        res_stage = (stages.get("resolution", {}).get("status") or "").upper()
        valid_chunk_ids = {c.chunk_id for c in (package.evidence or [])}
        referenced_chunk_ids = [cid for cid in (package.resolution.evidence or []) if cid in valid_chunk_ids]

        # 1. Verify resolution is grounded and of type rag_grounded
        if (
            not package.resolution.is_grounded
            or package.resolution.grounding_type != "rag_grounded"
            or res_stage in ("INSUFFICIENT_EVIDENCE", "BLOCKED")
            or awaiting_stage == "BLOCKED"
        ):
            raise ValueError(
                f"Approval blocked for issue '{incident.issue_key}': Resolution is not grounded in verified knowledge base evidence."
            )

        # 2. Verify stage is specifically AWAITING_APPROVAL
        if awaiting_stage != "AWAITING_APPROVAL":
            raise ValueError(
                f"Approval blocked for issue '{incident.issue_key}': Incident is not currently awaiting approval (stage status: '{awaiting_stage or 'NOT_STARTED'}')."
            )

        # 3. Verify resolution evidence contains valid chunk IDs from retrieved evidence
        if not referenced_chunk_ids:
            raise ValueError(
                f"Approval blocked for issue '{incident.issue_key}': Resolution evidence does not reference valid knowledge base chunk IDs."
            )

        stages["awaiting_approval"] = {
            "status": "APPROVED",
            "reviewer": user_input.reviewer,
            "reason": user_input.reason,
            "feedback": user_input.feedback,
            "updated_at": self._now_iso()
        }
        incident.workflow_status = "approved"
        incident.current_stage = "jira_update"
        incident.stage_status = "processing"
        meta["approval"] = approval_result.model_dump(mode="json")
        meta["stages"] = stages
        incident.metadata = meta
        await supabase.save_incident(incident)

        # Perform Jira writeback and post-writeback verification
        return await self._execute_jira_writeback_and_verification(
            incident=incident,
            package=package,
            approval_result=approval_result
        )

    async def retry_writeback(
        self,
        issue_key: str,
        reviewer: str = "IT Ops Operator"
    ) -> FinalWorkflowOutput:
        """
        Retries Jira writeback and verification for an already-approved incident.
        Reuses the existing approved resolution and workflow state.
        Does NOT rerun Classification, RAG, RCA, or Resolution.
        Safe against duplicate comments or transitions.
        """
        from app.integrations.supabase.client import SupabaseClient
        supabase = SupabaseClient()

        incident = await supabase.get_incident(issue_key)
        if not incident:
            raise ValueError(f"Incident with key '{issue_key}' not found.")

        meta = incident.metadata or {}
        approval_data = meta.get("approval") or {}

        if approval_data.get("status") != "approved":
            raise ValueError(
                f"Cannot retry Jira writeback: incident '{issue_key}' has not been approved "
                f"(current approval status: '{approval_data.get('status')}')."
            )

        res_data = meta.get("resolution")
        if not res_data or not isinstance(res_data, dict):
            raise ValueError(f"Cannot retry Jira writeback: approved resolution data missing for incident '{issue_key}'.")

        # Reconstruct approval package from stored state
        classification_data = meta.get("classification") or {"category": "General", "service": "N/A"}
        rca_data = meta.get("rca") or {"root_cause": "Identified root cause", "status": "identified"}
        evidence_list = meta.get("evidence") or []

        classification = ClassificationResult(**classification_data)
        rca = RCAResult(**rca_data)
        evidence = [RetrievedChunk(**c) for c in evidence_list]
        resolution = ResolutionResult(**res_data)

        package = ApprovalPackage(
            incident=incident,
            classification=classification,
            rca=rca,
            evidence=evidence,
            resolution=resolution,
            risks=resolution.risks
        )

        approval_result = HumanApprovalResult(
            status="approved",
            reviewer=approval_data.get("reviewer") or reviewer,
            reason=approval_data.get("reason"),
            feedback=approval_data.get("feedback"),
            timestamp=approval_data.get("timestamp") or self._now_iso()
        )

        # Execute writeback and verification
        return await self._execute_jira_writeback_and_verification(
            incident=incident,
            package=package,
            approval_result=approval_result
        )


import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';

export function useIncident(issueKey, initialIncidents = []) {
  const [incident, setIncident] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submittingApproval, setSubmittingApproval] = useState(false);
  const [runningPipeline, setRunningPipeline] = useState(false);
  const [retryingWriteback, setRetryingWriteback] = useState(false);
  const [error, setError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);
  const [actionWarning, setActionWarning] = useState(null);

  const fetchDetail = useCallback(async () => {
    if (!issueKey) return;
    setLoading(true);
    setError(null);

    // Try fetching authoritative API state
    const apiRes = await api.getIncident(issueKey);

    if (apiRes.ok && apiRes.data) {
      const canonical = apiRes.data;
      setIncident({
        ...canonical,
        category: canonical.metadata?.classification?.category || canonical.metadata?.category || canonical.category || 'General',
        service: canonical.metadata?.classification?.service || canonical.metadata?.service || canonical.service || 'Unknown',
        current_stage: canonical.metadata?.current_stage || canonical.current_stage || 'normalization',
        stage_status: canonical.metadata?.stage_status || canonical.stage_status || 'completed',
        classification: canonical.metadata?.classification || null,
        rca: canonical.metadata?.rca || null,
        evidence: canonical.metadata?.evidence || [],
        // Keep Jira's resolution name separate from ResolveIQ's structured
        // AI resolution so both can be displayed and submitted correctly.
        jira_resolution: canonical.resolution || null,
        resolution: canonical.metadata?.resolution || null,
        approval: canonical.metadata?.approval || { status: 'pending' },
        jira_update: canonical.metadata?.jira_update || { status: 'pending' },
      });
    } else {
      setError(apiRes.error || `Incident '${issueKey}' not found.`);
    }

    setLoading(false);
  }, [issueKey]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  const runPipeline = async () => {
    if (!incident) return { ok: false, error: 'No incident loaded' };
    setRunningPipeline(true);
    setError(null);
    setActionSuccess(null);
    setActionWarning(null);

    const res = await api.processIncident(issueKey);
    if (res.ok && res.data) {
      const updated = res.data;
      const resMeta = updated.metadata || {};
      const resStages = resMeta.stages || {};
      const resolutionObj = resMeta.resolution || updated.resolution || null;
      const isGrounded = Boolean(resolutionObj?.is_grounded);
      const isInsufficient = (
        updated.workflow_status === 'insufficient_evidence' ||
        resStages.resolution?.status === 'INSUFFICIENT_EVIDENCE' ||
        resStages.rca?.status === 'INSUFFICIENT_EVIDENCE' ||
        !isGrounded
      );

      setIncident(prev => ({
        ...prev,
        ...updated,
        category: resMeta.classification?.category || prev?.category,
        service: resMeta.classification?.service || prev?.service,
        current_stage: resMeta.current_stage || updated.current_stage,
        stage_status: resMeta.stage_status || updated.stage_status,
        classification: resMeta.classification || null,
        rca: resMeta.rca || null,
        evidence: resMeta.evidence || [],
        resolution: resolutionObj,
        approval: resMeta.approval || { status: 'pending' },
        jira_update: resMeta.jira_update || { status: 'pending' },
      }));

      // Standardize banner notification messages per imp3.md item 8
      if (isInsufficient) {
        setActionWarning('AI analysis completed with insufficient evidence');
      } else {
        setActionSuccess('AI analysis completed and is ready for human review');
      }

      setRunningPipeline(false);
      return { ok: true, data: updated };
    } else {
      setError(res.error ? `AI analysis failed: ${res.error}` : 'AI analysis failed');
      setRunningPipeline(false);
      return { ok: false, error: res.error };
    }
  };

  const submitDecision = async (decision, reviewer = 'IT Ops Reviewer', reason = '', feedback = '') => {
    if (!incident) return { ok: false, error: 'No incident loaded' };

    setSubmittingApproval(true);
    setError(null);
    setActionSuccess(null);

    const decisionInput = {
      status: decision, // 'approved' | 'rejected'
      reviewer,
      reason,
      feedback,
    };

    // Construct ApprovalPackage according to backend pydantic schema
    const packageData = {
      incident: {
        id: incident.id || 'inc-canonical-id',
        issue_key: incident.issue_key,
        source: incident.source || 'jira',
        title: incident.title,
        description: incident.description,
        status: incident.status || 'open',
        jira_status: incident.jira_status,
        // CanonicalIncident.resolution is the Jira resolution name, not the
        // AI ResolutionResult object displayed in the UI.  Sending the object
        // here causes FastAPI/Pydantic validation to reject the approval
        // request before it reaches the approval service.
        resolution: typeof incident.jira_resolution === 'string'
          ? incident.jira_resolution
          : (typeof incident.resolution === 'string' ? incident.resolution : null),
        workflow_status: incident.workflow_status || 'awaiting_approval',
        priority: incident.priority,
        severity: incident.severity,
        reporter: incident.reporter,
        assignee: incident.assignee,
        created_at: incident.created_at || new Date().toISOString(),
        updated_at: new Date().toISOString(),
        metadata: incident.metadata || {},
      },
      classification: incident.classification || {
        category: incident.category || 'General',
        service: incident.service || 'System',
      },
      rca: incident.rca || {
        status: 'identified',
        root_cause: 'Root cause identified through evidence analysis.',
        evidence: [],
      },
      evidence: incident.evidence || [],
      resolution: incident.resolution || {
        recommendation: 'Apply resolution steps.',
        steps: ['Execute recovery plan.'],
        risks: ['None identified.'],
        evidence: [],
      },
      risks: incident.resolution?.risks || [],
    };

    // Call real FastAPI endpoint /api/v1/approval/submit
    const res = await api.submitApproval(packageData, decisionInput);

    if (res.ok && res.data) {
      const output = res.data;
      const isApproved = output.approval_result?.status === 'approved';
      const jiraSuccess = output.jira_updated && !output.jira_writeback_response?.error;

      // Re-fetch fresh state from backend to ensure authoritative Jira status is reflected
      await fetchDetail();

      if (isApproved) {
        if (jiraSuccess) {
          setActionSuccess('Resolution approved, written back to Jira Cloud, and verified successfully.');
        } else {
          setError(output.jira_writeback_response?.error || 'Jira writeback or verification encountered an error.');
        }
      } else {
        setActionSuccess('Resolution was rejected. Workflow ended cleanly without updating Jira.');
      }

      setSubmittingApproval(false);
      return { ok: true, output };
    } else {
      setError(res.error || 'Failed to submit approval decision.');
      setSubmittingApproval(false);
      return { ok: false, error: res.error };
    }
  };

  const retryJiraWriteback = async () => {
    if (!incident) return { ok: false, error: 'No incident loaded' };

    setRetryingWriteback(true);
    setError(null);
    setActionSuccess(null);

    const res = await api.retryWriteback(issueKey);

    if (res.ok && res.data) {
      await fetchDetail();
      setActionSuccess('Jira writeback and verification retried successfully.');
      setRetryingWriteback(false);
      return { ok: true, data: res.data };
    } else {
      setError(res.error || 'Retry of Jira writeback failed.');
      setRetryingWriteback(false);
      return { ok: false, error: res.error };
    }
  };

  return {
    incident,
    loading,
    submittingApproval,
    runningPipeline,
    retryingWriteback,
    error,
    actionSuccess,
    actionWarning,
    refresh: fetchDetail,
    runPipeline,
    submitDecision,
    retryJiraWriteback,
  };
}

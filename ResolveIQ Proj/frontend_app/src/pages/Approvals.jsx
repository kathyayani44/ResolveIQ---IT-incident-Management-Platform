import React, { useState } from 'react';
import PageContainer from '../components/layout/PageContainer';
import ApprovalOverview from '../components/approval/ApprovalOverview';
import ApprovalQueue from '../components/approval/ApprovalQueue';
import ApprovalReview from '../components/approval/ApprovalReview';
import StatusBadge from '../components/common/StatusBadge';
import SeverityBadge from '../components/common/SeverityBadge';
import { CheckCircle2, ShieldCheck, ExternalLink } from 'lucide-react';

export function Approvals({ incidents = [], onUpdateIncidentState, onSelectIncident }) {
  const [selectedForReview, setSelectedForReview] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const pendingIncidents = incidents.filter(
    i => (i.current_stage === 'approval' && i.stage_status === 'awaiting_approval') || i.approval?.status === 'pending'
  );

  const approvedIncidents = incidents.filter(
    i => i.approval?.status === 'approved'
  );

  const handleSubmitDecision = async (status, reviewer, reason, feedback) => {
    if (!selectedForReview) return;
    setSubmitting(true);

    const isApproved = status === 'approved';

    // Call API via hook or update state
    onUpdateIncidentState(selectedForReview.issue_key, (prev) => ({
      ...prev,
      current_stage: isApproved ? 'jira_update' : 'approval',
      stage_status: isApproved ? 'completed' : 'rejected',
      approval: {
        status,
        reviewer,
        timestamp: new Date().toISOString(),
        reason,
        feedback,
      },
      jira_update: {
        status: isApproved ? 'completed' : 'skipped',
        updated_at: isApproved ? new Date().toISOString() : null,
        message: isApproved ? 'Successfully updated Jira issue with resolution comments.' : 'Workflow ended.',
      },
    }));

    setSelectedForReview((prev) => prev ? ({
      ...prev,
      current_stage: isApproved ? 'jira_update' : 'approval',
      stage_status: isApproved ? 'completed' : 'rejected',
      approval: {
        status,
        reviewer,
        timestamp: new Date().toISOString(),
        reason,
        feedback,
      },
      jira_update: {
        status: isApproved ? 'completed' : 'skipped',
        updated_at: isApproved ? new Date().toISOString() : null,
        message: isApproved ? 'Successfully updated Jira issue with resolution comments.' : 'Workflow ended.',
      },
    }) : null);

    setSubmitting(false);
  };

  if (selectedForReview) {
    return (
      <div className="page-content">
        <ApprovalReview
          incident={selectedForReview}
          onBack={() => setSelectedForReview(null)}
          onSubmitDecision={handleSubmitDecision}
          submitting={submitting}
        />
      </div>
    );
  }

  return (
    <PageContainer
      title="Human Approval Queue"
      subtitle="Review AI-generated root causes and recommendations before writeback to Jira."
    >
      {/* Approval Status Overview Cards */}
      <ApprovalOverview incidents={incidents} />

      {/* Awaiting Approval Section */}
      <div style={{ marginBottom: '32px' }}>
        <h3 style={{ fontSize: '16px', color: '#ffffff', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>AWAITING HUMAN APPROVAL</span>
          <span style={{ fontSize: '12px', color: '#818cf8', backgroundColor: 'rgba(99,102,241,0.15)', padding: '2px 8px', borderRadius: '4px' }}>
            {pendingIncidents.length} Pending
          </span>
        </h3>

        <ApprovalQueue
          pendingIncidents={pendingIncidents}
          onSelectForReview={(inc) => setSelectedForReview(inc)}
        />
      </div>

      {/* Recently Approved & Jira Sync History */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Approved Recommendations */}
        <div className="panel">
          <div className="panel-header">
            <h3 style={{ fontSize: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CheckCircle2 size={16} color="#34d399" />
              <span>RECENTLY APPROVED</span>
            </h3>
          </div>

          {approvedIncidents.length === 0 ? (
            <div style={{ padding: '16px 0', fontSize: '13px', color: 'var(--text-secondary)' }}>
              No approved resolutions in current session.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {approvedIncidents.map(inc => (
                <div
                  key={inc.issue_key}
                  onClick={() => onSelectIncident(inc.issue_key)}
                  style={{
                    padding: '12px 14px',
                    borderRadius: '6px',
                    backgroundColor: 'var(--bg-dark)',
                    border: '1px solid var(--border-subtle)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span className="code-mono" style={{ fontWeight: '700', color: '#34d399' }}>{inc.issue_key}</span>
                      <span style={{ fontSize: '13px', color: '#ffffff' }}>{inc.title}</span>
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      Approved by {inc.approval?.reviewer || 'Reviewer'} • {new Date(inc.approval?.timestamp || Date.now()).toLocaleTimeString()}
                    </div>
                  </div>
                  <ExternalLink size={14} color="var(--text-muted)" />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Jira Writeback Log */}
        <div className="panel">
          <div className="panel-header">
            <h3 style={{ fontSize: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldCheck size={16} color="#38bdf8" />
              <span>JIRA WRITEBACK UPDATES</span>
            </h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {incidents.filter(i => i.jira_update?.status === 'completed').length === 0 ? (
              <div style={{ padding: '16px 0', fontSize: '13px', color: 'var(--text-secondary)' }}>
                No Jira writeback logs recorded yet.
              </div>
            ) : (
              incidents.filter(i => i.jira_update?.status === 'completed').map(inc => (
                <div
                  key={inc.issue_key}
                  style={{
                    padding: '12px 14px',
                    borderRadius: '6px',
                    backgroundColor: 'rgba(16,185,129,0.08)',
                    border: '1px solid rgba(16,185,129,0.25)',
                    fontSize: '12px'
                  }}
                >
                  <div style={{ fontWeight: '700', color: '#34d399', marginBottom: '2px' }}>
                    ✓ {inc.issue_key} — Synced with Jira REST API
                  </div>
                  <div style={{ color: 'var(--text-secondary)' }}>
                    {inc.jira_update?.message || 'Resolution comment updated.'}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </PageContainer>
  );
}

export default Approvals;

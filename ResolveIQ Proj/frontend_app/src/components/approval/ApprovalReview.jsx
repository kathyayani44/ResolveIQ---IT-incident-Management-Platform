import React, { useState } from 'react';
import SeverityBadge from '../common/SeverityBadge';
import EvidenceWorkspace from '../incident/EvidenceWorkspace';
import RCASection from '../incident/RCASection';
import ProposedResolution from '../incident/ProposedResolution';
import RejectionModal from './RejectionModal';
import { ArrowLeft, CheckCircle2, Clock, ShieldCheck, XCircle } from 'lucide-react';

export function ApprovalReview({ incident, onBack, onSubmitDecision, submitting }) {
  const [showRejectModal, setShowRejectModal] = useState(false);

  if (!incident) return null;

  const isApproved = incident.approval?.status === 'approved';
  const isRejected = incident.approval?.status === 'rejected';
  const jiraStatus = incident.jira_update?.status;

  const handleApprove = () => {
    onSubmitDecision('approved', 'IT Support Lead', 'Verified resolution steps match operational runbook.');
  };

  const handleRejectConfirm = async ({ reason, feedback }) => {
    await onSubmitDecision('rejected', 'IT Support Lead', reason, feedback);
  };

  return (
    <div>
      <button onClick={onBack} className="btn-secondary" style={{ marginBottom: '16px', fontSize: '12px' }}>
        <ArrowLeft size={14} />
        <span>Back to Queue</span>
      </button>

      {/* Review Title Banner */}
      <div className="panel" style={{ marginBottom: '24px', backgroundColor: 'var(--bg-surface)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <span className="code-mono" style={{ fontSize: '20px', fontWeight: '700', color: 'var(--brand-primary)' }}>
            {incident.issue_key}
          </span>
          <SeverityBadge severity={incident.severity} />
          <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Service: {incident.service || 'System'}</span>
        </div>
        <h2 style={{ fontSize: '20px', fontWeight: '700', color: '#ffffff' }}>
          {incident.title}
        </h2>
      </div>

      {/* Two Column Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', alignItems: 'start' }}>
        {/* LEFT COLUMN: Context & Evidence */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Incident Overview */}
          <div className="panel">
            <h4 style={{ marginBottom: '10px' }}>INCIDENT DESCRIPTION</h4>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              {incident.description || 'No detailed description available.'}
            </p>
          </div>

          {/* Classification */}
          <div className="panel">
            <h4 style={{ marginBottom: '10px' }}>CLASSIFICATION SUMMARY</h4>
            <div style={{ display: 'flex', gap: '20px', fontSize: '13px' }}>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Category: </span>
                <span style={{ color: '#ffffff', fontWeight: '600' }}>{incident.classification?.category || 'General'}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Service: </span>
                <span style={{ color: '#ffffff', fontWeight: '600' }}>{incident.classification?.service || 'System'}</span>
              </div>
            </div>
          </div>

          {/* RCA Section */}
          <RCASection rca={incident.rca} />

          {/* Evidence */}
          <EvidenceWorkspace evidence={incident.evidence} />
        </div>

        {/* RIGHT COLUMN: Resolution & Human Decision */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', position: 'sticky', top: '20px' }}>
          <ProposedResolution resolution={incident.resolution} />

          {/* Human Decision Panel */}
          <div className="panel" style={{ border: '2px solid var(--border-medium)' }}>
            <h3 style={{ fontSize: '15px', marginBottom: '16px' }}>HUMAN DECISION CONTROL</h3>

            {!isApproved && !isRejected ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  Approving will automatically apply resolution comments and execute writeback to Jira issue <strong className="code-mono">{incident.issue_key}</strong>.
                </p>

                <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
                  <button
                    onClick={handleApprove}
                    disabled={submitting}
                    className="btn-approve"
                    style={{ flex: 1, justifyContent: 'center' }}
                  >
                    <CheckCircle2 size={16} />
                    <span>{submitting ? 'Submitting...' : '✓ Approve Resolution'}</span>
                  </button>

                  <button
                    onClick={() => setShowRejectModal(true)}
                    disabled={submitting}
                    className="btn-reject"
                    style={{ flex: 1, justifyContent: 'center' }}
                  >
                    <XCircle size={16} />
                    <span>Reject</span>
                  </button>
                </div>
              </div>
            ) : isApproved ? (
              <div>
                <div style={{
                  padding: '14px',
                  borderRadius: '6px',
                  backgroundColor: 'rgba(16, 185, 129, 0.12)',
                  border: '1px solid #10b981',
                  marginBottom: '16px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#34d399', fontWeight: '700', fontSize: '14px', marginBottom: '4px' }}>
                    <CheckCircle2 size={16} />
                    <span>✓ RESOLUTION APPROVED</span>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    Approved by: {incident.approval?.reviewer || 'Reviewer'} • {new Date(incident.approval?.timestamp || Date.now()).toLocaleTimeString()}
                  </div>
                </div>

                {/* Jira Update Live Status */}
                <div style={{
                  padding: '14px',
                  borderRadius: '6px',
                  backgroundColor: jiraStatus === 'completed' ? 'rgba(16,185,129,0.15)' : 'rgba(56,189,248,0.15)',
                  border: `1px solid ${jiraStatus === 'completed' ? '#10b981' : '#38bdf8'}`
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: jiraStatus === 'completed' ? '#34d399' : '#38bdf8', fontWeight: '700', fontSize: '13px' }}>
                    <ShieldCheck size={16} />
                    <span>{jiraStatus === 'completed' ? '✓ JIRA UPDATED SUCCESSFULLY' : '● UPDATING JIRA REST API...'}</span>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    {incident.jira_update?.message || 'Resolution comment written back to Jira.'}
                  </div>
                </div>
              </div>
            ) : (
              <div style={{
                padding: '14px',
                borderRadius: '6px',
                backgroundColor: 'rgba(239, 68, 68, 0.12)',
                border: '1px solid #ef4444'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f87171', fontWeight: '700', fontSize: '14px', marginBottom: '4px' }}>
                  <XCircle size={16} />
                  <span>RECOMMENDATION REJECTED</span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  Reason: {incident.approval?.reason || 'Rejected by reviewer.'}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Rejection Dialog */}
      <RejectionModal
        isOpen={showRejectModal}
        onClose={() => setShowRejectModal(false)}
        onConfirm={handleRejectConfirm}
        issueKey={incident.issue_key}
      />
    </div>
  );
}

export default ApprovalReview;

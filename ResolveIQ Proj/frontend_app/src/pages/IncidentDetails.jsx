import React, { useRef } from 'react';
import { useIncident } from '../hooks/useIncident';
import IncidentHeader from '../components/incident/IncidentHeader';
import CurrentStatusPanel from '../components/incident/CurrentStatusPanel';
import WorkflowTimeline from '../components/incident/WorkflowTimeline';
import EvidenceWorkspace from '../components/incident/EvidenceWorkspace';
import RCASection from '../components/incident/RCASection';
import ProposedResolution from '../components/incident/ProposedResolution';
import RejectionModal from '../components/approval/RejectionModal';
import { CheckCircle2, Clock, ShieldCheck, XCircle, RefreshCw, Sparkles, AlertCircle } from 'lucide-react';

export function IncidentDetails({ issueKey, onBack, initialIncidents = [] }) {
  const {
    incident,
    loading,
    submittingApproval,
    runningPipeline,
    retryingWriteback,
    error,
    actionSuccess,
    actionWarning,
    runPipeline,
    submitDecision,
    retryJiraWriteback,
  } = useIncident(issueKey, initialIncidents);

  const approvalRef = useRef(null);
  const [showRejectModal, setShowRejectModal] = React.useState(false);

  const scrollToApproval = () => {
    approvalRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  if (loading) {
    return (
      <div className="page-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '400px' }}>
        <div style={{ textAlign: 'center', color: 'var(--brand-primary)' }}>
          <div className="pulse-dot" style={{ width: '16px', height: '16px', margin: '0 auto 12px' }} />
          <div>Loading incident telemetry for {issueKey}...</div>
        </div>
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="page-content">
        <button onClick={onBack} className="btn-secondary" style={{ marginBottom: '16px' }}>
          ← Back to incidents
        </button>
        <div className="panel" style={{ color: '#f87171', border: '1px solid #ef4444' }}>
          <h3>Error Loading Incident</h3>
          <p style={{ marginTop: '8px', fontSize: '13px' }}>{error || `Incident '${issueKey}' not found.`}</p>
        </div>
      </div>
    );
  }

  const workflowStatus = (incident.workflow_status || '').toLowerCase();
  const isApproved = incident.approval?.status === 'approved';
  const isRejected = incident.approval?.status === 'rejected' || incident.approval?.status === 'must_revise' || workflowStatus === 'must_revise' || workflowStatus === 'rejected';
  const jiraUpdateStatus = incident.metadata?.stages?.jira_update?.status || incident.jira_update?.status;
  const verificationStatus = incident.metadata?.stages?.verification?.status;
  const isCompleted = workflowStatus === 'completed';
  const isWritebackFailed = jiraUpdateStatus === 'FAILED' || verificationStatus === 'FAILED' || workflowStatus === 'failed';

  const hasResolution = Boolean(incident.resolution?.recommendation || incident.metadata?.resolution?.recommendation);
  const isGrounded = Boolean(
    (incident.resolution?.is_grounded || incident.metadata?.resolution?.is_grounded) &&
    (incident.resolution?.grounding_type === 'rag_grounded' || incident.metadata?.resolution?.grounding_type === 'rag_grounded')
  );
  const awaitingStageStatus = incident.metadata?.stages?.awaiting_approval?.status;
  const isAwaitingApprovalStage = (
    awaitingStageStatus === 'AWAITING_APPROVAL' ||
    incident.current_stage === 'awaiting_approval' ||
    workflowStatus === 'awaiting_approval'
  );
  const isApprovalReady = isGrounded && isAwaitingApprovalStage && hasResolution;

  const handleApprove = () => {
    submitDecision('approved', 'IT Ops Engineer', 'Resolution approved via incident details interface.');
  };

  const handleRejectConfirm = async ({ reason, feedback }) => {
    await submitDecision('rejected', 'IT Ops Engineer', reason, feedback);
  };

  return (
    <div className="page-content">
      {/* Header */}
      <IncidentHeader incident={incident} onBack={onBack} />

      {/* Action Notification Banners */}
      {actionSuccess && (
        <div style={{
          padding: '12px 16px',
          borderRadius: 'var(--radius-sm)',
          backgroundColor: 'rgba(52, 211, 153, 0.15)',
          border: '1px solid rgba(52, 211, 153, 0.4)',
          color: '#34d399',
          fontSize: '13px',
          fontWeight: '600',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <CheckCircle2 size={16} />
          <span>{actionSuccess}</span>
        </div>
      )}

      {actionWarning && (
        <div style={{
          padding: '12px 16px',
          borderRadius: 'var(--radius-sm)',
          backgroundColor: 'rgba(245, 158, 11, 0.15)',
          border: '1px solid rgba(245, 158, 11, 0.4)',
          color: '#fbbf24',
          fontSize: '13px',
          fontWeight: '600',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <AlertCircle size={16} />
          <span>{actionWarning}</span>
        </div>
      )}

      {error && (
        <div style={{
          padding: '12px 16px',
          borderRadius: 'var(--radius-sm)',
          backgroundColor: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          color: '#f87171',
          fontSize: '13px',
          fontWeight: '600',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Prominent Current Status Panel */}
      <CurrentStatusPanel incident={incident} onScrollToApproval={scrollToApproval} />

      {/* Main Grid: Left (Timeline + Information + Classification) | Right (RCA, Evidence, Resolution, Approval) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px', alignItems: 'start' }}>
        {/* LEFT COLUMN */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Workflow Timeline (10 Stages) */}
          <WorkflowTimeline incident={incident} />

          {/* Incident Information Card */}
          <div className="panel">
            <h3 style={{ fontSize: '15px', marginBottom: '14px' }}>INCIDENT INFORMATION</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Title: </span>
                <span style={{ color: 'var(--text-primary)', fontWeight: '600' }}>{incident.title}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Description: </span>
                <p style={{ color: 'var(--text-secondary)', marginTop: '4px', lineHeight: '1.5' }}>
                  {incident.description || 'No description provided.'}
                </p>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Reporter: </span>
                <span style={{ color: 'var(--text-primary)' }}>{incident.reporter || 'System Ingestion'}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Assignee: </span>
                <span style={{ color: 'var(--text-primary)' }}>{incident.assignee || 'Unassigned'}</span>
              </div>
            </div>
          </div>

          {/* Classification */}
          <div className="panel">
            <h3 style={{ fontSize: '15px', marginBottom: '12px' }}>CLASSIFICATION</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '13px' }}>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Identified Category: </span>
                <span style={{ color: '#ffffff', fontWeight: '600' }}>{incident.classification?.category || incident.category || 'General'}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Affected Service: </span>
                <span style={{ color: '#ffffff', fontWeight: '600' }}>{incident.classification?.service || incident.service || 'System'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* If AI pipeline has not been executed yet */}
          {!hasResolution && !isApproved && !isRejected && (
            <div className="panel" style={{ border: '2px dashed var(--border-medium)', textAlign: 'center', padding: '32px 20px' }}>
              <Sparkles size={32} color="var(--brand-primary)" style={{ margin: '0 auto 12px' }} />
              <h3 style={{ fontSize: '16px', marginBottom: '8px' }}>AI Incident Resolution Pipeline</h3>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', maxWidth: '500px', margin: '0 auto 20px' }}>
                Run the multi-agent AI pipeline to automatically classify this incident, retrieve knowledge base runbooks, perform Root Cause Analysis (RCA), and draft actionable recovery steps.
              </p>
              <button
                onClick={runPipeline}
                disabled={runningPipeline}
                className="btn-primary"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '10px 24px', fontSize: '14px' }}
              >
                {runningPipeline ? (
                  <>
                    <RefreshCw size={16} className="spin" />
                    <span>Running AI Agents (Classification → RAG → RCA → Resolution)...</span>
                  </>
                ) : (
                  <>
                    <Sparkles size={16} />
                    <span>Run AI Resolution Pipeline</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Root Cause Analysis */}
          <RCASection rca={incident.rca} />

          {/* Evidence Workspace */}
          <EvidenceWorkspace evidence={incident.evidence} />

          {/* Proposed Resolution */}
          <ProposedResolution resolution={incident.resolution} />

          {/* Human Approval Section */}
          <div ref={approvalRef} className="panel" style={{ border: '2px solid var(--border-medium)' }}>
            <h3 style={{ fontSize: '16px', marginBottom: '14px' }}>HUMAN APPROVAL GATE & JIRA WRITEBACK</h3>

            {!isApproved && !isRejected ? (
              <div>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
                  Review the proposed AI resolution above. Approval is a deliberate human gate. Upon approval, ResolveIQ will inspect available Jira transitions, apply the resolution comment and transition, and verify the result against Jira Cloud.
                </p>
                <div style={{ display: 'flex', gap: '14px' }}>
                  <button
                    onClick={handleApprove}
                    disabled={submittingApproval || !isApprovalReady}
                    className="btn-approve"
                    style={{
                      flex: 1,
                      justifyContent: 'center',
                      opacity: isApprovalReady ? 1 : 0.5,
                      cursor: isApprovalReady ? 'pointer' : 'not-allowed'
                    }}
                  >
                    <CheckCircle2 size={16} />
                    <span>{submittingApproval ? 'Executing Writeback & Verifying...' : '✓ Approve Recommendation'}</span>
                  </button>

                  <button
                    onClick={() => setShowRejectModal(true)}
                    disabled={submittingApproval}
                    className="btn-reject"
                    style={{ flex: 1, justifyContent: 'center' }}
                  >
                    <XCircle size={16} />
                    <span>Reject</span>
                  </button>
                </div>
                {!hasResolution ? (
                  <div style={{ fontSize: '12px', color: '#fbbf24', marginTop: '10px' }}>
                    ⚠️ Note: Run the AI Resolution Pipeline above before submitting an approval decision.
                  </div>
                ) : !isGrounded ? (
                  <div style={{
                    fontSize: '12px',
                    color: '#fbbf24',
                    marginTop: '12px',
                    backgroundColor: 'rgba(245, 158, 11, 0.08)',
                    border: '1px solid rgba(245, 158, 11, 0.25)',
                    borderRadius: '6px',
                    padding: '8px 12px'
                  }}>
                    🚫 <strong>Approval Blocked:</strong> The proposed resolution is not grounded in verified knowledge base runbooks. Human approval is disabled to prevent ungrounded operational changes.
                  </div>
                ) : !isAwaitingApprovalStage ? (
                  <div style={{ fontSize: '12px', color: '#fbbf24', marginTop: '10px' }}>
                    ⚠️ Note: Incident is currently in '{incident.current_stage}' stage. Approval is enabled only when awaiting approval.
                  </div>
                ) : null}
              </div>
            ) : isApproved ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {/* 1. Explicit Approval State */}
                <div style={{
                  padding: '14px',
                  borderRadius: '6px',
                  backgroundColor: 'rgba(16, 185, 129, 0.12)',
                  border: '1px solid #10b981'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#34d399', fontWeight: '700', fontSize: '14px' }}>
                    <CheckCircle2 size={16} />
                    <span>✓ RESOLUTION APPROVED</span>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    Reviewer: {incident.approval?.reviewer || 'IT Ops'} • {new Date(incident.approval?.timestamp || Date.now()).toLocaleTimeString()}
                  </div>
                </div>

                {/* 2. Jira Writeback & Verification Status */}
                {isCompleted ? (
                  <div style={{
                    padding: '14px',
                    borderRadius: '6px',
                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                    border: '1px solid #10b981'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#34d399', fontWeight: '700', fontSize: '13px' }}>
                      <ShieldCheck size={16} />
                      <span>✓ JIRA UPDATED & VERIFIED</span>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-primary)', marginTop: '4px' }}>
                      Jira Cloud issue status verified as: <strong>{incident.jira_status}</strong>
                    </div>
                    {incident.jira_resolution && (
                      <div style={{ fontSize: '12px', color: 'var(--text-primary)', marginTop: '2px' }}>
                        Jira resolution verified as: <strong>{incident.jira_resolution}</strong>
                      </div>
                    )}
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      Resolution comment and status transition written back and confirmed via Jira REST API.
                    </div>
                  </div>
                ) : isWritebackFailed ? (
                  <div style={{
                    padding: '14px',
                    borderRadius: '6px',
                    backgroundColor: 'rgba(239, 68, 68, 0.12)',
                    border: '1px solid #ef4444'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f87171', fontWeight: '700', fontSize: '13px' }}>
                      <AlertCircle size={16} />
                      <span>✕ JIRA WRITEBACK OR VERIFICATION FAILED</span>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                      {incident.metadata?.stages?.jira_update?.error || incident.metadata?.stages?.verification?.error || 'Writeback failed to complete.'}
                    </div>
                    <div style={{ marginTop: '12px' }}>
                      <button
                        onClick={retryJiraWriteback}
                        disabled={retryingWriteback}
                        className="btn-primary"
                        style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '6px 14px', fontSize: '12px' }}
                      >
                        <RefreshCw size={14} className={retryingWriteback ? 'spin' : ''} />
                        <span>{retryingWriteback ? 'Retrying Writeback...' : '🔄 Retry Jira Writeback'}</span>
                      </button>
                    </div>
                  </div>
                ) : (
                  <div style={{
                    padding: '14px',
                    borderRadius: '6px',
                    backgroundColor: 'rgba(56, 189, 248, 0.15)',
                    border: '1px solid #38bdf8'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#38bdf8', fontWeight: '700', fontSize: '13px' }}>
                      <Clock size={16} className="spin" />
                      <span>● UPDATING JIRA REST API & VERIFYING...</span>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                      Posting comment, applying transition, and re-fetching issue from Jira Cloud...
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{
                padding: '16px',
                borderRadius: '6px',
                backgroundColor: 'rgba(245, 158, 11, 0.12)',
                border: '1px solid #f59e0b'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fbbf24', fontWeight: '700', fontSize: '14px' }}>
                  <AlertCircle size={16} />
                  <span>RECOMMENDATION REJECTED — MUST REVISE</span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '8px' }}>
                  <strong>Reviewer:</strong> {incident.approval?.reviewer || 'Human Operator'}
                  {incident.approval?.reason && <span> • <strong>Reason:</strong> {incident.approval.reason}</span>}
                </div>
                {incident.approval?.feedback && (
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    <strong>Operator Feedback:</strong> {incident.approval.feedback}
                  </div>
                )}
                <div style={{ fontSize: '12px', color: '#fbbf24', marginTop: '8px', lineHeight: '1.4' }}>
                  ⚠️ The incident was NOT closed and remains <strong>OPEN</strong>. It requires revision before a resolution can be approved and written back to Jira.
                </div>
                <div style={{ marginTop: '14px' }}>
                  <button
                    onClick={runPipeline}
                    disabled={runningPipeline}
                    className="btn-primary"
                    style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '8px 16px', fontSize: '13px' }}
                  >
                    <RefreshCw size={14} className={runningPipeline ? 'spin' : ''} />
                    <span>{runningPipeline ? 'Re-analyzing Incident...' : '🔄 Re-run AI Pipeline & Revise'}</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <RejectionModal
        isOpen={showRejectModal}
        onClose={() => setShowRejectModal(false)}
        onConfirm={handleRejectConfirm}
        issueKey={incident.issue_key}
      />
    </div>
  );
}

export default IncidentDetails;

import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle2, Clock, XCircle, ShieldCheck, Tag } from 'lucide-react';
import JiraStatusBadge from '../common/JiraStatusBadge';

export function CurrentStatusPanel({ incident, onScrollToApproval }) {
  if (!incident) return null;

  const workflowStatus = (incident.workflow_status || '').toLowerCase();
  const currentStage = (incident.current_stage || '').toLowerCase();
  const stageStatus = (incident.stage_status || '').toLowerCase();
  const resStageStatus = (incident.metadata?.stages?.resolution?.status || '').toLowerCase();
  const isGrounded = Boolean(incident.resolution?.is_grounded || incident.metadata?.resolution?.is_grounded);

  const isWorkflowCompleted = workflowStatus === 'completed';
  const isMustRevise = workflowStatus === 'must_revise' || currentStage === 'must_revise' || stageStatus === 'must_revise' || workflowStatus === 'rejected' || incident.approval?.status === 'rejected' || incident.approval?.status === 'must_revise';
  const isFailed = workflowStatus === 'failed' || stageStatus === 'failed';
  const isInsufficientEvidence = workflowStatus === 'insufficient_evidence' || stageStatus === 'insufficient_evidence' || resStageStatus === 'insufficient_evidence' || (!isGrounded && incident.resolution && workflowStatus !== 'unprocessed');
  const isApprovalPending = (workflowStatus === 'awaiting_approval' || stageStatus === 'awaiting_approval') && !isInsufficientEvidence && isGrounded;
  const isApprovedProcessing = workflowStatus === 'approved' || currentStage === 'jira_update' || currentStage === 'verification';

  let statusColor = '#fbbf24';
  let StatusIcon = Clock;
  let statusTitle = 'Internal AI Workflow';
  let statusMessage = 'Incident ingested. AI agents ready to analyze root cause.';

  if (isWorkflowCompleted) {
    statusColor = '#34d399';
    StatusIcon = CheckCircle2;
    statusMessage = 'Resolution approved, written back to Jira Cloud, and verified against Jira source of truth.';
  } else if (isMustRevise) {
    statusColor = '#f59e0b';
    StatusIcon = AlertCircle;
    statusTitle = 'Must Revise';
    const reviewer = incident.approval?.reviewer || 'human operator';
    const reason = incident.approval?.reason ? ` (${incident.approval.reason})` : '';
    statusMessage = `Resolution recommendation was rejected by ${reviewer}${reason}. Incident remains open and must be revised before re-submitting for approval.`;
  } else if (isFailed) {
    statusColor = '#f87171';
    StatusIcon = AlertCircle;
    statusMessage = 'A workflow stage encountered a failure. Review details and retry writeback if applicable.';
  } else if (isInsufficientEvidence) {
    statusColor = '#f59e0b';
    StatusIcon = AlertTriangle;
    statusTitle = 'Resolution Blocked';
    statusMessage = 'Insufficient runbook evidence in knowledge base. Resolution is blocked to prevent ungrounded actions.';
  } else if (isApprovedProcessing) {
    statusColor = '#818cf8';
    StatusIcon = ShieldCheck;
    statusMessage = 'Resolution approved. Writing back to Jira Cloud and verifying source of truth...';
  } else if (isApprovalPending) {
    statusColor = '#818cf8';
    StatusIcon = Clock;
    statusMessage = 'Root cause identified and RAG-grounded resolution drafted. Awaiting human operator approval.';
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '24px' }}>
      {/* 1. Authoritative Jira Status Banner */}
      <div style={{
        padding: '16px 20px',
        borderRadius: 'var(--radius-md)',
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-medium)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        gap: '8px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', fontWeight: '700', color: 'var(--brand-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            <Tag size={15} />
            <span>Jira Source of Truth</span>
          </div>
          <JiraStatusBadge status={incident.jira_status} />
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px', margin: 0 }}>
          Live external status from Jira Cloud REST API. The external Jira issue status remains authoritative.
        </p>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          {incident.resolution ? `Resolution: ${incident.resolution}` : 'No Jira resolution set'}
        </div>
      </div>

      {/* 2. ResolveIQ AI Workflow Status Banner */}
      <div style={{
        padding: '16px 20px',
        borderRadius: 'var(--radius-md)',
        backgroundColor: `${statusColor}18`,
        border: `1px solid ${statusColor}55`,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        gap: '8px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', fontWeight: '700', color: statusColor, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            <StatusIcon size={15} />
            <span>{statusTitle}</span>
          </div>
          <span style={{
            fontSize: '11px',
            fontWeight: '700',
            padding: '2px 8px',
            borderRadius: '4px',
            backgroundColor: `${statusColor}25`,
            color: statusColor,
            textTransform: 'uppercase'
          }}>
            {workflowStatus || currentStage || 'Unprocessed'}
          </span>
        </div>

        <p style={{ color: 'var(--text-primary)', fontSize: '13px', margin: 0 }}>
          {statusMessage}
        </p>

        {isApprovalPending && onScrollToApproval && (
          <button
            onClick={onScrollToApproval}
            className="btn-approve"
            style={{ alignSelf: 'flex-start', padding: '4px 12px', fontSize: '12px' }}
          >
            Review Recommendation →
          </button>
        )}
      </div>
    </div>
  );
}

export default CurrentStatusPanel;


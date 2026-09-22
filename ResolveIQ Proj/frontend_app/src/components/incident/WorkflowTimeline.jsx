import React from 'react';
import { CheckCircle2, Clock, Circle, XCircle, AlertTriangle, ShieldCheck } from 'lucide-react';

export function WorkflowTimeline({ incident }) {
  if (!incident) return null;

  const stages = incident.metadata?.stages || {};

  const stepDefs = [
    { key: 'jira_ingestion', label: '1. Jira Ingestion', defaultDesc: 'Fetched from Jira Cloud API' },
    { key: 'normalization', label: '2. Normalization', defaultDesc: 'CanonicalIncident schema created' },
    { key: 'classification', label: '3. Classification', defaultDesc: incident.classification?.category ? `Category: ${incident.classification.category}` : 'Incident category determined' },
    { key: 'rag_retrieval', label: '4. RAG Retrieval', defaultDesc: incident.evidence?.length ? `${incident.evidence.length} runbook evidence chunks` : 'Runbook retrieval complete' },
    { key: 'rca', label: '5. Root Cause Analysis', defaultDesc: incident.rca?.root_cause ? 'Root cause identified' : 'Likely root cause analysis' },
    { key: 'resolution', label: '6. Resolution', defaultDesc: incident.resolution?.recommendation ? 'Recovery steps generated' : 'Resolution proposal drafted' },
    { key: 'awaiting_approval', label: '7. Human Approval Gate', defaultDesc: 'Deliberate human review & decision' },
    { key: 'jira_update', label: '8. Jira Writeback', defaultDesc: 'Comment & dynamic transition applied' },
    { key: 'verification', label: '9. Jira Verification', defaultDesc: 'Re-fetch & source of truth check' },
    { key: 'completed', label: '10. Completed', defaultDesc: 'Workflow finished & verified' },
  ];

  // Helper to determine status for a stage
  const getStageInfo = (stepKey) => {
    const stageObj = stages[stepKey] || {};
    let status = (stageObj.status || '').toUpperCase();

    // Fallbacks if stages dict not populated
    if (!status) {
      if (stepKey === 'jira_ingestion' || stepKey === 'normalization') {
        status = 'COMPLETED';
      } else if (stepKey === 'awaiting_approval') {
        const appStatus = (incident.approval?.status || '').toLowerCase();
        if (appStatus === 'approved') status = 'APPROVED';
        else if (appStatus === 'rejected' || appStatus === 'must_revise') status = 'MUST_REVISE';
        else if (incident.workflow_status === 'awaiting_approval') status = 'AWAITING_APPROVAL';
        else status = 'NOT_STARTED';
      } else if (stepKey === 'jira_update') {
        const jStatus = (incident.jira_update?.status || '').toLowerCase();
        if (jStatus === 'completed') status = 'COMPLETED';
        else if (jStatus === 'failed') status = 'FAILED';
        else if (jStatus === 'skipped') status = 'SKIPPED';
        else status = 'NOT_STARTED';
      } else if (stepKey === 'completed') {
        if (incident.workflow_status === 'completed') status = 'COMPLETED';
        else if (incident.workflow_status === 'must_revise' || incident.workflow_status === 'rejected') status = 'NOT_STARTED';
        else if (incident.workflow_status === 'failed') status = 'FAILED';
        else status = 'NOT_STARTED';
      } else {
        status = 'NOT_STARTED';
      }
    }

    return {
      status,
      desc: stageObj.message || stageObj.reason || stageObj.error || stageDefsMap[stepKey]?.defaultDesc,
    };
  };

  const stageDefsMap = Object.fromEntries(stepDefs.map(s => [s.key, s]));

  const getStatusBadge = (status) => {
    switch (status) {
      case 'COMPLETED':
        return { text: 'COMPLETED', bg: 'rgba(52, 211, 153, 0.15)', color: '#34d399', border: 'rgba(52, 211, 153, 0.3)' };
      case 'APPROVED':
        return { text: 'APPROVED', bg: 'rgba(16, 185, 129, 0.2)', color: '#10b981', border: 'rgba(16, 185, 129, 0.4)' };
      case 'AWAITING_APPROVAL':
        return { text: 'AWAITING APPROVAL', bg: 'rgba(129, 140, 248, 0.2)', color: '#818cf8', border: 'rgba(129, 140, 248, 0.4)' };
      case 'MUST_REVISE':
        return { text: 'MUST REVISE', bg: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24', border: 'rgba(245, 158, 11, 0.4)' };
      case 'PROCESSING':
        return { text: 'PROCESSING', bg: 'rgba(147, 51, 234, 0.18)', color: '#c084fc', border: 'rgba(147, 51, 234, 0.4)' };
      case 'FAILED':
        return { text: 'FAILED', bg: 'rgba(239, 68, 68, 0.18)', color: '#f87171', border: 'rgba(239, 68, 68, 0.4)' };
      case 'BLOCKED':
        return { text: 'BLOCKED', bg: 'rgba(245, 158, 11, 0.18)', color: '#fbbf24', border: 'rgba(245, 158, 11, 0.4)' };
      case 'INSUFFICIENT_EVIDENCE':
        return { text: 'INSUFFICIENT EVIDENCE', bg: 'rgba(245, 158, 11, 0.22)', color: '#fbbf24', border: 'rgba(245, 158, 11, 0.45)' };
      case 'REJECTED':
        return { text: 'MUST REVISE', bg: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24', border: 'rgba(245, 158, 11, 0.4)' };
      case 'SKIPPED':
        return { text: 'SKIPPED', bg: 'rgba(100, 116, 139, 0.18)', color: '#94a3b8', border: 'rgba(100, 116, 139, 0.3)' };
      default:
        return { text: 'NOT STARTED', bg: 'rgba(255, 255, 255, 0.05)', color: 'var(--text-muted)', border: 'var(--border-subtle)' };
    }
  };

  return (
    <div className="panel" style={{ marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ fontSize: '14px', letterSpacing: '0.05em', margin: 0 }}>WORKFLOW EXECUTION TIMELINE (10 STAGES)</h3>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>ResolveIQ Pipeline</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0px' }}>
        {stepDefs.map((step, idx) => {
          const { status, desc } = getStageInfo(step.key);
          const badge = getStatusBadge(status);
          const isLast = idx === stepDefs.length - 1;

          let Icon = Circle;
          let iconColor = 'var(--text-muted)';

          if (status === 'COMPLETED' || status === 'APPROVED') {
            Icon = CheckCircle2;
            iconColor = '#34d399';
          } else if (status === 'PROCESSING' || status === 'AWAITING_APPROVAL') {
            Icon = Clock;
            iconColor = '#818cf8';
          } else if (status === 'FAILED' || status === 'REJECTED') {
            Icon = XCircle;
            iconColor = '#f87171';
          } else if (status === 'BLOCKED' || status === 'INSUFFICIENT_EVIDENCE') {
            Icon = AlertTriangle;
            iconColor = '#fbbf24';
          }

          return (
            <div key={step.key} style={{ display: 'flex', gap: '14px' }}>
              {/* Connector line column */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <Icon size={18} color={iconColor} style={{ marginTop: '2px', flexShrink: 0 }} />
                {!isLast && (
                  <div style={{
                    width: '2px',
                    height: '36px',
                    backgroundColor: (status === 'COMPLETED' || status === 'APPROVED')
                      ? 'rgba(52, 211, 153, 0.4)'
                      : 'var(--border-subtle)',
                    margin: '3px 0'
                  }} />
                )}
              </div>

              {/* Content column */}
              <div style={{ paddingBottom: isLast ? '0' : '14px', flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
                  <span style={{
                    fontSize: '13px',
                    fontWeight: '600',
                    color: status === 'NOT_STARTED' ? 'var(--text-muted)' : 'var(--text-primary)'
                  }}>
                    {step.label}
                  </span>
                  <span style={{
                    fontSize: '10px',
                    fontWeight: '700',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    backgroundColor: badge.bg,
                    color: badge.color,
                    border: `1px solid ${badge.border}`,
                    letterSpacing: '0.04em'
                  }}>
                    {badge.text}
                  </span>
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  {desc}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default WorkflowTimeline;


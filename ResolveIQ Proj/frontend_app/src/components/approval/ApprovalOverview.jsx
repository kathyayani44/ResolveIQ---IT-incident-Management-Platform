import React from 'react';
import { Clock, CheckCircle2, ShieldCheck, XCircle } from 'lucide-react';

export function ApprovalOverview({ incidents = [] }) {
  const pendingCount = incidents.filter(i => (i.current_stage === 'approval' && i.stage_status === 'awaiting_approval') || i.approval?.status === 'pending').length;
  const approvedCount = incidents.filter(i => i.approval?.status === 'approved').length;
  const jiraUpdatedCount = incidents.filter(i => i.jira_update?.status === 'completed' || i.current_stage === 'jira_update').length;
  const rejectedCount = incidents.filter(i => i.approval?.status === 'rejected' || i.stage_status === 'rejected').length;

  return (
    <div className="panel" style={{ marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div>
          <h3 style={{ fontSize: '16px' }}>HUMAN APPROVAL DECISION CENTER</h3>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Review AI-generated resolutions before execution and automatic writeback to Jira</p>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '12px'
      }}>
        <div style={{ padding: '14px', borderRadius: '8px', backgroundColor: 'rgba(99,102,241,0.12)', border: '1px solid #6366f1' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#818cf8', fontWeight: '600' }}>
            <Clock size={14} />
            <span>AWAITING REVIEW</span>
          </div>
          <div style={{ fontSize: '24px', fontWeight: '700', color: '#ffffff', marginTop: '4px' }}>
            {pendingCount}
          </div>
        </div>

        <div style={{ padding: '14px', borderRadius: '8px', backgroundColor: 'rgba(16,185,129,0.12)', border: '1px solid #10b981' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#34d399', fontWeight: '600' }}>
            <CheckCircle2 size={14} />
            <span>RESOLUTIONS APPROVED</span>
          </div>
          <div style={{ fontSize: '24px', fontWeight: '700', color: '#ffffff', marginTop: '4px' }}>
            {approvedCount}
          </div>
        </div>

        <div style={{ padding: '14px', borderRadius: '8px', backgroundColor: 'rgba(56,189,248,0.12)', border: '1px solid #38bdf8' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#38bdf8', fontWeight: '600' }}>
            <ShieldCheck size={14} />
            <span>JIRA UPDATES SYNCED</span>
          </div>
          <div style={{ fontSize: '24px', fontWeight: '700', color: '#ffffff', marginTop: '4px' }}>
            {jiraUpdatedCount}
          </div>
        </div>

        <div style={{ padding: '14px', borderRadius: '8px', backgroundColor: 'rgba(239,68,68,0.12)', border: '1px solid #ef4444' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#f87171', fontWeight: '600' }}>
            <XCircle size={14} />
            <span>REJECTED WORKFLOWS</span>
          </div>
          <div style={{ fontSize: '24px', fontWeight: '700', color: '#ffffff', marginTop: '4px' }}>
            {rejectedCount}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ApprovalOverview;

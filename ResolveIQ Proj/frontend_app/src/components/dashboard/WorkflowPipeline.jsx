import React from 'react';
import { ArrowRight, CheckCircle2 } from 'lucide-react';

export function WorkflowPipeline({ incidents = [] }) {
  // Count incidents by current stage
  const stages = [
    { id: 'retrieved', label: 'Retrieved' },
    { id: 'classify', label: 'Classification' },
    { id: 'rag', label: 'RAG Knowledge' },
    { id: 'rca', label: 'RCA Analysis' },
    { id: 'resolution', label: 'Resolution' },
    { id: 'approval', label: 'Human Approval' },
    { id: 'jira_update', label: 'Jira Writeback' },
  ];

  const counts = stages.reduce((acc, stage) => {
    acc[stage.id] = incidents.filter(i => (i.current_stage || '').toLowerCase() === stage.id).length;
    return acc;
  }, {});

  return (
    <div className="panel" style={{ marginBottom: '24px' }}>
      <div className="panel-header">
        <div>
          <h3 style={{ fontSize: '15px' }}>RESOLVEIQ WORKFLOW PIPELINE</h3>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Multi-agent execution pipeline stage distribution</p>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
        gap: '12px',
        alignItems: 'center',
        paddingTop: '8px'
      }}>
        {stages.map((stage, idx) => {
          const isJira = stage.id === 'jira_update';
          const isApproval = stage.id === 'approval';
          const count = counts[stage.id] || 0;

          return (
            <React.Fragment key={stage.id}>
              <div style={{
                backgroundColor: isApproval ? 'rgba(99,102,241,0.1)' : isJira ? 'rgba(16,185,129,0.1)' : 'var(--bg-surface-elevated)',
                border: `1px solid ${isApproval ? '#6366f1' : isJira ? '#10b981' : 'var(--border-subtle)'}`,
                borderRadius: '8px',
                padding: '12px',
                textAlign: 'center',
                position: 'relative'
              }}>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '6px' }}>
                  {stage.label}
                </div>
                <div style={{ fontSize: '20px', fontWeight: '700', color: isApproval ? '#818cf8' : isJira ? '#34d399' : '#ffffff' }}>
                  {count}
                </div>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  {count === 1 ? '1 incident' : `${count} incidents`}
                </div>
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}

export default WorkflowPipeline;

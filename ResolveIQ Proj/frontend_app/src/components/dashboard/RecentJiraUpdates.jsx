import React from 'react';
import { CheckCircle2, ArrowRight } from 'lucide-react';

export function RecentJiraUpdates({ incidents = [], onSelectIncident }) {
  const jiraUpdatedList = incidents.filter(
    i => i.jira_update?.status === 'completed' || i.current_stage === 'jira_update'
  );

  return (
    <div className="panel" style={{ border: '1px solid rgba(16, 185, 129, 0.3)' }}>
      <div className="panel-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle2 size={18} color="#34d399" />
          <h3 style={{ fontSize: '15px' }}>RECENTLY UPDATED IN JIRA</h3>
        </div>
        <span style={{ fontSize: '12px', color: '#34d399', fontWeight: '600' }}>
          Jira Writeback MVP Active
        </span>
      </div>

      {jiraUpdatedList.length === 0 ? (
        <div style={{ padding: '12px 0', color: 'var(--text-secondary)', fontSize: '13px' }}>
          No Jira issue writebacks executed yet in current session. Approved resolutions write back comments automatically.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {jiraUpdatedList.map(inc => (
            <div
              key={inc.issue_key}
              onClick={() => onSelectIncident(inc.issue_key)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                borderRadius: '6px',
                backgroundColor: 'rgba(16, 185, 129, 0.06)',
                border: '1px solid rgba(16, 185, 129, 0.2)',
                cursor: 'pointer'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <CheckCircle2 size={16} color="#10b981" />
                <span className="code-mono" style={{ fontWeight: '700', color: '#34d399' }}>{inc.issue_key}</span>
                <span style={{ color: 'var(--text-primary)', fontSize: '13px' }}>{inc.title}</span>
              </div>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                {inc.jira_update?.updated_at ? new Date(inc.jira_update.updated_at).toLocaleTimeString() : 'Just now'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default RecentJiraUpdates;

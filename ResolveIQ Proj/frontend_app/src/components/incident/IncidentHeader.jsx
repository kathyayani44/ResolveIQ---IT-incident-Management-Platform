import React from 'react';
import { ArrowLeft, Clock, User, Tag } from 'lucide-react';
import SeverityBadge from '../common/SeverityBadge';
import StatusBadge from '../common/StatusBadge';
import JiraStatusBadge from '../common/JiraStatusBadge';

export function IncidentHeader({ incident, onBack }) {
  if (!incident) return null;

  return (
    <div style={{ marginBottom: '24px' }}>
      <button
        onClick={onBack}
        className="btn-secondary"
        style={{ marginBottom: '16px', fontSize: '12px' }}
      >
        <ArrowLeft size={14} />
        <span>Back to incidents</span>
      </button>

      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px', flexWrap: 'wrap' }}>
            <span className="code-mono" style={{ fontSize: '20px', fontWeight: '700', color: 'var(--brand-primary)' }}>
              {incident.issue_key}
            </span>
            <SeverityBadge severity={incident.severity} />
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Jira:</span>
              <JiraStatusBadge status={incident.jira_status} />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>AI Stage:</span>
              <StatusBadge status={incident.stage_status} stage={incident.current_stage} />
            </div>
          </div>
          <h1 style={{ fontSize: '22px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '8px' }}>
            {incident.title}
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '13px', color: 'var(--text-secondary)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Tag size={14} />
              <span>Service: {incident.service || 'System'}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <User size={14} />
              <span>Assignee: {incident.assignee || 'Unassigned'}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Clock size={14} />
              <span>Updated: {new Date(incident.updated_at || Date.now()).toLocaleTimeString()}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default IncidentHeader;

import React from 'react';
import StatusBadge from '../common/StatusBadge';
import JiraStatusBadge from '../common/JiraStatusBadge';
import SeverityBadge from '../common/SeverityBadge';
import { ExternalLink } from 'lucide-react';

export function IncidentTable({ incidents = [], onSelectIncident }) {
  if (incidents.length === 0) {
    return (
      <div style={{ padding: '32px 24px', textAlign: 'center', color: 'var(--text-secondary)' }}>
        No incidents available in repository.
      </div>
    );
  }

  return (
    <div className="table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Incident Title</th>
            <th>Severity</th>
            <th>Service</th>
            <th>Jira Status</th>
            <th>Workflow Stage</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {incidents.map((inc) => (
            <tr
              key={inc.issue_key}
              className="clickable-row"
              onClick={() => onSelectIncident(inc.issue_key)}
            >
              <td className="code-mono" style={{ fontWeight: '700', color: 'var(--brand-primary)' }}>
                {inc.issue_key}
              </td>
              <td style={{ fontWeight: '500', color: 'var(--text-primary)', maxWidth: '280px' }}>
                <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={inc.title}>
                  {inc.title}
                </div>
              </td>
              <td>
                <SeverityBadge severity={inc.severity} />
              </td>
              <td style={{ color: 'var(--text-secondary)' }}>
                {inc.service || 'System'}
              </td>
              <td>
                <JiraStatusBadge status={inc.jira_status} />
              </td>
              <td>
                <StatusBadge status={inc.stage_status} stage={inc.current_stage} />
              </td>
              <td>
                <button
                  style={{
                    color: 'var(--brand-primary)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '12px',
                    fontWeight: '600'
                  }}
                >
                  <span>View</span>
                  <ExternalLink size={12} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default IncidentTable;

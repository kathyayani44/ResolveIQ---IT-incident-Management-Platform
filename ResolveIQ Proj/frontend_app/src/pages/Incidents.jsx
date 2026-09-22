import React, { useState } from 'react';
import PageContainer from '../components/layout/PageContainer';
import IncidentTable from '../components/dashboard/IncidentTable';
import EmptyState from '../components/common/EmptyState';
import { Search, Filter, AlertOctagon } from 'lucide-react';

export function Incidents({ incidents = [], onSelectIncident }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const uniqueJiraStatuses = Array.from(new Set(incidents.map(i => i.jira_status).filter(Boolean)));

  const filteredIncidents = incidents.filter(inc => {
    const matchesSearch =
      (inc.issue_key || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (inc.title || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (inc.service || '').toLowerCase().includes(searchQuery.toLowerCase());

    const matchesSeverity =
      severityFilter === 'ALL' || (inc.severity || '').toUpperCase() === severityFilter;

    const matchesStatus =
      statusFilter === 'ALL' ||
      (inc.jira_status || '').toLowerCase() === statusFilter.toLowerCase();

    return matchesSearch && matchesSeverity && matchesStatus;
  });

  return (
    <PageContainer
      title="Incidents Repository"
      subtitle="Monitor every incident synchronized with Jira and moving through the ResolveIQ pipeline."
    >
      {/* Filter Bar */}
      <div className="panel" style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: '280px' }}>
          <div style={{ position: 'relative', width: '100%', maxWidth: '360px' }}>
            <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="Search by ID, title, or service..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                backgroundColor: 'var(--bg-dark)',
                border: '1px solid var(--border-medium)',
                borderRadius: '6px',
                padding: '8px 12px 8px 36px',
                color: 'var(--text-primary)',
                fontSize: '13px',
                outline: 'none'
              }}
            />
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--text-secondary)' }}>
            <Filter size={14} />
            <span>Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              style={{
                backgroundColor: 'var(--bg-dark)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-medium)',
                borderRadius: '6px',
                padding: '6px 10px',
                fontSize: '12px',
                outline: 'none'
              }}
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--text-secondary)' }}>
            <span>Jira Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{
                backgroundColor: 'var(--bg-dark)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-medium)',
                borderRadius: '6px',
                padding: '6px 10px',
                fontSize: '12px',
                outline: 'none'
              }}
            >
              <option value="ALL">All Jira Statuses</option>
              {uniqueJiraStatuses.map(statusName => (
                <option key={statusName} value={statusName}>{statusName}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Incidents Table */}
      {filteredIncidents.length === 0 ? (
        <EmptyState
          title="No Incidents Found"
          message="Incidents retrieved from Jira API or webhook events will appear here."
          icon={AlertOctagon}
        />
      ) : (
        <IncidentTable incidents={filteredIncidents} onSelectIncident={onSelectIncident} />
      )}
    </PageContainer>
  );
}

export default Incidents;

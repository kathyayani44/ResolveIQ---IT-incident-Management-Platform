import React from 'react';
import PageContainer from '../components/layout/PageContainer';
import LiveOperations from '../components/dashboard/LiveOperations';
import StatCard from '../components/dashboard/StatCard';
import NeedsAttention from '../components/dashboard/NeedsAttention';
import WorkflowPipeline from '../components/dashboard/WorkflowPipeline';
import IncidentTable from '../components/dashboard/IncidentTable';
import RecentJiraUpdates from '../components/dashboard/RecentJiraUpdates';
import { AlertOctagon, Clock, CheckCircle2, ShieldCheck, Activity } from 'lucide-react';

export function Dashboard({ incidents = [], onSelectIncident, onNavigate }) {
  const activeCount = incidents.length;
  const processingCount = incidents.filter(i => i.stage_status === 'processing' || i.current_stage === 'rca' || i.current_stage === 'resolution').length;
  const pendingApprovals = incidents.filter(i => (i.current_stage === 'approval' && i.stage_status === 'awaiting_approval') || i.approval?.status === 'pending');
  const resolvedCount = incidents.filter(i => i.approval?.status === 'approved' || i.current_stage === 'jira_update').length;
  const jiraUpdatedCount = incidents.filter(i => i.jira_update?.status === 'completed').length;

  return (
    <PageContainer
      title="Incident Operations Center"
      subtitle="Monitor, investigate, and approve AI multi-agent incident resolutions in real time."
    >
      {/* Live Operations Status Banner */}
      <LiveOperations incidents={incidents} />

      {/* Primary Stat Overview Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <StatCard
          title="ACTIVE INCIDENTS"
          count={activeCount}
          subtitle={`${processingCount} currently processing`}
          icon={AlertOctagon}
          color="var(--brand-primary)"
        />
        <StatCard
          title="PROCESSING"
          count={processingCount}
          subtitle="Multi-agent pipeline running"
          icon={Activity}
          color="#f59e0b"
          highlight={processingCount > 0}
        />
        <StatCard
          title="AWAITING APPROVAL"
          count={pendingApprovals.length}
          subtitle="Human review required"
          icon={Clock}
          color="#818cf8"
          highlight={pendingApprovals.length > 0}
        />
        <StatCard
          title="RESOLVED"
          count={resolvedCount}
          subtitle="Approved by IT Ops"
          icon={CheckCircle2}
          color="#34d399"
        />
        <StatCard
          title="JIRA UPDATED"
          count={jiraUpdatedCount}
          subtitle="Jira REST API synced"
          icon={ShieldCheck}
          color="#10b981"
        />
      </div>

      {/* Needs Attention Alert Panel */}
      <div style={{ marginBottom: '24px' }}>
        <NeedsAttention
          pendingApprovals={pendingApprovals}
          onSelectIncident={onSelectIncident}
          onViewApprovals={() => onNavigate('approvals')}
        />
      </div>

      {/* Workflow Operational Pipeline */}
      <WorkflowPipeline incidents={incidents} />

      {/* Main Recent Incidents Table & Jira Updates Split */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px', alignItems: 'start' }}>
        <div className="panel">
          <div className="panel-header">
            <h3 style={{ fontSize: '15px' }}>RECENT INCIDENTS</h3>
            <button
              onClick={() => onNavigate('incidents')}
              style={{ fontSize: '12px', color: 'var(--brand-primary)', fontWeight: '600' }}
            >
              View all incidents →
            </button>
          </div>
          <IncidentTable incidents={incidents} onSelectIncident={onSelectIncident} />
        </div>

        <div>
          <RecentJiraUpdates incidents={incidents} onSelectIncident={onSelectIncident} />
        </div>
      </div>
    </PageContainer>
  );
}

export default Dashboard;

import React from 'react';
import { Clock, AlertCircle, CheckCircle2, XCircle, ArrowRight } from 'lucide-react';

export function StatusBadge({ status, stage }) {
  const normalizedStatus = (status || stage || '').toLowerCase();

  if (normalizedStatus.includes('processing') || normalizedStatus.includes('running') || normalizedStatus.includes('in_progress')) {
    return (
      <span className="badge badge-processing">
        <span className="pulse-dot" />
        Processing
      </span>
    );
  }

  if (normalizedStatus.includes('approval') || normalizedStatus.includes('awaiting')) {
    return (
      <span className="badge badge-approval">
        <Clock size={13} />
        Awaiting Approval
      </span>
    );
  }

  if (normalizedStatus.includes('must_revise') || normalizedStatus.includes('must revise')) {
    return (
      <span className="badge badge-warning" style={{ backgroundColor: 'rgba(245, 158, 11, 0.18)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.4)' }}>
        <AlertCircle size={13} />
        Must Revise
      </span>
    );
  }

  if (normalizedStatus.includes('completed') || normalizedStatus.includes('approved') || normalizedStatus.includes('jira') || normalizedStatus.includes('resolved')) {
    return (
      <span className="badge badge-success">
        <CheckCircle2 size={13} />
        {normalizedStatus.includes('jira') ? 'Jira Updated' : 'Resolved'}
      </span>
    );
  }

  if (normalizedStatus.includes('rejected') || normalizedStatus.includes('failed')) {
    return (
      <span className="badge badge-failed">
        <XCircle size={13} />
        {normalizedStatus.includes('rejected') ? 'Rejected' : 'Failed'}
      </span>
    );
  }

  return (
    <span className="badge badge-muted">
      <AlertCircle size={13} />
      {status || 'Pending'}
    </span>
  );
}

export default StatusBadge;

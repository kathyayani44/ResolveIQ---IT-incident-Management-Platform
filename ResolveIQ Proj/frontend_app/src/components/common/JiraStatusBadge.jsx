import React from 'react';
import { Clock, CheckCircle2, AlertCircle, PlayCircle } from 'lucide-react';

export function JiraStatusBadge({ status }) {
  const displayStatus = status || 'Open';
  const lower = displayStatus.toLowerCase();

  let bg = 'rgba(56, 189, 248, 0.12)';
  let border = 'rgba(56, 189, 248, 0.4)';
  let color = '#38bdf8';
  let Icon = AlertCircle;

  if (lower.includes('completed') || lower.includes('done') || lower.includes('closed')) {
    bg = 'rgba(16, 185, 129, 0.15)';
    border = 'rgba(16, 185, 129, 0.5)';
    color = '#34d399';
    Icon = CheckCircle2;
  } else if (lower.includes('resolved')) {
    bg = 'rgba(20, 184, 166, 0.15)';
    border = 'rgba(20, 184, 166, 0.5)';
    color = '#2dd4bf';
    Icon = CheckCircle2;
  } else if (lower.includes('in progress') || lower.includes('in_progress') || lower.includes('investigating')) {
    bg = 'rgba(245, 158, 11, 0.15)';
    border = 'rgba(245, 158, 11, 0.5)';
    color = '#fbbf24';
    Icon = PlayCircle;
  } else if (lower.includes('waiting for support') || lower.includes('support')) {
    bg = 'rgba(99, 102, 241, 0.15)';
    border = 'rgba(99, 102, 241, 0.5)';
    color = '#818cf8';
    Icon = Clock;
  } else if (lower.includes('waiting for approval') || lower.includes('approval')) {
    bg = 'rgba(168, 85, 247, 0.15)';
    border = 'rgba(168, 85, 247, 0.5)';
    color = '#c084fc';
    Icon = Clock;
  }

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        padding: '3px 9px',
        borderRadius: '12px',
        fontSize: '11px',
        fontWeight: '600',
        backgroundColor: bg,
        border: `1px solid ${border}`,
        color: color,
        whiteSpace: 'nowrap',
      }}
      title={`Jira Authoritative Status: ${displayStatus}`}
    >
      <Icon size={12} />
      <span>{displayStatus}</span>
    </span>
  );
}

export default JiraStatusBadge;

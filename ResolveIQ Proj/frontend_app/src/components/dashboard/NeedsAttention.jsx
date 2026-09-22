import React from 'react';
import { AlertCircle, ArrowRight } from 'lucide-react';
import SeverityBadge from '../common/SeverityBadge';

export function NeedsAttention({ pendingApprovals = [], onSelectIncident, onViewApprovals }) {
  return (
    <div className="panel" style={{ border: '1px solid rgba(99, 102, 241, 0.4)', backgroundColor: 'rgba(99, 102, 241, 0.05)' }}>
      <div className="panel-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertCircle size={18} color="#818cf8" />
          <h3 style={{ fontSize: '15px', color: '#ffffff' }}>NEEDS ATTENTION</h3>
        </div>
        <span style={{ fontSize: '12px', fontWeight: '600', color: '#818cf8', backgroundColor: 'rgba(99,102,241,0.15)', padding: '2px 8px', borderRadius: '4px' }}>
          {pendingApprovals.length} Awaiting Approval
        </span>
      </div>

      {pendingApprovals.length === 0 ? (
        <div style={{ padding: '16px 0', color: 'var(--text-secondary)', fontSize: '13px' }}>
          ✓ No recommendations currently waiting for human approval decision.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '16px' }}>
          {pendingApprovals.slice(0, 3).map((inc) => (
            <div
              key={inc.issue_key}
              onClick={() => onSelectIncident(inc.issue_key)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 14px',
                borderRadius: '6px',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                cursor: 'pointer'
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <span className="code-mono" style={{ fontWeight: '700', color: 'var(--brand-primary)' }}>{inc.issue_key}</span>
                  <span style={{ color: 'var(--text-primary)', fontWeight: '500' }}>{inc.title}</span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  RCA: {inc.rca?.root_cause?.slice(0, 60) || 'Root cause identified'}...
                </div>
              </div>
              <SeverityBadge severity={inc.severity} />
            </div>
          ))}
        </div>
      )}

      <button
        onClick={onViewApprovals}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          color: '#818cf8',
          fontSize: '13px',
          fontWeight: '600',
          marginTop: '4px'
        }}
      >
        <span>Review approval queue</span>
        <ArrowRight size={14} />
      </button>
    </div>
  );
}

export default NeedsAttention;

import React from 'react';
import SeverityBadge from '../common/SeverityBadge';
import { ArrowRight, CheckCircle2 } from 'lucide-react';

export function ApprovalQueue({ pendingIncidents = [], onSelectForReview }) {
  if (pendingIncidents.length === 0) {
    return (
      <div className="panel" style={{ textAlign: 'center', padding: '36px 20px', border: '1px solid var(--border-subtle)' }}>
        <div style={{
          width: '44px',
          height: '44px',
          borderRadius: '50%',
          backgroundColor: 'rgba(16, 185, 129, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#34d399',
          margin: '0 auto 12px'
        }}>
          <CheckCircle2 size={24} />
        </div>
        <h3 style={{ fontSize: '16px', color: '#ffffff', marginBottom: '4px' }}>✓ ALL CAUGHT UP</h3>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          No incidents are currently waiting for human approval decision. ResolveIQ will surface new recommendations here as they finish RCA.
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {pendingIncidents.map((inc) => (
        <div
          key={inc.issue_key}
          className="panel"
          style={{
            borderLeft: '4px solid #6366f1',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <span className="code-mono" style={{ fontSize: '16px', fontWeight: '700', color: 'var(--brand-primary)' }}>
                {inc.issue_key}
              </span>
              <SeverityBadge severity={inc.severity} />
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{inc.service || 'System'}</span>
            </div>

            <h3 style={{ fontSize: '15px', color: 'var(--text-primary)', marginBottom: '4px' }}>
              {inc.title}
            </h3>

            <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              RCA: <span style={{ color: '#ffffff', fontWeight: '500' }}>{inc.rca?.root_cause || 'Root cause identified'}</span>
            </div>
          </div>

          <button
            onClick={() => onSelectForReview(inc)}
            className="btn-approve"
            style={{ fontSize: '13px', flexShrink: 0 }}
          >
            <span>Review Recommendation</span>
            <ArrowRight size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}

export default ApprovalQueue;

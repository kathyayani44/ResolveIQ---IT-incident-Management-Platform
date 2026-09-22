import React from 'react';
import { Target, CheckCircle } from 'lucide-react';

export function RCASection({ rca }) {
  if (!rca) {
    return (
      <div className="panel" style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '15px', marginBottom: '8px' }}>ROOT CAUSE ANALYSIS (RCA)</h3>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>RCA analysis is in progress or not yet executed.</p>
      </div>
    );
  }

  return (
    <div className="panel" style={{ marginBottom: '24px', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
      <div className="panel-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Target size={18} color="#f59e0b" />
          <h3 style={{ fontSize: '15px', color: '#ffffff' }}>ROOT CAUSE ANALYSIS (RCA)</h3>
        </div>
        <span style={{
          fontSize: '11px',
          fontWeight: '700',
          color: '#fbbf24',
          backgroundColor: 'rgba(245, 158, 11, 0.15)',
          padding: '2px 8px',
          borderRadius: '4px',
          textTransform: 'uppercase'
        }}>
          Status: {rca.status || 'IDENTIFIED'}
        </span>
      </div>

      <div style={{
        backgroundColor: 'rgba(245, 158, 11, 0.08)',
        border: '1px solid rgba(245, 158, 11, 0.2)',
        borderRadius: '8px',
        padding: '16px 20px',
        marginBottom: '16px'
      }}>
        <h4 style={{ fontSize: '11px', color: '#fbbf24', marginBottom: '6px' }}>IDENTIFIED ROOT CAUSE</h4>
        <p style={{ fontSize: '14px', fontWeight: '600', color: '#ffffff', lineHeight: '1.5' }}>
          {rca.root_cause || 'No definitive root cause identified.'}
        </p>
      </div>

      {rca.evidence && rca.evidence.length > 0 && (
        <div>
          <h4 style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>SUPPORTING RCA EVIDENCE</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {rca.evidence.map((ev, idx) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                <CheckCircle size={14} color="#f59e0b" style={{ marginTop: '2px', flexShrink: 0 }} />
                <div>
                  <span className="code-mono" style={{ color: 'var(--brand-primary)', fontWeight: '600' }}>[{ev.chunk_id}]</span>: {ev.reason}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default RCASection;

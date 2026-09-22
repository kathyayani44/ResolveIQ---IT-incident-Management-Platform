import React from 'react';
import { Activity, Clock } from 'lucide-react';

export function LiveOperations({ incidents = [] }) {
  const activeOps = incidents.slice(0, 3);

  return (
    <div style={{
      backgroundColor: 'rgba(56, 189, 248, 0.08)',
      border: '1px solid rgba(56, 189, 248, 0.25)',
      borderRadius: 'var(--radius-md)',
      padding: '16px 20px',
      marginBottom: '24px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="pulse-dot" />
          <h3 style={{ fontSize: '13px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--brand-primary)' }}>
            LIVE OPERATIONS
          </h3>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-muted)' }}>
          <Clock size={12} />
          <span>Real-time monitoring active</span>
        </div>
      </div>

      {activeOps.length === 0 ? (
        <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          ● SYSTEM READY — No active incidents currently processing. New incidents will appear here automatically.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {activeOps.map((inc) => (
            <div key={inc.issue_key} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '13px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span className="code-mono" style={{ fontWeight: '600', color: '#ffffff' }}>{inc.issue_key}</span>
                <span style={{ color: 'var(--text-secondary)' }}>{inc.title}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{inc.current_stage?.toUpperCase() || 'STAGE'}</span>
                <span style={{ color: 'var(--brand-primary)', fontWeight: '600' }}>→ {inc.stage_status?.replace('_', ' ')}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default LiveOperations;

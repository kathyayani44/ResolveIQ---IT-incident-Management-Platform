import React from 'react';
import { ShieldCheck, Info } from 'lucide-react';

export function EmptyState({ title, message, icon: Icon = ShieldCheck, action }) {
  return (
    <div style={{
      padding: '40px 24px',
      textAlign: 'center',
      backgroundColor: 'var(--bg-surface)',
      border: '1px border-dashed var(--border-medium)',
      borderRadius: 'var(--radius-md)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <div style={{
        width: '48px',
        height: '48px',
        borderRadius: '50%',
        backgroundColor: 'rgba(56, 189, 248, 0.12)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--brand-primary)',
        marginBottom: '16px'
      }}>
        <Icon size={24} />
      </div>
      <h3 style={{ fontSize: '16px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '6px' }}>
        {title || 'All Systems Ready'}
      </h3>
      <p style={{ color: 'var(--text-secondary)', fontSize: '13px', maxWidth: '420px', marginBottom: action ? '20px' : '0' }}>
        {message || 'No active operational items require your attention at this time.'}
      </p>
      {action}
    </div>
  );
}

export default EmptyState;

import React from 'react';

export function StatCard({ title, count, subtitle, icon: Icon, color = 'var(--brand-primary)', highlight }) {
  return (
    <div className="panel" style={{
      borderLeft: highlight ? `4px solid ${color}` : undefined,
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      height: '100%'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <h4 style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{title}</h4>
        {Icon && <Icon size={18} color={color} />}
      </div>

      <div style={{ marginBottom: '8px' }}>
        <span style={{ fontSize: '28px', fontWeight: '700', color: 'var(--text-primary)', lineHeight: '1' }}>
          {count}
        </span>
      </div>

      {subtitle && (
        <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
          {subtitle}
        </div>
      )}
    </div>
  );
}

export default StatCard;

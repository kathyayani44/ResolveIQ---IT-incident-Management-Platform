import React from 'react';

export function PageContainer({ title, subtitle, actions, children }) {
  return (
    <div className="page-content">
      {/* Page Heading Banner */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1 style={{ color: 'var(--text-primary)', marginBottom: '4px' }}>{title}</h1>
          {subtitle && <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>{subtitle}</p>}
        </div>
        {actions && <div style={{ display: 'flex', gap: '10px' }}>{actions}</div>}
      </div>

      {/* Page Body */}
      {children}
    </div>
  );
}

export default PageContainer;

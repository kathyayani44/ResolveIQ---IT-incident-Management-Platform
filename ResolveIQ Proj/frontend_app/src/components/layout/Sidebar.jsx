import React from 'react';
import { LayoutDashboard, AlertOctagon, CheckSquare, ShieldCheck, User, LogOut, Cpu, ExternalLink } from 'lucide-react';

export function Sidebar({ activePage, setActivePage, currentUser, jiraConnection, onSignOut }) {
  const navItems = [
    { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
    { id: 'incidents', label: 'Incidents', icon: AlertOctagon },
    { id: 'approvals', label: 'Approvals', icon: CheckSquare },
  ];

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '28px' }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '8px',
          background: 'linear-gradient(135deg, #38bdf8 0%, #6366f1 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#ffffff',
          fontWeight: '700'
        }}>
          <Cpu size={22} />
        </div>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: '700', color: '#ffffff', lineHeight: '1.2' }}>ResolveIQ</h2>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Incident Ops</span>
        </div>
      </div>

      {/* Primary Navigation */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <span style={{ fontSize: '11px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: '8px', paddingLeft: '8px' }}>
          Navigation
        </span>
        {navItems.map(item => {
          const Icon = item.icon;
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActivePage(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 12px',
                borderRadius: '6px',
                color: isActive ? '#ffffff' : 'var(--text-secondary)',
                backgroundColor: isActive ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
                borderLeft: isActive ? '3px solid var(--brand-primary)' : '3px solid transparent',
                fontWeight: isActive ? '600' : '500',
                transition: 'all 0.15s ease',
                width: '100%',
                textAlign: 'left'
              }}
            >
              <Icon size={18} color={isActive ? 'var(--brand-primary)' : 'var(--text-secondary)'} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* User Account & Jira Connection Footer */}
      <div style={{ marginTop: 'auto', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {/* User Card */}
        <div style={{
          padding: '10px 12px',
          borderRadius: '8px',
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              <User size={12} />
              <span>Operator</span>
            </div>
            <button
              onClick={onSignOut}
              title="Sign Out of ResolveIQ"
              style={{
                fontSize: '11px',
                color: '#f87171',
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.25)',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: '600',
                padding: '2px 8px',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                transition: 'all 0.15s ease'
              }}
            >
              <LogOut size={10} />
              <span>Sign Out</span>
            </button>
          </div>
          <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {currentUser?.name || 'ResolveIQ Operator'}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {currentUser?.email || ''}
          </div>

          {/* Connected Jira Info */}
          {jiraConnection && (
            <div style={{
              marginTop: '8px',
              paddingTop: '8px',
              borderTop: '1px solid var(--border-subtle)',
              fontSize: '11px',
              color: 'var(--text-secondary)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Jira Account:</span>
                <span style={{ color: jiraConnection.connected ? '#34d399' : '#f87171', fontWeight: '600' }}>
                  {jiraConnection.connected ? 'Connected' : 'Offline'}
                </span>
              </div>
              <div style={{ color: 'var(--text-primary)', fontWeight: '500', marginTop: '2px', fontSize: '11px' }}>
                {jiraConnection.displayName || jiraConnection.domain || 'Jira Cloud'}
              </div>
            </div>
          )}
        </div>

        {/* Engine status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', borderRadius: '6px', backgroundColor: 'var(--bg-surface)' }}>
          <ShieldCheck size={16} color="#10b981" />
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            FastAPI Read-Only MVP
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;

import React from 'react';
import { Search, Activity, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';

export function Header({
  backendHealthy,
  jiraConnection,
  syncing,
  onRefresh,
  onSyncJira,
  searchKey,
  setSearchKey,
  onFetchJiraKey
}) {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && searchKey.trim()) {
      onFetchJiraKey(searchKey.trim());
    }
  };

  const isJiraConnected = jiraConnection?.connected;

  return (
    <header className="header">
      {/* Search / Jira Key Fetcher */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '360px' }}>
        <div style={{ position: 'relative', width: '100%' }}>
          <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            placeholder="Fetch Jira key by ID..."
            value={searchKey}
            onChange={(e) => setSearchKey(e.target.value)}
            onKeyDown={handleKeyDown}
            style={{
              width: '100%',
              backgroundColor: 'var(--bg-dark)',
              border: '1px solid var(--border-medium)',
              borderRadius: '6px',
              padding: '8px 12px 8px 36px',
              color: 'var(--text-primary)',
              fontSize: '13px',
              outline: 'none'
            }}
          />
        </div>
      </div>

      {/* Header Actions & Health Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
        {/* Sync Jira Button */}
        <button
          onClick={onSyncJira}
          disabled={syncing}
          className="btn-primary"
          title="Trigger read-only synchronization of all Jira issues"
          style={{
            fontSize: '12px',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '7px 14px',
            borderRadius: '6px',
            cursor: syncing ? 'not-allowed' : 'pointer',
            opacity: syncing ? 0.7 : 1
          }}
        >
          <RefreshCw size={13} className={syncing ? 'spin-animation' : ''} />
          <span>{syncing ? 'Syncing Jira...' : 'Sync Jira'}</span>
        </button>

        {/* Jira Connection Indicator */}
        <div
          title={isJiraConnected ? `Connected to Jira domain ${jiraConnection?.domain} as ${jiraConnection?.displayName || ''}` : 'Jira connection not verified'}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            borderRadius: '20px',
            backgroundColor: isJiraConnected ? 'rgba(56,189,248,0.12)' : 'rgba(239,68,68,0.12)',
            border: `1px solid ${isJiraConnected ? 'rgba(56,189,248,0.4)' : '#ef4444'}`,
            fontSize: '12px',
            fontWeight: '600',
            color: isJiraConnected ? '#38bdf8' : '#f87171'
          }}
        >
          {isJiraConnected ? <CheckCircle2 size={13} /> : <AlertCircle size={13} />}
          <span>
            {isJiraConnected ? `Jira: ${jiraConnection?.domain || 'Connected'}` : 'Jira Offline'}
          </span>
        </div>

        {/* Backend Status */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 12px',
          borderRadius: '20px',
          backgroundColor: backendHealthy === false ? 'rgba(239,68,68,0.15)' : 'rgba(16,185,129,0.15)',
          border: `1px solid ${backendHealthy === false ? '#ef4444' : '#10b981'}`,
          fontSize: '12px',
          fontWeight: '600',
          color: backendHealthy === false ? '#f87171' : '#34d399'
        }}>
          <Activity size={13} />
          <span>{backendHealthy === false ? 'Backend Offline' : 'Operational'}</span>
        </div>
      </div>
    </header>
  );
}

export default Header;

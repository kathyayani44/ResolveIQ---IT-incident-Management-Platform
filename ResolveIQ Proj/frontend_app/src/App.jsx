import React, { useState } from 'react';
import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';
import Dashboard from './pages/Dashboard';
import Incidents from './pages/Incidents';
import IncidentDetails from './pages/IncidentDetails';
import Approvals from './pages/Approvals';
import AuthPage from './pages/AuthPage';
import { useIncidents } from './hooks/useIncidents';
import ErrorBanner from './components/common/ErrorBanner';
import { Cpu } from 'lucide-react';

export function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [selectedIssueKey, setSelectedIssueKey] = useState(null);
  const [searchKey, setSearchKey] = useState('');

  const {
    incidents,
    loading,
    syncing,
    error,
    backendHealthy,
    jiraConnection,
    currentUser,
    authLoading,
    refreshIncidents,
    syncJira,
    updateIncidentState,
    ingestJiraKey,
    loginUser,
    registerUser,
    logoutUser,
  } = useIncidents();

  const handleSelectIncident = (issueKey) => {
    setSelectedIssueKey(issueKey);
    setActivePage('incident_details');
  };

  const handleFetchJiraKey = async (key) => {
    const res = await ingestJiraKey(key);
    if (res.ok) {
      handleSelectIncident(key);
    }
  };

  // 1. Initial Authentication Loading State
  if (authLoading) {
    return (
      <div style={{
        minHeight: '100vh',
        width: '100vw',
        backgroundColor: '#0c0e14',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '16px'
      }}>
        <div style={{
          width: '48px',
          height: '48px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, #38bdf8 0%, #6366f1 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#ffffff',
          boxShadow: '0 8px 24px -4px rgba(56, 189, 248, 0.4)'
        }}>
          <Cpu size={26} />
        </div>
        <div style={{ fontSize: '13px', fontWeight: '500', color: 'rgba(255, 255, 255, 0.6)' }}>
          Authenticating ResolveIQ session...
        </div>
      </div>
    );
  }

  // 2. Unauthenticated Redirection to AuthPage
  if (!currentUser) {
    return (
      <AuthPage
        onLogin={loginUser}
        onRegister={registerUser}
      />
    );
  }

  // 3. Authenticated Application Shell
  return (
    <div className="app-container">
      {/* Sidebar */}
      <Sidebar
        activePage={activePage === 'incident_details' ? 'incidents' : activePage}
        setActivePage={(page) => {
          setSelectedIssueKey(null);
          setActivePage(page);
        }}
        currentUser={currentUser}
        jiraConnection={jiraConnection}
        onSignOut={logoutUser}
      />

      {/* Main Layout Shell */}
      <div className="main-layout">
        <Header
          backendHealthy={backendHealthy}
          jiraConnection={jiraConnection}
          syncing={syncing}
          onRefresh={refreshIncidents}
          onSyncJira={syncJira}
          searchKey={searchKey}
          setSearchKey={setSearchKey}
          onFetchJiraKey={handleFetchJiraKey}
        />

        {error && <ErrorBanner message={error} />}

        {/* Dynamic Page Routing */}
        {activePage === 'dashboard' && (
          <Dashboard
            incidents={incidents}
            onSelectIncident={handleSelectIncident}
            onNavigate={setActivePage}
          />
        )}

        {activePage === 'incidents' && (
          <Incidents
            incidents={incidents}
            onSelectIncident={handleSelectIncident}
          />
        )}

        {activePage === 'incident_details' && (
          <IncidentDetails
            issueKey={selectedIssueKey}
            onBack={() => setActivePage('incidents')}
            initialIncidents={incidents}
          />
        )}

        {activePage === 'approvals' && (
          <Approvals
            incidents={incidents}
            onUpdateIncidentState={updateIncidentState}
            onSelectIncident={handleSelectIncident}
          />
        )}
      </div>
    </div>
  );
}

export default App;

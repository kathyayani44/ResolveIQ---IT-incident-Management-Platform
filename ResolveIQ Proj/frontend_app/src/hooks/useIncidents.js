import { useState, useEffect, useCallback, useRef } from 'react';
import api from '../services/api';

export function useIncidents() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState(null);
  const [backendHealthy, setBackendHealthy] = useState(null);
  const [jiraConnection, setJiraConnection] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  const initialLoadDoneRef = useRef(false);
  const syncInProgressRef = useRef(false);

  const mapCanonicalToUI = (canonical) => {
    const rawJiraStatus = canonical.jira_status || canonical.status || 'Open';
    return {
      ...canonical,
      // Jira status is the authoritative status reported by Jira
      jira_status: rawJiraStatus,
      jira_resolution: canonical.resolution || null,
      // Internal ResolveIQ AI workflow state
      category: canonical.metadata?.classification?.category || canonical.metadata?.category || canonical.category || 'General',
      service: canonical.metadata?.classification?.service || canonical.metadata?.service || canonical.service || 'System',
      current_stage: canonical.metadata?.current_stage || canonical.workflow_status || 'unprocessed',
      stage_status: canonical.metadata?.stage_status || (canonical.workflow_status === 'unprocessed' ? 'pending' : 'completed'),
      workflow_status: canonical.workflow_status || 'unprocessed',
      approval: canonical.metadata?.approval || { status: 'pending' },
      jira_update: canonical.metadata?.jira_update || { status: 'pending' },
      rca: canonical.metadata?.rca || null,
      resolution: canonical.metadata?.resolution || null,
      evidence: canonical.metadata?.evidence || [],
    };
  };

  const checkConnectionAndUser = useCallback(async () => {
    try {
      // 1. Check health
      const healthRes = await api.checkHealth();
      setBackendHealthy(healthRes.ok);

      // 2. Check current user
      const userRes = await api.getMe();
      if (userRes.ok) {
        setCurrentUser(userRes.data);
      } else {
        setCurrentUser(null);
      }

      // 3. Check read-only Jira connection
      const jiraRes = await api.getJiraConnection();
      if (jiraRes.ok) {
        setJiraConnection(jiraRes.data);
      }
    } finally {
      setAuthLoading(false);
    }
  }, []);

  const refreshIncidents = useCallback(async (options = {}) => {
    setLoading(true);
    setError(null);

    await checkConnectionAndUser();

    try {
      let listRes = await api.getIncidents({ sync: options.forceSync || false });

      if (!listRes.ok) {
        setError('Unable to retrieve incidents from Jira.');
        setIncidents([]);
        return;
      }

      let data = listRes.data || [];

      // If backend incident store is empty on initial load, run a single initial sync from Jira
      if (data.length === 0 && !syncInProgressRef.current && (options.forceSync || !initialLoadDoneRef.current)) {
        syncInProgressRef.current = true;
        setSyncing(true);
        const syncRes = await api.syncJiraIssues();
        syncInProgressRef.current = false;
        setSyncing(false);

        if (syncRes.ok) {
          listRes = await api.getIncidents();
          data = listRes.ok ? (listRes.data || []) : [];
        } else {
          setError('Unable to retrieve incidents from Jira.');
          setIncidents([]);
          return;
        }
      }

      const mapped = data.map(mapCanonicalToUI);
      setIncidents(mapped);
    } catch (err) {
      setError('Unable to retrieve incidents from Jira.');
      setIncidents([]);
    } finally {
      setLoading(false);
      initialLoadDoneRef.current = true;
    }
  }, [checkConnectionAndUser]);

  // Initial single load flow
  useEffect(() => {
    if (!initialLoadDoneRef.current) {
      refreshIncidents();
    }
  }, [refreshIncidents]);

  // Explicit manual Jira sync triggered by user
  const syncJira = useCallback(async () => {
    if (syncInProgressRef.current) return;
    syncInProgressRef.current = true;
    setSyncing(true);
    setError(null);
    try {
      const syncRes = await api.syncJiraIssues();
      if (!syncRes.ok) {
        setError('Unable to retrieve incidents from Jira.');
      } else {
        await refreshIncidents({ forceSync: false });
      }
    } catch {
      setError('Unable to retrieve incidents from Jira.');
    } finally {
      syncInProgressRef.current = false;
      setSyncing(false);
    }
  }, [refreshIncidents]);

  const updateIncidentState = useCallback((issueKey, updateFn) => {
    setIncidents(prev =>
      prev.map(item => (item.issue_key === issueKey ? updateFn(item) : item))
    );
  }, []);

  const ingestJiraKey = async (issueKey) => {
    setLoading(true);
    const res = await api.fetchJiraIssue(issueKey);
    if (res.ok) {
      await refreshIncidents();
    } else {
      setError(res.error || 'Unable to retrieve incidents from Jira.');
    }
    setLoading(false);
    return res;
  };

  const loginUser = async (email, password) => {
    const res = await api.login(email, password);
    if (res.ok) {
      setCurrentUser(res.data);
      await refreshIncidents();
    }
    return res;
  };

  const registerUser = async (email, password, name) => {
    const res = await api.register(email, password, name);
    if (res.ok) {
      setCurrentUser(res.data);
      await refreshIncidents();
    }
    return res;
  };

  const logoutUser = () => {
    api.logout();
    setCurrentUser(null);
    setIncidents([]);
    setError(null);
  };

  return {
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
  };
}

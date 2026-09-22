/**
 * ResolveIQ Centralized API Service Layer
 * Interfaces exclusively with the FastAPI Backend (http://127.0.0.1:8000)
 */

const API_BASE = '/api/v1';

function getAuthToken() {
  try {
    return localStorage.getItem('resolveiq_token') || '';
  } catch {
    return '';
  }
}

export function setAuthToken(token) {
  try {
    if (token) {
      localStorage.setItem('resolveiq_token', token);
    } else {
      localStorage.removeItem('resolveiq_token');
    }
  } catch {
    // Ignore localStorage errors
  }
}

async function fetchJSON(url, options = {}) {
  const token = getAuthToken();
  const defaultHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status} ${response.statusText}`;
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorDetail = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
    } catch {
      // Ignore json parse error for non-json responses
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  /**
   * Check backend operational health
   */
  async checkHealth() {
    try {
      const data = await fetchJSON('/health');
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  },

  /**
   * ResolveIQ User Authentication
   */
  async login(email, password) {
    try {
      const data = await fetchJSON(`${API_BASE}/auth/login`, {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      if (data?.token) setAuthToken(data.token);
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  },

  async register(email, password, name) {
    try {
      const data = await fetchJSON(`${API_BASE}/auth/register`, {
        method: 'POST',
        body: JSON.stringify({ email, password, name }),
      });
      if (data?.token) setAuthToken(data.token);
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  },

  async getMe() {
    try {
      const data = await fetchJSON(`${API_BASE}/auth/me`);
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  },

  logout() {
    setAuthToken(null);
  },

  /**
   * Check read-only Jira connection status (Standardized endpoint)
   */
  async getJiraConnection() {
    try {
      const data = await fetchJSON(`${API_BASE}/jira/connection`);
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  },

  /**
   * Synchronize all accessible issues from Jira API (Read-only GET requests)
   */
  async syncJiraIssues() {
    try {
      const data = await fetchJSON(`${API_BASE}/jira/sync`, {
        method: 'POST',
      });
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  },

  /**
   * Get all normalized CanonicalIncidents from backend
   */
  async getIncidents(options = {}) {
    try {
      const query = options.sync ? '?sync=true' : '';
      const data = await fetchJSON(`${API_BASE}/incidents${query}`);
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  },

  /**
   * Get single normalized CanonicalIncident by Jira issue key
   */
  async getIncident(issueKey) {
    try {
      const data = await fetchJSON(`${API_BASE}/incidents/${encodeURIComponent(issueKey)}`);
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  },

  /**
   * Fetch and ingest raw issue from Jira API
   */
  async fetchJiraIssue(issueKey) {
    try {
      const data = await fetchJSON(`${API_BASE}/jira/fetch/${encodeURIComponent(issueKey)}`, {
        method: 'POST',
      });
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  },

  /**
   * Ingest raw Jira webhook payload
   */
  async submitJiraWebhook(payload) {
    try {
      const data = await fetchJSON(`${API_BASE}/jira/webhook`, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  },

  /**
   * Perform RAG retrieval for incident
   */
  async retrieveRAG(ragRequest) {
    try {
      const data = await fetchJSON(`${API_BASE}/rag/retrieve`, {
        method: 'POST',
        body: JSON.stringify(ragRequest),
      });
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  },

  /**
   * Execute multi-agent resolution pipeline on an incident
   */
  async processIncident(issueKey) {
    try {
      const data = await fetchJSON(`${API_BASE}/incidents/${encodeURIComponent(issueKey)}/process`, {
        method: 'POST',
      });
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  },

  /**
   * Submit Human Approval or Rejection decision
   * Triggers automatic Jira writeback & verification if decision status is 'approved'
   */
  async submitApproval(packageData, decisionInput) {
    try {
      const data = await fetchJSON(`${API_BASE}/approval/submit`, {
        method: 'POST',
        body: JSON.stringify({
          package: packageData,
          decision: decisionInput,
        }),
      });
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  },

  /**
   * Retry Jira writeback & verification for an already-approved incident
   * Reuses existing approved resolution without rerunning AI stages
   */
  async retryWriteback(issueKey) {
    try {
      const data = await fetchJSON(`${API_BASE}/incidents/${encodeURIComponent(issueKey)}/retry-writeback`, {
        method: 'POST',
      });
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  },
};

export default api;


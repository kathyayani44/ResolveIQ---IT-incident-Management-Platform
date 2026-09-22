/**
 * Isolated Sample Incident Dataset for UI demonstration and fallback testing
 * Purely declarative data matching backend CanonicalIncident and ApprovalPackage schemas.
 */

export const SAMPLE_INCIDENTS = [
  {
    id: "inc-1042-uuid",
    issue_key: "INC-1042",
    source: "jira",
    title: "Payment API latency spike & HTTP 504 gateway timeouts",
    description: "Checkout requests are timing out when attempting to authorize payments with Stripe gateway. Spike started at 12:35 PM UTC after database connection pool reached maximum utilization.",
    status: "in_progress",
    priority: "High",
    severity: "HIGH",
    category: "Payments",
    service: "PaymentGatewayService",
    reporter: "sarah.ops@resolveiq.io",
    assignee: "alex.dev@resolveiq.io",
    created_at: "2026-09-10T12:35:00Z",
    updated_at: "2026-09-10T12:48:00Z",
    current_stage: "approval",
    stage_status: "awaiting_approval",
    classification: {
      category: "Database & Microservices",
      service: "PaymentGatewayService"
    },
    rca: {
      status: "identified",
      root_cause: "Database connection pool exhaustion caused by unclosed connections during high-concurrency payment authorization retries.",
      evidence: [
        {
          chunk_id: "chk-postmortem-884",
          reason: "Matches connection leak pattern documented in Q3 Payment API postmortem."
        },
        {
          chunk_id: "chk-runbook-db-02",
          reason: "Active connection count reached 100 max limit at 12:36 PM."
        }
      ]
    },
    evidence: [
      {
        chunk_id: "chk-postmortem-884",
        text: "During high latency events, Payment Worker pool connections were left in idle-in-transaction state due to missing cleanup block in HTTP timeout handler.",
        source: "postmortems/2025-q3-payment-leak.md",
        document_type: "postmortem",
        score: 0.94
      },
      {
        chunk_id: "chk-runbook-db-02",
        text: "Connection Pool Runbook: When pool exhaustion occurs, increase max_connections parameter to 250 in RDS parameter group and execute connection reset script on payment nodes.",
        source: "runbooks/payment-db-pool-scaling.md",
        document_type: "runbook",
        score: 0.89
      },
      {
        chunk_id: "chk-sop-infra-101",
        text: "Emergency Scaling Procedure: Restart payment-worker-v2 pods sequentially after updating environment variables.",
        source: "sop/infra-pod-restart.md",
        document_type: "sop",
        score: 0.82
      }
    ],
    resolution: {
      recommendation: "Increase database connection pool capacity from 100 to 250 and trigger sequential pod restart for affected PaymentGateway workers.",
      steps: [
        "1. Apply updated pool limit configuration (max_connections=250) via Terraform / RDS parameter group.",
        "2. Execute graceful pod restart on `payment-worker-v2` deployments.",
        "3. Verify active connection metrics drop below 40% in Datadog dashboard.",
        "4. Confirm payment processing latency recovers below 200ms."
      ],
      risks: [
        "Temporary slight spike in RDS CPU utilization during worker reconnect phase."
      ],
      evidence: ["chk-postmortem-884", "chk-runbook-db-02"]
    },
    approval: {
      status: "pending",
      reviewer: null,
      timestamp: null,
      reason: null,
      feedback: null
    },
    jira_update: {
      status: "pending",
      updated_at: null,
      message: null
    }
  },
  {
    id: "inc-1041-uuid",
    issue_key: "INC-1041",
    source: "jira",
    title: "PostgreSQL master node replication lag exceeding SLA threshold",
    description: "Replication lag between primary DB node db-prod-01 and replica db-prod-02 breached 300 seconds, causing stale reads on customer dashboard.",
    status: "in_progress",
    priority: "Highest",
    severity: "CRITICAL",
    category: "Database",
    service: "PostgreSQL Cluster",
    reporter: "monitor-bot@resolveiq.io",
    assignee: "database-oncall@resolveiq.io",
    created_at: "2026-09-10T12:10:00Z",
    updated_at: "2026-09-10T12:45:00Z",
    current_stage: "resolution",
    stage_status: "processing",
    classification: {
      category: "Infrastructure & Storage",
      service: "PostgreSQL Cluster"
    },
    rca: {
      status: "identified",
      root_cause: "Heavy analytics query execution on primary node saturated WAL replication bandwidth.",
      evidence: []
    },
    evidence: [
      {
        chunk_id: "chk-db-wal-01",
        text: "WAL replication bottleneck runbook: Cancel long running query PIDs on master node using pg_cancel_backend().",
        source: "runbooks/postgres-replication.md",
        document_type: "runbook",
        score: 0.91
      }
    ],
    resolution: {
      recommendation: "Terminate long-running analytics queries on master DB node and dedicate replica db-prod-03 strictly to analytics workloads.",
      steps: [
        "1. Identify active long-running PID via `pg_stat_activity`.",
        "2. Terminate PID using `SELECT pg_terminate_backend(pid)`.",
        "3. Route analytics traffic to dedicated reporting replica."
      ],
      risks: [
        "In-flight analytics reports will need to be re-triggered."
      ],
      evidence: ["chk-db-wal-01"]
    },
    approval: {
      status: "pending",
      reviewer: null,
      timestamp: null,
      reason: null,
      feedback: null
    },
    jira_update: {
      status: "pending",
      updated_at: null,
      message: null
    }
  },
  {
    id: "inc-1038-uuid",
    issue_key: "INC-1038",
    source: "jira",
    title: "OAuth2 Token Validation failing for SSO enterprise users",
    description: "Users attempting login via Okta SSO receive 401 Unauthorized due to expired signing key cache in auth-service.",
    status: "resolved",
    priority: "Medium",
    severity: "MEDIUM",
    category: "Authentication",
    service: "AuthService",
    reporter: "support@resolveiq.io",
    assignee: "secops@resolveiq.io",
    created_at: "2026-09-10T11:20:00Z",
    updated_at: "2026-09-10T12:30:00Z",
    current_stage: "jira_update",
    stage_status: "completed",
    classification: {
      category: "Security & Auth",
      service: "AuthService"
    },
    rca: {
      status: "identified",
      root_cause: "JWKS key rotation occurred at Okta endpoint without cache invalidation signal.",
      evidence: []
    },
    evidence: [
      {
        chunk_id: "chk-auth-jwks",
        text: "Auth Service Runbook: Flush Redis key `auth:jwks:keys` to force immediate fetching of new public keys.",
        source: "runbooks/auth-jwks-flush.md",
        document_type: "runbook",
        score: 0.96
      }
    ],
    resolution: {
      recommendation: "Flush Redis JWKS key cache to refresh Okta public keys immediately.",
      steps: [
        "1. Flush Redis cache key `auth:jwks:keys`.",
        "2. Verify successful token verification in auth service logs."
      ],
      risks: ["None"],
      evidence: ["chk-auth-jwks"]
    },
    approval: {
      status: "approved",
      reviewer: "lead-engineer@resolveiq.io",
      timestamp: "2026-09-10T12:28:00Z",
      reason: "Verified solution matches Okta key rotation runbook.",
      feedback: "Looks good, proceeding with flush."
    },
    jira_update: {
      status: "completed",
      updated_at: "2026-09-10T12:30:00Z",
      message: "Jira issue updated with approved resolution steps and comment added."
    }
  }
];

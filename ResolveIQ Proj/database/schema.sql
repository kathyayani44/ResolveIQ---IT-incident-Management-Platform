-- ResolveIQ Supabase / PostgreSQL Schema Definition

-- Enable UUID extension if not enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table 1: raw_events (Stores raw un-normalized payloads from Jira or other webhook sources)
CREATE TABLE IF NOT EXISTS raw_events (
    id VARCHAR(64) PRIMARY KEY,
    source VARCHAR(50) NOT NULL DEFAULT 'jira',
    issue_key VARCHAR(100),
    raw_payload JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_raw_events_issue_key ON raw_events(issue_key);
CREATE INDEX IF NOT EXISTS idx_raw_events_received_at ON raw_events(received_at);

-- Table 2: incidents (Stores normalized CanonicalIncident records)
CREATE TABLE IF NOT EXISTS incidents (
    id VARCHAR(64) PRIMARY KEY,
    issue_key VARCHAR(100) UNIQUE NOT NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'jira',
    title TEXT NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    priority VARCHAR(50),
    severity VARCHAR(50),
    reporter VARCHAR(255),
    assignee VARCHAR(255),
    raw_event_id VARCHAR(64) REFERENCES raw_events(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_incidents_issue_key ON incidents(issue_key);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at);

-- Table 3: users (Stores ResolveIQ user accounts and credentials)
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(64) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    pwd_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);


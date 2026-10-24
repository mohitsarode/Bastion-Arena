"""SQLite connection management and schema migrations (DATABASE.md)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id TEXT PRIMARY KEY,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at REAL NOT NULL,
    FOREIGN KEY(tenant_id) REFERENCES tenants(tenant_id)
);

CREATE TABLE IF NOT EXISTS rounds (
    round_id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    state TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    created_at REAL NOT NULL,
    closed_at REAL,
    FOREIGN KEY(campaign_id) REFERENCES campaigns(campaign_id)
);

CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    round_id TEXT NOT NULL,
    iteration INTEGER NOT NULL CHECK (iteration >= 0),
    taxonomy_id TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at REAL NOT NULL,
    FOREIGN KEY(round_id) REFERENCES rounds(round_id)
);

CREATE TABLE IF NOT EXISTS evaluations (
    case_id TEXT PRIMARY KEY,
    refusal_score INTEGER NOT NULL CHECK (refusal_score BETWEEN 0 AND 2),
    bypass_score INTEGER NOT NULL CHECK (bypass_score BETWEEN 0 AND 2),
    harm_score INTEGER NOT NULL CHECK (harm_score BETWEEN 0 AND 2),
    confidence REAL NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),
    category TEXT NOT NULL,
    created_at REAL NOT NULL,
    FOREIGN KEY(case_id) REFERENCES cases(case_id)
);

CREATE TABLE IF NOT EXISTS ledger_events (
    sequence INTEGER PRIMARY KEY,
    event_id TEXT UNIQUE NOT NULL,
    tenant_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    actor TEXT NOT NULL,
    timestamp REAL NOT NULL,
    payload_hash TEXT NOT NULL,
    previous_hash TEXT NOT NULL,
    event_hash TEXT UNIQUE NOT NULL,
    signature_b64 TEXT NOT NULL,
    key_id TEXT NOT NULL,
    safe_metadata_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS capability_jtis (
    jti TEXT PRIMARY KEY,
    expires_at REAL NOT NULL,
    consumed_at REAL
);

-- Indexes defined in DATABASE.md
CREATE INDEX IF NOT EXISTS idx_campaigns_tenant ON campaigns(tenant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_rounds_campaign ON rounds(campaign_id, state);
CREATE INDEX IF NOT EXISTS idx_cases_round ON cases(round_id, status);
CREATE INDEX IF NOT EXISTS idx_ledger_case_seq ON ledger_events(case_id, sequence);
"""


class Database:
    """Manages SQLite database connections and schema setup."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = str(db_path)
        self._shared_conn: sqlite3.Connection | None = None
        if self.db_path == ":memory:":
            # Keep a persistent connection for in-memory databases so tables survive across queries
            self._shared_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._shared_conn.row_factory = sqlite3.Row
            self._shared_conn.execute("PRAGMA foreign_keys = ON;")
            self._shared_conn.executescript(SCHEMA_SQL)
            self._shared_conn.commit()
        else:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self.init_schema()

    def get_connection(self) -> sqlite3.Connection:
        if self._shared_conn is not None:
            return self._shared_conn
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_schema(self) -> None:
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    def close(self) -> None:
        if self._shared_conn is not None:
            self._shared_conn.close()
            self._shared_conn = None

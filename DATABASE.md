# Database Design — Bastion Arena

## Choice
Use SQLite for the single-host MVP. Keep database access behind `storage/` repositories so PostgreSQL can be added later. The cryptographic ledger is the integrity source of truth; reporting tables are queryable projections.

## Tables
- `tenants(tenant_id PK, created_at)`
- `campaigns(campaign_id PK, tenant_id FK, created_at, status)`
- `rounds(round_id PK, campaign_id FK, state, config_hash, created_at, closed_at nullable)`
- `cases(case_id PK, round_id FK, iteration, taxonomy_id, prompt_hash, status, created_at)`
- `evaluations(case_id PK/FK, refusal_score, bypass_score, harm_score, confidence, category, created_at)`
- `ledger_events(sequence PK, event_id UNIQUE, tenant_id, case_id, phase, actor, timestamp, payload_hash, previous_hash, event_hash UNIQUE, signature_b64, key_id, safe_metadata_json)`
- `capability_jtis(jti PK, expires_at, consumed_at)`

## Constraints and indexes
Scores must be integers 0–2; confidence is 0–1; iteration is non-negative. Index `(tenant_id, created_at)` for campaigns, `(campaign_id, state)` for rounds, `(round_id, status)` for cases and `(case_id, sequence)` for ledger events.

## Transactions and ownership
Resolve tenant from authenticated identity, not the request body. Insert case and submit event transactionally. Enforce one evaluation per case with a primary key. Serialize ledger append so concurrent writers cannot fork the chain. Every query to tenant-owned records scopes by trusted tenant ID.

## Sensitive data
Store hashes and normalized outcome by default. Raw prompts/outputs, if required for replay, must be in separately access-controlled storage with a retention policy. Never store provider secrets or private signing keys in SQLite.

## Migrations and recovery
Use versioned schema migrations or versioned SQL scripts. Back up the database before migrations. Verify ledger hashes/signatures/links before evidence finalization. Modification, deletion and reordering of events must fail verification.

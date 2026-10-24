# API Contract — Bastion Arena

Base prefix: `/api/v1`. Use JSON. Hardened mode uses HTTPS and workload identity; local fake mode may bind only to loopback.

## Public/Red-facing endpoints
- `GET /health/live` — process liveness.
- `GET /health/ready` — readiness of config, writable ledger, required providers.
- `POST /rounds` — create authorized round.
- `POST /rounds/{round_id}/cases` — submit a bounded case.
- `GET /cases/{case_id}/result` — retrieve normalized result if the trusted tenant owns the case.
- `POST /evidence/{round_id}/finalize` — close eligible round, verify ledger and sign manifest.
- `GET /evidence/{round_id}/manifest` — get authorized public-safe manifest.

## Internal-only endpoints
- `POST /internal/blue/precheck`
- `POST /internal/blue/postcheck`
- `POST /internal/evaluator/score`
- `POST /internal/tools/{tool_name}`

Internal endpoints are not exposed on public ports. They require authenticated service identity. A caller-supplied role header alone is never authentication.

## Example case input
```json
{
  "case_id": "case-001",
  "iteration": 0,
  "prompt": "synthetic test prompt",
  "objective": "evaluate refusal behavior",
  "taxonomy_id": "jailbreak"
}
```

## Example normalized response
```json
{
  "case_id": "case-001",
  "status": "uncertain",
  "refusal_score": 1,
  "bypass_score": 0,
  "harm_score": 0,
  "latency_bucket_ms": 500,
  "evaluator_confidence": 0.72
}
```

Red must never receive raw model output, Blue rule names/private thresholds, evaluator system prompt/private rationale, signing keys, or private ledger metadata.

## Validation
Use strict Pydantic contracts, maximum prompt/output size, bounded case count/iteration, enums for status/phase/category, nonce/replay protection, trusted role/tenant/capability checks, budgets, timeouts and rate limits.

## Error envelope
```json
{"error":{"code":"BUDGET_EXCEEDED","message":"Case budget exhausted","request_id":"req-123"}}
```

Error codes: `AUTH_FAILED`, `CAPABILITY_DENIED`, `TENANT_MISMATCH`, `INVALID_PHASE`, `REPLAY_DETECTED`, `BUDGET_EXCEEDED`, `INPUT_TOO_LARGE`, `MODEL_TIMEOUT`, `EVALUATOR_INVALID_OUTPUT`, `LEDGER_WRITE_FAILED`, `LEDGER_VERIFY_FAILED`, `ROUND_CLOSED`, `INTERNAL_ERROR`. Never return stack traces, credentials, host paths, or private policy internals.

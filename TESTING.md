# Testing Strategy

## Unit tests
- Pydantic required fields, enums, forbidden fields and bounds
- state-machine allowed/forbidden transitions
- config precedence and invalid config
- budget reservation/concurrency
- deterministic Red mutation path and size bounds
- Blue detection/redaction/fallback
- evaluator JSON parsing, wrong case ID and malformed-output fallback
- ledger canonicalization/hash/signature/chain verification
- latency bucket boundaries

## Integration tests
- one whole case through the Arbiter
- Blue `blocked=true` still follows the configured internal shadow path
- Red response excludes raw model output and private diagnostics
- Evaluator sees one bounded case only
- ledger event order is durable
- evidence manifest validates
- provider/evaluator/Blue failures do not become automatic safe results

## Security tests
- Red cannot reach Blue or MUT directly
- Blue cannot reach Red or MUT directly
- no untrusted service mounts Docker socket
- no privileged or host-networked untrusted service
- wrong role/tenant/capability rejected
- replay rejected
- ledger mutation, deletion and reordering detected
- tool allow-list and quota enforced
- synthetic canary leakage test
- timing-only inference experiment with reported uncertainty

## Test rules
Automated tests use deterministic fake providers and require no paid API or model download. External provider tests must be separately marked optional. A Python mock does not prove network isolation; network claims require real container tests.

## Commands
```bash
python -m compileall src tests
pytest -q
ruff check .
ruff format --check .
docker compose config
```

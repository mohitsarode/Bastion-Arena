# Security Model — Bastion Arena

## Assets
Red private strategy; Blue rules and diagnostics; MUT input/output and transient state; Evaluator prompt/state; tenant boundaries; provider credentials; capability tokens; mTLS keys; signing keys; ledger and evidence; host/runtime resources.

## Trust assumptions
The single-host MVP trusts the host kernel and container runtime. It does not claim resistance to a compromised host/hypervisor or malicious administrator. LLMs are untrusted decision-support components, not enforcement mechanisms.

## Required boundaries
- Red cannot directly reach Blue, MUT, evaluator internals, host resources, or other tenants.
- Blue cannot access Red-private state or contact MUT directly; Arbiter mediates checks and inference.
- Evaluator receives one case at a time and no private agent state.
- MUT has no host path, Docker socket, production data, provider key, or signing key access.
- Tool calls go through an allow-listed gateway with per-case limits.
- Red receives normalized feedback only.
- Ledger verifier recomputes event hashes from canonical fields, verifies signatures and chain links.

## Threat-to-control map
| Threat | Control |
|---|---|
| Cross-cell movement | separate containers/private networks + active connectivity tests |
| Prompt injection | role-local system prompts, schema checks, least privilege; prompt alone is not a boundary |
| Tool abuse | tool gateway, capability check, allow-list, quotas |
| Canary leakage | synthetic canaries, output scan/redaction and tests |
| Timing inference | shadow execution + response bucketing + statistical validation; does not prove elimination |
| Replay | unique case IDs, nonce/JTI store, round/phase checks |
| Ledger tampering | canonical hashing, Ed25519 signatures, previous-hash chain and independent verifier |
| Resource exhaustion | size/time/concurrency/CPU/memory/PID budgets |
| Provider outage | bounded retries and explicit error result |
| Malformed evaluator output | strict Pydantic parsing, sanity checks, clearly marked fallback |

## Scope boundary
Tests target synthetic/local benchmark applications only. No real third-party targets, production data, external scanning, host access or cloud credentials are in scope.

## Honest reporting
Every control must be marked implemented-and-tested, implemented-not-tested, planned, or residual risk. Never present planned criteria as measured success.

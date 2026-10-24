# PRD — Bastion Arena

## Product
Bastion Arena is a zero-trust framework for testing a Model Under Test (MUT) with controlled adversarial cases while protecting private agent state and test evidence.

## Problem
A safety test is not trustworthy if Red attack details, Blue defense logic, model state, or audit evidence can leak or be tampered with during execution.

## Users
AI safety/red-team researchers; AI application and model teams; security engineers validating tool boundaries; competition judges seeking reproducible evidence.

## MVP requirements
1. Submit a bounded test case through the Arbiter.
2. Generate/mutate synthetic test cases with deterministic fallback.
3. Run Blue input checks and output checks/redaction.
4. Execute a deterministic fake MUT by default; optionally connect to local OpenAI-compatible inference.
5. Score the case with a neutral Evaluator and strict typed verdict.
6. Return normalized feedback only.
7. Store append-only, hash-linked events and Ed25519-signed evidence.
8. Independently verify the ledger and detect modification/deletion/reordering.
9. Provide a local no-paid-key smoke test.
10. Test permitted and prohibited container/network paths when separate containers are enabled.

## Non-functional requirements
Python 3.11+; strict input bounds; bounded retries/timeouts/budgets; secrets excluded from source control and prompts; observable failures; deterministic tests; honest security claims.

## Out of scope for MVP
Kubernetes, multi-host control plane, confidential computing, formal timing-side-channel elimination, verified KV-cache isolation, real customer data, live third-party targets, mandatory commercial APIs, premature adoption of multi-agent frameworks.

## Acceptance
See `IMPLEMENTATION_PLAN.md` and `TESTING.md`. The product is not complete until end-to-end fake mode, explicit failure paths, ledger tamper detection, normalized feedback, and actual isolation tests pass.

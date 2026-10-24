---
name: test-and-verify
description: Designs and runs deterministic tests for Bastion Arena features, failure paths, invariants and evidence integrity.
---

# Test and Verify

1. Read requirements and acceptance criteria first.
2. Prefer deterministic fake providers and temporary SQLite/filesystem paths.
3. Test success, boundaries, malformed input, timeout/failure and authorization denial.
4. Do not use paid API keys in automated tests.
5. For ledger tests, mutate, delete, insert and reorder events.
6. For network claims, test actual service reachability under Compose; mocks do not prove isolation.
7. Run the tests and report exact counts/results. Never delete or skip failing tests to get green CI.

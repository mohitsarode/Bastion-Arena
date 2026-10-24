---
name: feature-implementation
description: Implements one approved Bastion Arena milestone or scoped feature with tests and security review. Use for API, provider, agent, ledger, or backend changes.
---

# Feature Implementation

1. Read `AGENTS.md` and relevant canonical docs.
2. Inspect Git status, existing code, tests, dependencies and callers.
3. Confirm the task belongs to the active implementation milestone.
4. Present a concise approach, file list, contract impact, security risks and tests.
5. Implement the smallest cohesive change; avoid unrelated refactoring.
6. Add success, boundary, failure and authorization tests as appropriate.
7. Run compile, focused tests, lint, then full tests where practical.
8. Update docs and milestone status to reflect what is actually complete.
9. Report changed files, exact commands/results, limitations and follow-up tasks.
10. If source docs conflict or a security invariant is unclear, document a decision and stop rather than silently weakening the invariant.

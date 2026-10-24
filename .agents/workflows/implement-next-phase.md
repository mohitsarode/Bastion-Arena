---
title: Implement Next Approved Phase
description: Implements only the next incomplete phase and verifies it before further work.
---

1. Read `AGENTS.md` and relevant documents.
2. Inspect current code, tests, dependencies and Git status.
3. Identify the first incomplete phase in `IMPLEMENTATION_PLAN.md`.
4. Present approach, files and tests before editing.
5. Implement only that phase.
6. Add tests for success, malformed input, failure and relevant security boundaries.
7. Run `python -m compileall src tests`, focused tests, `pytest -q`, `ruff check .`, `ruff format --check .`, and `docker compose config` where applicable.
8. Fix failures instead of weakening checks.
9. Update docs with actual status and test results.
10. Report changes, commands/results and unverified assumptions. Do not start another phase in the same run.

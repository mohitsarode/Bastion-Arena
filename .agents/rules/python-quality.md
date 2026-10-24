---
trigger: glob
globs: "src/**/*.py, tests/**/*.py"
description: "Python typing, error handling, and test conventions for Bastion Arena code."
---

# Python Quality

- Python 3.11+; type hints on public interfaces.
- Keep functions focused; inject provider, storage, ledger and clock dependencies.
- Use Pydantic v2 contracts and reject unexpected fields where practical.
- No broad `except Exception: pass`; fallback behavior must be explicit and tested.
- All retries and timeouts are bounded.
- Unit tests use fake providers; no commercial API calls in default test suite.
- Every security boundary needs an allowed-path and denied-path test.
- Recompute ledger hashes from event fields; do not trust a stored hash alone.
- Run focused tests, then the full suite when practical.

# Bastion Arena

Zero-Trust Adversarial AI Safety Evaluation Framework.

Bastion Arena isolates adversarial Red Team attackers, Blue Team defenses, Neutral Evaluators, and Models Under Test (MUT) behind an in-process and network-isolated Arbiter security control plane.

Original design specifications are preserved immutable under `docs/reference/` and indexed in `docs/REFERENCE_INDEX.md`.

---

## Key Invariants

1. **Zero-Trust Information Hiding**: Untrusted Red workers receive only `NormalizedResponse` (status, categorical scores, latency bucket, evaluator confidence). Raw model tokens, Blue defense rule names, and Evaluator chain-of-thought rationale are strictly stripped.
2. **Cryptographic Append-Only Ledger**: All evaluation lifecycle events are signed with Ed25519 and chained via SHA-256 hashes. Independent verifier recomputes hashes from canonical unsigned fields (ADR-005).
3. **Shadow Execution Timing Governor**: When Blue defense blocks an attack prompt, Arbiter still runs the model in the background to normalize response latencies, neutralizing timing side-channels.
4. **Offline-First & Deterministic**: Full test suite runs 100% offline using `FakeProvider` without API keys or active internet access.
5. **No Silent Pass On Outage**: Model timeouts or network disconnects explicitly return `MODEL_TIMEOUT` (HTTP 504) via circuit breakers, never silently passing.

---

## Quickstart (Offline / Test Profile)

### 1. Installation
```bash
pip install -e .
```

### 2. Run Test Suite
```bash
python -m compileall src tests scripts
pytest -q
ruff check src tests scripts
ruff format --check src tests scripts
```

### 3. Verify Docker Compose Configuration
```bash
docker compose config --quiet
```

---

## Runtime Profiles

Bastion Arena supports three provider profiles in `config.yaml` or via environment variable `BASTION_PROVIDERS_MODE`:

### Profile 1: `fake` (Default / CI / Offline)
Uses deterministic in-memory `FakeProvider`. Requires zero external services or API keys.
```yaml
providers:
  mode: fake
```

### Profile 2: `ollama` (Local Open-Weights Model)
Runs against a local Ollama or llama.cpp instance via OpenAI-compatible endpoints with automated circuit breakers and retry policies:
```bash
# 1. Pull model in Ollama
ollama pull qwen3:8b

# 2. Run Bastion Arena with Ollama profile
export BASTION_PROVIDERS_MODE=ollama
```
Config in `config.yaml`:
```yaml
providers:
  mode: ollama

models:
  ollama:
    base_url: "http://localhost:11434/v1"
    model: "qwen3:8b"
    timeout_seconds: 45
```

### Profile 3: `openai_compatible_cloud` (Optional Cloud Gateway)
Connects to an external OpenAI-compatible inference gateway:
```yaml
providers:
  mode: openai_compatible_cloud

models:
  cloud:
    base_url: "https://api.openai.com/v1"
    model: "gpt-4o-mini"
    timeout_seconds: 45
```

---

## Standalone Ledger Integrity & Auditor Forensic Tools

### 1. Run Complete Offline Demo
Executes 5 benchmark test cases (benign, jailbreaks, DAN prompts, canary extraction), triggers shadow execution, and generates signed evidence manifest:
```bash
python scripts/run_demo.py
```

### 2. Auditor Forensic Console (Red vs Blue vs Evaluator)
Inspects the cryptographic evidence manifest and presents an auditor-grade forensic timeline detailing exactly what Red submitted, what Blue detected, and how the Neutral Evaluator scored:
```bash
python scripts/inspect_audit_trail.py --manifest demo_evidence_manifest.json
```

### 3. Cryptographic Tamper Detection Demonstration
Demonstrates 100% detection of in-place SQLite tampering, event deletion, event reordering, and forged digital signatures via ADR-005 canonical field recomputation:
```bash
python scripts/demo_tamper.py
```

### 4. Independent Ledger Verification CLI
An auditor can independently verify the cryptographic ledger without database access:
```bash
python scripts/verify_ledger.py --manifest demo_evidence_manifest.json
```
Performs 4 independent checks per ADR-005:
1. Strict integer sequence continuity
2. Previous-hash SHA-256 link validity
3. Recomputation of SHA-256 hash from canonical unsigned event fields
4. PyNaCl Ed25519 signature verification against public verify key

### 5. Security Isolation Scorecard
Runs automated verification of all 12 platform security controls:
```bash
python scripts/run_scorecard.py
```

### 6. Interactive Web Dashboard & Visual Auditor Console
Bastion Arena provides an offline-first, zero-dependency visual interface for live hackathon presentations:
- **Live Server**: Run `uvicorn bastion_arena.main:app --reload` and navigate to `http://127.0.0.1:8000/dashboard` or `http://127.0.0.1:8000/`.
- **Standalone Offline**: Double-click `dashboard.html` in any browser without needing Python or network connectivity.
- **Capabilities**:
  - **Multi-Agent Timeline**: Interactive comparison of what Red sees vs. Blue defense scans, shadow execution, and Evaluator verdicts.
  - **Cryptographic Ledger & Tamper Sandbox**: Visual DAG block explorer with interactive buttons to test ADR-005 tamper detection in real-time.
  - **Security Scorecard**: Visual 12-control Track 04 compliance matrix.

---

## Observability & Auditor Role

### How the Auditor Tracks What Red and Blue Did
In Bastion Arena, participants operate under zero-trust:
- **Red Team (Untrusted)**: Submits test cases via `POST /api/v1/rounds/{round_id}/cases`. Receives only `NormalizedResponse` containing categorical scores (`refusal`, `bypass`, `harm`), high-level status (`ALLOW`, `BLOCK`, `ERROR`), and quantized latency. Red never sees raw model output, Blue filter pattern names, or Evaluator reasoning.
- **Blue Defense**: Scans input prompts using attack signatures and scrubs sensitive tokens/credentials from responses. If an attack signature matches, Blue marks the input `BLOCKED`.
- **Neutral Evaluator & Arbiter**: Runs shadow execution of the Model Under Test (MUT) to neutralize timing side-channels, scores the result using a neutral rubric, and writes an Ed25519-signed event to the append-only SHA-256 hash-chained ledger.
- **Auditor (Privileged)**: Uses read-only capability `evidence:verify` or the forensic console (`scripts/inspect_audit_trail.py`) to inspect the entire chronological event sequence, comparing Red's inputs against Blue's matched filters and Evaluator ground truth.

### How to View Application Logs
Bastion Arena employs structured contextual logging with automatic canary scrubbing:
1. **Live Console Stream**: Every round, case, and component emits prefixed structured log events:
   - `[RED]` — Case submission, taxonomy, and sanitized payload hash.
   - `[BLUE]` — Input scan result, regex matches, and output redactions.
   - `[MUT]` — Model Under Test invocation (including shadow execution).
   - `[EVALUATOR]` — Ground truth scoring and refusal/bypass assessment.
   - `[ARBITER]` — Latency quantization, budget reservations, and state machine transitions.
   - `[LEDGER]` — Canonical hashing, Ed25519 digital signing, and chain link recording.
2. **Correlation IDs**: All log entries carry `tenant_id`, `round_id`, and `case_id` for end-to-end tracing across workers.
3. **Privileged API Endpoint**: Auditors can query `GET /api/v1/evidence/{round_id}/audit-trail` with an auditor token to inspect the full timeline programmatically. Red workers attempting to query this endpoint are rejected with HTTP 403 `CAPABILITY_DENIED`.

---

## Container Hardening & Multi-Cell Topology

When running in containerized environments, `docker-compose.yml` provisions 4 isolated bridge networks:
- `net_red`: Red worker $\leftrightarrow$ Arbiter
- `net_blue`: Blue worker $\leftrightarrow$ Arbiter
- `net_model`: Model worker $\leftrightarrow$ Arbiter
- `net_eval`: Evaluator worker $\leftrightarrow$ Arbiter

All containers run with:
- Non-root user (`user: "10001:10001"`)
- All Linux capabilities dropped (`cap_drop: [ALL]`)
- Privilege escalation disabled (`no-new-privileges: true`)
- Read-only root filesystems (`read_only: true`)
- Dangerous syscalls blocked via Seccomp filter (`infra/docker/seccomp_profile.json`)
- Zero access to Docker socket (`/var/run/docker.sock` strictly prohibited)

# Preflight: Live Demo Runbook & Evaluator Q&A

This runbook guides presenters through conducting live evaluations of Preflight, including a 60-second elevator pitch, a 3-minute comprehensive walkthrough, failure fallback procedures, and technical Q&A preparation.

---

## 1. Quick Start: Launching the Demo Environment

### Step 1: Verify Environment & Launch Server
From the repository root:
```bash
# 1. Activate virtual environment
source .venv/bin/activate  # or .\.venv\Scripts\Activate.ps1 on Windows

# 2. Start the FastAPI backend and mounted UI (Port 8000)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
Open your browser to: **`http://localhost:8000`**

### Step 2: Verification Checklist Before Presenting
- [ ] UI header displays `Kestrel Pay Pipeline Gate` and bank `kestrel-pay`.
- [ ] Mode badge shows `Mode: Cached (Fast)` or `Mode: Live (Hindsight + Groq)`.
- [ ] Headline metrics card displays `4 / 9` repeat incidents caught.
- [ ] Confusion matrix card loads both Memory-On and Memory-Off tables.
- [ ] Preset buttons (`dep-131`, `dep-111`, `dep-101`, `dep-223`, `dep-164`) update the Gate Simulator instantly.

---

## 2. 60-Second Elevator Pitch

**Goal**: Deliver a punchy, memorable demonstration of persistent CI memory in one minute.

1. **The Hook (0:00 - 0:15)**:
   > *"Every team suffers from repeat outages. A developer tightens a timeout on Friday afternoon; all unit tests pass; it merges; production crashes. The exact same thing happened four months ago, but the CI pipeline had zero memory of it."*

2. **The Demo (0:15 - 0:40)**:
   > *(Click preset button `dep-131` on the console)*
   > *"Look at this release on payments-api. Without memory, the pipeline gives it a green PASS (Risk: 0.20). But toggle to Memory-On: Preflight queries Hindsight persistent memory at T_deploy. It recalls outage dep-101, detects the matching failure mechanism, and blocks the merge with exit code 1. Best of all, it provides the verified fix: Runbook RB-PAY-04."*

3. **The Proof (0:40 - 1:00)**:
   > *(Scroll to Headline Metrics)*
   > *"Across 150 historical releases, memory caught 4 of 9 repeat outages compared to 1 of 9 without memory, with zero increase in false alarms on healthy code. Preflight turns passive CI gates into an operational immune system."*

---

## 3. 3-Minute Comprehensive Demo Script

**Goal**: Walk evaluators through problem setup, live gate simulator, empirical backtest results, and CI workflow integration.

### Phase 1: Context & Problem (0:00 – 0:45)
- Open the GitHub repository README.
- Explain the persona: Kestrel Pay, a high-volume fintech processing real-time payments across 16 microservices.
- Point out the limitation of modern CI/CD: unit tests and linters only check syntax and isolated logic. They cannot anticipate production runtime interactions or remember past post-mortems.

### Phase 2: Live Gate Simulation (0:45 – 1:45)
- Navigate to `http://localhost:8000`.
- **Demonstrate Failure Pattern P1 (`dep-131`)**:
  - Click preset `dep-131 (Payments Friday Config)`.
  - Contrast **Memory-Off** (`PASS`, Risk 0.20, "Modest configuration adjustment") against **Memory-On** (`BLOCK`, Risk 0.75, "Connection pool exhaustion under peak load").
  - Point out the **Grounded Citations**: Preflight cites memory from `dep-101` and attaches `Runbook RB-PAY-04`.
- **Demonstrate Safe Release (`dep-111`)**:
  - Click preset `dep-111 (Healthy Payment Service Logic)`.
  - Show that both Memory-On and Memory-Off evaluate this as `PASS` (Risk 0.15). Memory does not create paranoia.
- **Demonstrate Decoy Pattern (`dep-223`)**:
  - Click preset `dep-223 (Decoy Auth Config Update)`.
  - Show how `disposition_skepticism=4` avoids confusing benign auth parameter changes with token migration outages.

### Phase 3: Empirical Replay & Metrics (1:45 – 2:30)
- Scroll to the **Headline Metrics** and **Confusion Matrix** cards:
  - **Repeat Outage Recall**: Highlight 4/9 (Memory-On) vs 1/9 (Memory-Off).
  - **Healthy Deploys**: Highlight 5/111 false alarms on both arms (no false positive explosion).
  - **Sample Size Transparency**: Point to the callout banner ($N=9$). Emphasize that we report honest, unhyped raw counts.
- Scroll to the **Learning Curve Trajectory**:
  - Explain why F1 starts high (1.0) when the first repeat incident is blocked, and gradually stabilizes around 0.44 as dozens of normal releases dilute the precision metric.

### Phase 4: CI/CD Pipeline Integration (2:30 – 3:00)
- Open `docs/ci/preflight_gate.yml`.
- Show how `preflight gate` runs in GitHub Actions:
  ```yaml
  - name: Evaluate Release Safety Gate
    run: |
      python -m backend.agent.gate --commit ${{ github.sha }} --pr ${{ github.event.pull_request.number }}
  ```
- Highlight the closed feedback loop: after deployment, `POST /outcome` retains the observed health, stack trace, and resolution runbook into Hindsight, updating the memory bank for future releases.

---

## 4. Failure Fallback Procedures

If network connectivity degrades, or if upstream external APIs (Groq or Vectorize Hindsight) experience latency or rate limits during a live demo:

### Fallback Option A: Seamless Cached Mode (Default)
Preflight includes an automated, offline-resilient replay engine (`DEMO_MODE=cached`):
1. In the terminal, start the server with:
   ```bash
   export DEMO_MODE=cached  # or $env:DEMO_MODE="cached" in PowerShell
   uvicorn backend.app.main:app --port 8000
   ```
2. The UI header will display a purple **Mode: Cached (Fast)** badge.
3. Every preset, gate evaluation, and replay metric is served instantly from local validated replay records (`data/results/replay.json`) without making external API calls.

### Fallback Option B: Pre-Baked Offline CLI Verification
If the browser or local web server is inaccessible, run the pre-baked verification test directly in your terminal:
```bash
python -m pytest backend/tests/test_memory_and_leakage.py -v
```
This demonstrates zero-leakage whitelist enforcement, retain idempotency, and June 2026 event timestamp preservation in 12 seconds.

---

## 5. Evaluator Q&A Preparation

### Q1: How do you guarantee the agent doesn't "cheat" by looking at future incidents during historical backtesting?
> **Answer**: *"We enforce zero leakage through two strict architectural barriers. First, the agent's evaluation function `get_predeploy_proposal()` enforces a whitelist of pre-deploy fields only (service, diff, author, timestamp). Incident fields like root cause, stack traces, and detected time are strictly inaccessible. Second, when querying Hindsight, we pass `query_timestamp = T_deploy`. Hindsight filters out any memory stored after that exact minute. Our automated test suite `test_memory_and_leakage.py` asserts this property programmatically."*

### Q2: Why did the rolling F1 score decline from 1.0 to 0.44 over the 150 releases?
> **Answer**: *"That decline represents real-world operational base rates, not a degradation in capability. In a production pipeline, 80–90% of releases are healthy. Early in the backtest, when the first planted repeat incident occurred, precision was 1.0. As dozens of healthy releases passed, even a small number of false alarms (5 out of 111 healthy releases) naturally dilutes the precision denominator ($TP / (TP + FP)$). Showing this full trajectory honestly is much more valuable for platform teams than claiming artificial 100% precision."*

### Q3: How is Hindsight persistent memory different from a standard RAG vector database?
> **Answer**: *"Standard RAG has three fatal flaws in DevOps: no temporal anchoring (leading to look-ahead bias), no cognitive disposition (causing semantic hallucinations between unrelated config keys), and no reflection engine. Hindsight provides first-class temporal filtering (`query_timestamp`), behavioral directives (`disposition_skepticism=4`), and multi-incident reflection that synthesizes systemic failure modes into concrete runbooks."*

### Q4: Why did both arms flag 5 out of 111 healthy releases?
> **Answer**: *"In complex infrastructure, certain healthy PRs contain changes that look inherently risky—like updating core database migration schemas or major dependency bumps. The agent flagged those with an abundance of caution, but crucially, memory did not introduce additional paranoia. Both Memory-On and Memory-Off had the exact same 5/111 false alarm rate, proving that memory enhances incident detection without spamming developers with false warnings."*

### Q5: How do you determine the PASS, WARN, and BLOCK risk thresholds?
> **Answer**: *"Preflight maps normalized risk scores to pipeline exit codes:
> - `Risk >= 0.60` (or `HIGH`): **`BLOCK`** (Exit Code 1). Merge is prevented; requires on-call review and runbook compliance.
> - `0.35 <= Risk < 0.60` (or `MEDIUM`): **`WARN`** (Exit Code 0). Merge is allowed, but an operational warning is posted on the PR.
> - `Risk < 0.35` (or `LOW`): **`PASS`** (Exit Code 0). Green light to merge.*
> *These thresholds were calibrated against the 150-deploy dataset to balance incident prevention against developer velocity."*

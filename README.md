# Preflight: Autonomous Release Gate with Persistent Memory

> Autonomous CI/CD release-safety agent for fintech **Kestrel Pay**, powered by Vectorize's **Hindsight** memory system and Groq open-weights LLMs.

---

## Overview

Preflight sits at the CI/CD pipeline gate between pull request approvals and production deployment. By retaining past deployments, outages, root-cause analyses, and mitigation runbooks in persistent memory, Preflight intercepts repeat failure patterns before they reach production.

```
       Incoming PR / Deploy Proposal
                    │
                    ▼
     ┌──────────────────────────────┐
     │  get_predeploy_proposal()    │  ◄── Strict Sanitization (Zero Leakage)
     └──────────────┬───────────────┘
                    │
                    ▼
     ┌──────────────────────────────┐
     │  Hindsight Memory Recall     │  ◄── Query-anchored to exact deploy time
     └──────────────┬───────────────┘
                    │
                    ▼
     ┌──────────────────────────────┐
     │  Risk Briefing Agent (Groq)  │  ◄── Model Consistency (Temp 0.0)
     └──────────────┬───────────────┘
                    │
                    ▼
       Gate Decision & Actions
       ├── PASS  (Risk < 0.35,  Exit 0)
       ├── WARN  (0.35 - 0.59,  Exit 0)
       └── BLOCK (Risk >= 0.60, Exit 1)
```

---

## Gate Thresholds & Score Clamping

To eliminate contradictory outputs between qualitative classifications and numeric risk scores, Preflight enforces boundary clamping:

| Classification | Score Range | Gate Action | CI Exit Code | Pipeline Behavior |
| :--- | :---: | :---: | :---: | :--- |
| **LOW** | `0.00 – 0.34` | **`PASS`** | `0` | Automated pass-through; deployment proceeds. |
| **MEDIUM** | `0.35 – 0.59` | **`WARN`** | `0` | Advisory warning; publishes risk summary and checklists. |
| **HIGH** | `0.60 – 1.00` | **`BLOCK`** | `1` | Halts release; requires on-call remediation and rollback review. |

### Score Clamping Invariants:
- If the agent classifies risk as `HIGH` but outputs a raw score $< 0.60$, the score is clamped to `0.75`.
- If the agent classifies risk as `LOW` but outputs a raw score $> 0.40$, the score is clamped to `0.20`.
- All cited memory IDs are validated against recalled evidence; hallucinated citations are stripped automatically.

---

## Quickstart

Preflight requires Python 3.11+ (tested on Python 3.14.7; verified compatible with Python 3.11, 3.12, 3.13, and 3.14). No `make` or C/C++ compiler is required.

### 1. Clone & Set Up Virtual Environment

**Windows (PowerShell):**
```powershell
git clone https://github.com/kestrel-pay/preflight.git
cd preflight
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux (Bash):**
```bash
git clone https://github.com/kestrel-pay/preflight.git
cd preflight
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit .env to add your API keys:
# HINDSIGHT_API_KEY=hsk_...
# GROQ_API_KEY=gsk_...
```

*(Note: For instant offline evaluation without external API keys, you can run in cached demo mode as shown below).*

### 3. Launch Preflight Console & API

```powershell
# Windows PowerShell (Cached Offline Mode - instant, no keys needed):
$env:DEMO_MODE="cached"
python -m uvicorn backend.app.main:app --port 8000

# macOS / Linux (Cached Offline Mode):
export DEMO_MODE="cached"
python3 -m uvicorn backend.app.main:app --port 8000
```
Open **`http://localhost:8000`** in your browser to view the interactive console.

### 4. Run Test Suite

```bash
python -m pytest backend/tests/ -v
```

---

## Empirical Results & Limitations

All metrics below are derived directly from the canonical 150-deployment chronological backtest file: [`data/results/replay_run1_mixed.json`](data/results/replay_run1_mixed.json) (mirrored in [`data/results/replay.json`](data/results/replay.json)).

### Headline Metric: Repeat Incident Prediction

| Evaluation Cohort | Memory-On (Preflight) | Memory-Off (Stateless Baseline) |
| :--- | :---: | :---: |
| **Repeat Incidents Flagged HIGH** | **4 / 9** | **1 / 9** |
| False Alarms on Healthy Releases | 5 / 111 | 5 / 111 |
| Planted Decoy Deploys Flagged HIGH | 1 / 11 | 0 / 11 |
| Safe Pattern-Matches Flagged HIGH | 1 / 2 | 0 / 2 |
| CI Build Failures Flagged HIGH | 2 / 22 | 3 / 22 |
| Background Incidents Flagged HIGH | 0 / 3 | 0 / 3 |

### Confusion Matrix (Positive Class = Incident, Risk >= 0.5)

Evaluated across the 128 production deployment rows (17 incidents + 111 healthy releases; 22 build failures excluded from binary incident classification as build failures occur before production deployment):

- **Memory-On**: True Positives (TP) = 8, False Positives (FP) = 11, False Negatives (FN) = 9, True Negatives (TN) = 100.
  - Precision: `8 / (8 + 11) = 42.1%`
  - Recall: `8 / (8 + 9) = 47.1%`
- **Memory-Off**: True Positives (TP) = 9, False Positives (FP) = 16, False Negatives (FN) = 8, True Negatives (TN) = 95.
  - Precision: `9 / (9 + 16) = 36.0%`
  - Recall: `9 / (9 + 8) = 52.9%`

### Explicit Empirical Limitations

1. **Synthetic Operational History**: The 150-deployment dataset models real-world fintech traffic patterns but was synthetically generated to provide reproducible ground-truth labels for P1–P6 failure modes.
2. **Small Sample Size ($N=9$)**: Across 150 deployments, exactly 9 repeat occurrences took place across planted patterns P1–P4 and P6. While Memory-On caught 4 compared to 1 for Memory-Off, 9 data points represent an initial empirical signal, not a definitive statistical ceiling.
3. **Open-Weights Model Allocation**: Both arms utilized open-weights LLMs with automatic quota-aware fallback (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`) under Groq daily token constraints. Model used and latency are logged per row.
4. **All-Healthy Baseline**: A trivial model predicting "healthy" on every release achieves `111 / 150 = 74.0%` overall accuracy (`88.7%` if build failures are grouped with non-incidents), which is why accuracy is omitted from headline reporting in favor of precision and repeat incident recall.
5. **No Unsupported Claims**: All findings are reported strictly as raw counts (e.g. 4/9 vs 1/9). Preflight avoids marketing percentages ("4x", "+300%") or speculative causal narratives.

---

## Interactive UI Console Walkthrough

Preflight serves an interactive developer console at `http://localhost:8000` with 5 primary screens:

### 1. Pipeline Gate Simulator
Select any deployment proposal or test preset (`dep-131`, `dep-111`, `dep-101`, `dep-223`, `dep-164`) to view real-time gate evaluation, risk score, classification, and grounded runbooks.

### 2. Before / After Memory Comparison
Side-by-side comparison illustrating how the Memory-On agent catches repeat failure mechanisms (e.g. connection pool exhaustion on Friday afternoon) with grounded runbook citations (`RB-PAY-04`), while the Memory-Off baseline evaluates the PR in isolation and grants a dangerous green PASS.

### 3. Post-Incident Feedback & Runbook Ingestion Form
On-call engineers can submit new post-mortems (service, severity, error logs, root cause, and verified runbook ID). Preflight ingests the outcome into Hindsight memory via `POST /api/outcome`, immunizing the pipeline gate against future occurrences.

### 4. Empirical Learning Curve
Interactive Recharts time-series plotting rolling F1, precision, and recall trajectories across all 150 releases. Illustrates the natural operational curve: an initial spike to 1.0 when the first recurring outage is blocked, stabilizing around 0.44 as healthy releases accumulate.

### 5. Systemic Reflected Patterns
Visual cards displaying failure mechanisms synthesized by Hindsight reflection (`reflect()`):
- **P1**: Friday Afternoon Payments Gateway Timeout (`RB-PAY-04`)
- **P2**: Auth Service Token Migration Invalidation (`RB-AUTH-01`)
- **P3**: Database Connection Pool Starvation (`RB-DB-02`)
- **P4**: Notification Worker Webhook Flooding (`RB-NOTIF-03`)
- **P6**: Inverted Gateway Dependency Timeout Cascades (`RB-GATEWAY-05`)

---

## Repository Structure

```
preflight/
├── backend/
│   ├── agent/           # Preflight Risk Briefing agent & schema
│   ├── app/             # FastAPI production service (POST /gate, /brief, /outcome)
│   ├── memory/          # Hindsight persistent memory store & retry layer
│   ├── replay/          # Chronological backtest simulation engine
│   └── tests/           # Pytest test suite (leakage, idempotency, API endpoints)
├── data/
│   ├── raw/             # Synthetic history (150 deploys) and ground truth
│   └── results/         # replay.json, replay_run1_mixed.json, patterns cache
├── docs/ci/             # Production GitHub Actions release gate specifications
├── frontend/            # React + Vite + Tailwind + Recharts console
└── DECISIONS.md         # Architectural invariants & metric definitions
```

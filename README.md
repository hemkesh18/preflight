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

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

## Operating Modes: `DEMO_MODE=cached|live`

Preflight supports two operational modes via environment variable:
- `DEMO_MODE=live` *(default)*: Issues real-time queries to Hindsight Cloud and Groq. If upstream API timeouts or quota limits occur, it gracefully serves cached results with an in-UI warning banner.
- `DEMO_MODE=cached`: Delivers instant, deterministic results from the 150-deployment replay telemetry without external API round-trips.

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

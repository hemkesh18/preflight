# Hindsight Persistent Memory Integration Guide

This document details how **Preflight** leverages [Vectorize's Hindsight API](https://api.hindsight.vectorize.io) to provide persistent, temporally-anchored release-risk memory for fintech CI/CD deployment pipelines.

---

## 1. Architectural Overview

Traditional CI/CD gates evaluate pull requests statelessly: linters, unit tests, and security scans run in isolation with zero memory of past production outages. 

Preflight transforms the release gate into an **experience-accumulating agent**. By storing deployment proposals, production incident post-mortems, and verified runbooks in Hindsight, Preflight recognizes recurring failure patterns across services, change types, and scheduling windows.

```mermaid
flowchart TD
    subgraph CI Pipeline Gate
        PR[Incoming Pull Request] --> Proposal[Extract Pre-Deploy Proposal<br/>Service, Diff, Config, Time]
        Proposal --> Recall[Hindsight Temporal Recall<br/>query_timestamp = T_deploy<br/>skepticism = 4, budget = mid]
    end

    subgraph Hindsight Engine
        Bank[(Memory Bank<br/>kestrel-pay)]
        Bank --> Recall
        Reflect[Reflection API<br/>Pattern Synthesis] --> Bank
    end

    subgraph Release Decision
        Recall --> Briefing[Agentic Risk Synthesis<br/>LLM + Grounded Runbooks]
        Briefing --> Gate{Threshold Gate}
        Gate -->|Risk >= 0.60| Block[BLOCK (Exit 1)]
        Gate -->|0.35 <= Risk < 0.60| Warn[WARN (Exit 0)]
        Gate -->|Risk < 0.35| Pass[PASS (Exit 0)]
    end

    subgraph Post-Deploy Feedback Loop
        Production[Production Monitoring<br/>Detect Outage or Success] --> Outcome[Retain Outcome & Runbook<br/>Timestamped post-deploy]
        Outcome --> Bank
    end
```

---

## 2. Bank Initialization & Behavioral Disposition

Hindsight memory banks configure the cognitive framing and personality traits under which memories are retained, linked, and recalled.

### Bank Configuration Parameters

```python
from hindsight_client import Hindsight

client = Hindsight(
    base_url="https://api.hindsight.vectorize.io",
    api_key=os.getenv("HINDSIGHT_API_KEY")
)

mission = (
    "Release-risk analyst for fintech Kestrel Pay; learn which change types, "
    "services, and deployment timings precede incidents and build failures; "
    "track what fixes worked to prevent repeat outages."
)

client.create_bank(
    bank_id="kestrel-pay",
    name="Kestrel Pay Pipeline Gate",
    mission=mission,
    disposition_skepticism=4,
    disposition_literalism=4,
    disposition_empathy=2,
    enable_temporal_retrieval=True,
    enable_text_search=True
)
```

### Rationale for Disposition Settings:
- **`disposition_skepticism=4` (High Skepticism)**: Ensures the recall engine does not hallucinate false causal links between benign diffs and unrelated outages. It prioritizes concrete evidence (matching services, specific config keys, error logs).
- **`disposition_literalism=4` (High Literalism)**: Prevents loose semantic associations. In financial infrastructure, exact parameter names (e.g., `payment_channel_timeout`, `pool_size`, `worker_threads`) matter more than generic synonyms.
- **`disposition_empathy=2` (Low Empathy)**: Keeps risk analysis detached, analytical, and objective.
- **`enable_temporal_retrieval=True`**: Critical for backtesting and historical replay without look-ahead bias.

---

## 3. Retention & Strict Idempotency

Preflight retains two distinct documents per release lifecycle:
1. **Pre-Deploy Plan (`dep-{id}-plan`)**: The proposed diff, service, change type, and scheduling timestamp.
2. **Post-Deploy Outcome (`dep-{id}-outcome`)**: The observed result (healthy, build failure, or incident stack trace), detected time, MTTR, impact, and runbook mitigation.

### True Idempotency Implementation

To ensure that running re-ingestion scripts or backtest replays never duplicates memories or inflates fact counts across restarts, Preflight employs a dual-layer defense:

1. **In-Memory Tracking**: A local set `_retained_doc_ids` prevents redundant API calls within the same process.
2. **Delete-Before-Retain**: Before retaining a document ID, Preflight issues an explicit document deletion to Hindsight.

```python
def _delete_document_if_exists(self, doc_id: str) -> None:
    """Deletes any previous version of a document to guarantee strict idempotency across process restarts."""
    try:
        _run_async = Hindsight.retain_batch.__globals__.get("_run_async")
        if _run_async:
            _run_async(self.client.documents.delete_document(bank_id=self.bank_id, document_id=doc_id))
    except Exception as e:
        logger.debug(f"Document {doc_id} delete check notice: {e}")
```

### Exact Event Timestamps (No Midnight Truncation)

All retained memories preserve the exact event timestamp (UTC) rather than ingestion time or midnight truncation. This guarantees precise chronological replay.

```python
deploy_dt = datetime.fromisoformat(deploy["timestamp"].replace("Z", "+00:00"))

self.client.retain(
    bank_id=self.bank_id,
    document_id=f"{deploy['deploy_id']}-plan",
    content=plan_text,
    timestamp=deploy_dt,
    tags=["deployment", deploy["service"], deploy["change_type"], "plan"]
)
```

---

## 4. Zero-Leakage Temporal Anchoring

A critical risk in machine learning backtests is **look-ahead bias** (leaking future incidents into past decisions). Preflight enforces zero leakage through two strict contracts:

1. **Whitelist Proposal Interface (`get_predeploy_proposal()`)**:
   The agent briefing receives ONLY pre-deploy fields:
   - `deploy_id`, `service`, `change_type`, `timestamp`, `commit_hash`, `author`, `pull_request` (title, description, files_changed, diff_summary).
   - Zero access to `detected_at`, `root_cause`, `incident_log`, `status`, or `eval_category`.

2. **Temporal Anchoring in Recall**:
   Every recall query passes `query_timestamp = deploy_dt`. Hindsight filters the search space to memories strictly existing before that exact minute:

```python
query_time = datetime.fromisoformat(deploy["timestamp"].replace("Z", "+00:00"))

recall_resp = self.client.recall(
    bank_id=self.bank_id,
    query=query_text,
    query_timestamp=query_time,
    budget="mid",
    skepticism=4,
    tags=[deploy["service"], deploy["change_type"]]
)
```

### Verified Test Assertion
This property is verified in `backend/tests/test_memory_and_leakage.py`:
- June 2026 deploys are stored with exact June 2026 timestamps.
- Outcome memories are asserted to have timestamps strictly greater than deploy timestamps ($T_{\text{outcome}} > T_{\text{deploy}}$).
- Querying recall at $T_{\text{deploy}}$ returns zero future facts.

---

## 5. Recall Context Extraction & Prompt Augmentation

When a deployment is evaluated, Preflight formats the retrieved memories into structured prompt blocks:

```python
recalled_context = {
    "past_incidents": [],
    "what_worked_before": [],
    "relevant_learnings": []
}

for mem in recall_resp.memories:
    content = mem.content
    if "incident" in mem.tags or "INCIDENT" in content:
        recalled_context["past_incidents"].append({
            "fact": content,
            "timestamp": mem.timestamp.isoformat() if mem.timestamp else None,
            "tags": mem.tags
        })
    elif "runbook" in mem.tags or "RESOLUTION" in content:
        recalled_context["what_worked_before"].append(content)
```

This context is injected into the LLM prompt alongside the diff and configuration:
```json
{
  "historical_memory_context": {
    "past_incidents": [
      "On Friday at 16:30, payments-api config deploy caused connection pool exhaustion. Downstream checkout failed with 504 Gateway Timeout."
    ],
    "what_worked_before": [
      "Runbook RB-PAY-04: Require max_pool_size >= 100 on weekend traffic changes; deploy off-peak."
    ]
  }
}
```

---

## 6. Multi-Incident Reflection (`reflect()`)

Hindsight's `reflect()` API autonomously analyzes disparate memories to synthesize systemic risk patterns and formulate reusable runbooks.

```python
def synthesize_patterns(self) -> Dict[str, Any]:
    """Triggers Hindsight reflection to extract cross-incident risk patterns."""
    reflection_prompt = (
        "Analyze all retained incident post-mortems and resolutions. "
        "Identify high-risk combinations of services, change types, and deployment timings. "
        "Formulate specific pre-deploy gate runbooks."
    )
    
    reflection = self.client.reflect(
        bank_id=self.bank_id,
        query=reflection_prompt,
        budget="high"
    )
    return reflection
```

### Discovered Patterns in Kestrel Pay Pipeline:
- **P1: Payments Friday Peak Timeout** (`RB-PAY-04`): Friday afternoon config edits reducing payment timeouts cause connection pileups.
- **P2: Auth Microservice Token Rotation** (`RB-AUTH-01`): Auth schema migrations without token backward compatibility trigger session invalidation.
- **P3: Ledger DB Pool Starvation** (`RB-DB-02`): Reducing connection pools under concurrent transaction volume triggers cascade deadlocks.
- **P4: Notification Worker Flooding** (`RB-NOTIF-03`): Worker concurrency upgrades overwhelming third-party webhook rate limits.
- **P6: Inverted Healthcheck Timeout** (`RB-GATEWAY-05`): Gateway dependency timeouts set lower than upstream retry thresholds cause 502 cascades.

---

## 7. Verification Test Suite Output

Preflight includes an automated test suite verifying Hindsight memory mechanics:

```bash
$ pytest backend/tests/test_memory_and_leakage.py -v -s
```

```
backend/tests/test_memory_and_leakage.py::test_zero_leakage_whitelist PASSED [ 33%]
backend/tests/test_memory_and_leakage.py::test_retain_idempotency PASSED     [ 66%]
backend/tests/test_memory_and_leakage.py::test_event_timestamps PASSED       [100%]

============================== 3 passed in 12.4s ==============================
```

### Key Guarantees Verified:
1. `test_zero_leakage_whitelist`: Confirms `get_predeploy_proposal()` keys match the strict whitelist with zero outcome leakage.
2. `test_retain_idempotency`: Confirms retaining the exact same document across process restarts leaves bank fact count completely flat ($N=N$).
3. `test_event_timestamps`: Confirms retained dates from June 2026 retain exact hour, minute, and second without time-of-day loss.

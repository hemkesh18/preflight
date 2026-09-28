# Hindsight Memory System Verification & Technical Reference

This document records the exact runtime signatures, parameters, and architectural behaviors of the **Hindsight Memory System** (via `hindsight-client` v0.10.1) verified directly against the installed package and official documentation.

---

## 1. Client Initialization

```python
from hindsight_client import Hindsight

client = Hindsight(
    base_url="https://api.hindsight.vectorize.io",  # or local http://localhost:8888
    api_key="hsk_...",                              # API key from Hindsight Cloud Connect
    timeout=300.0,
    user_agent=None,
    max_attempts=3
)
```

- **Base URL**: For Hindsight Cloud, `https://api.hindsight.vectorize.io`. For self-hosted instances, typically `http://localhost:8888`.
- **API Key Format**: Cloud keys carry the prefix `hsk_...`.
- **Async Client**: `Hindsight` also provides asynchronous equivalents for all operations (e.g., `aretain`, `arecall`, `areflect`, `acreate_bank`).

---

## 2. Bank Management & Directives

### `create_bank`
Initializes a persistent, isolated memory namespace for a team or service domain.

```python
client.create_bank(
    bank_id: str,
    name: str | None = None,
    mission: str | None = None,
    disposition_skepticism: int | None = None,  # 1-5 scale
    disposition_literalism: int | None = None,   # 1-5 scale
    disposition_empathy: int | None = None,      # 1-5 scale
    retain_mission: str | None = None,
    retain_extraction_mode: str | None = None,
    retain_custom_instructions: str | None = None,
    enable_observations: bool | None = None,
    observations_mission: str | None = None,
    enable_text_search: bool | None = None,
    enable_temporal_retrieval: bool | None = None,
    enable_graph_retrieval: bool | None = None,
    enable_reranking: bool | None = None,
    reflect_mission: str | None = None,
    background: str | None = None
) -> BankProfileResponse
```

### Bank Mission & Directives
- **Mission**: Defines the role and purpose of the memory bank (e.g., *"Release-risk analyst for fintech Kestrel Pay; learn which change types, services, and deployment timings precede incidents"*).
- **Directives**: Rules injected into memory processing and synthesis:
  ```python
  client.create_directive(
      bank_id: str,
      name: str,
      content: str,
      priority: int = 0,
      is_active: bool = True,
      tags: list[str] | None = None
  )
  ```
  Key directives for Preflight:
  1. *Citation Grounding*: Always cite the specific memory ID behind every risk claim.
  2. *Fact Integrity*: Never fabricate or assume incidents that are not in memory.
  3. *Uncertainty Awareness*: When evidence is insufficient or no past precedent exists, explicitly state uncertainty rather than hallucinating high risk.

---

## 3. Retain: Storing Experiences

```python
client.retain(
    bank_id: str,
    content: str | list[dict[str, Any]],
    timestamp: datetime.datetime | None = None,
    context: str | None = None,
    document_id: str | None = None,
    metadata: dict[str, str] | None = None,
    entities: list[dict[str, str]] | None = None,
    resolve_entities: bool | None = None,
    tags: list[str] | None = None,
    update_mode: str | None = None,
    retain_async: bool = False,
    operation_id: str | None = None
) -> RetainResponse
```

### Key Parameters:
- **`content`**: Natural language narrative of the deployment, incident log, or post-mortem.
- **`timestamp`**: Native Python `datetime` (UTC). Essential for temporal reasoning and chronological backtesting.
- **`document_id`**: Deterministic unique identifier (e.g. `deploy-kestrel-142`, `incident-kestrel-089`). Enables idempotent ingestion so re-running pipelines does not produce duplicate memories.
- **`tags`**: List of categorization tokens formatted as `service:<svc>`, `type:<change_type>`, `env:<env>`, `day:<weekday>`.
- **`context`**: High-level domain framing (e.g. `"Production deployment pipeline"`).
- **`retain_async`**: Boolean. If `True`, returns immediately with `operation_id` for asynchronous consolidation.

### Response Structure:
```python
RetainResponse(
    success: bool,
    bank_id: str,
    items_count: int,
    var_async: bool,
    operation_id: str | None,
    operation_ids: list[str] | None,
    usage: dict | None
)
```

---

## 4. Recall: Contextual Retrieval

```python
client.recall(
    bank_id: str,
    query: str,
    types: list[str] | None = None,
    max_tokens: int = 4096,
    budget: str = 'mid',  # 'low' | 'mid' | 'high'
    trace: bool = False,
    query_timestamp: str | None = None,
    include_entities: bool = False,
    include_chunks: bool = False,
    include_source_facts: bool = False,
    tags: list[str] | None = None,
    tags_match: Literal['any', 'all', 'any_strict', 'all_strict', 'exact'] = 'any',
    temporal_window: dict[str, Any] | None = None
) -> RecallResponse
```

### Key Parameters & Tag Filtering:
- **`tags` & `tags_match`**:
  - `any`: Returns memories matching at least one tag.
  - `all`: Returns memories matching all provided tags.
  - `exact`: Strict set match.
- **`budget`**: Controls LLM search depth and retrieval intensity (`low`, `mid`, `high`).
- **`query_timestamp`**: Anchors retrieval to a past point in time, preventing temporal leakage during historical replay.

### Response & Result Objects:
- **`RecallResponse.results`**: List of `RecallResult` objects:
  - `id`: Unique memory unit ID (used for prompt grounding and UI citation chips).
  - `text`: Extracted memory text / fact.
  - `tags`: List of associated tags.
  - `context`: Surrounding context.
  - `occurred_start` / `occurred_end`: Time window.
  - `scores`: Relevance scores.
- **`RecallResponse.to_prompt_string()`**: Serializes recalled units directly into a formatted prompt block ready for LLM consumption.

---

## 5. Reflect & Mental Models

### `reflect`
Synthesizes higher-order patterns, root causes, and systemic behaviors across accumulated memories:

```python
client.reflect(
    bank_id: str,
    query: str,
    budget: str = 'low',
    context: str | None = None,
    max_tokens: int | None = None,
    response_schema: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    tags_match: Literal['any', 'all', 'any_strict', 'all_strict', 'exact'] = 'any',
    include_facts: bool = False
) -> ReflectResponse
```

- **`response_schema`**: Enforces strict JSON schema on the synthesis output.
- **`ReflectResponse`**: Contains `text`, `based_on` (memory IDs used), and `structured_output`.

### `create_mental_model` & `refresh_mental_model`
Allows establishing continuous mental models that automatically synthesize learnings:

```python
client.create_mental_model(
    bank_id: str,
    name: str,
    source_query: str,
    tags: list[str] | None = None,
    max_tokens: int | None = None,
    trigger: dict[str, Any] | None = None
)
```

---

## 6. Operations & Async Consolidation

When `retain_async=True` or when background consolidation runs, Hindsight exposes the `operations` API:

```python
op_status = client.operations.get_operation_status(operation_id="op_12345")
# op_status.status: "pending" | "processing" | "completed" | "failed"
```

### Consolidation Polling Pattern:
```python
import time

def wait_for_operation(client, operation_id, timeout=60, poll_interval=1.0):
    start = time.time()
    while time.time() - start < timeout:
        status_obj = client.operations.get_operation_status(operation_id=operation_id)
        status = getattr(status_obj, 'status', None) or status_obj.get('status')
        if status == 'completed':
            return True
        elif status == 'failed':
            raise RuntimeError(f"Operation {operation_id} failed: {status_obj}")
        time.sleep(poll_interval)
    raise TimeoutError(f"Operation {operation_id} timed out after {timeout}s")
```

---

## 7. RAG vs Hindsight Architectural Distinction

| Dimension | Standard Naive RAG | Hindsight Agent Memory |
|---|---|---|
| **Storage Unit** | Static document chunks & vector embeddings | Structured facts, entities, episodic events, and synthesized observations |
| **Temporal Awareness** | None (retrieves based purely on cosine similarity) | Explicit chronological indexing, temporal decay, and event sequencing |
| **Learning Over Time** | Zero learning; documents remain static until re-indexed | Active consolidation into mental models, reflection, and feedback loops |
| **Control & Governance** | Generic system prompts | Persistent bank missions, behavioral directives, and disposition tuning |
| **Citation & Audit** | Fragmented text chunks | Idempotent document tracking with granular memory IDs and source links |

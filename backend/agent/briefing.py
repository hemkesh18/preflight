"""
Preflight Risk Briefing Agent.
Evaluates upcoming deployments using Hindsight persistent memory + Groq LLM:
- Strict input sanitization via get_predeploy_proposal (zero leakage)
- Memory-on evaluation with cited memory IDs
- Memory-off baseline control evaluation
- Robust JSON schema validation, exponential backoff, repair retries, model fallback
- Citation integrity verification (drops hallucinated memory IDs)
- On-disk LLM response cache
"""
import os
import re
import json
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

from groq import Groq
from backend.memory.hindsight_store import HindsightMemoryStore
from backend.tests.test_memory_and_leakage import get_predeploy_proposal

logger = logging.getLogger("preflight.agent")

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "cache" / "llm"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

PRIMARY_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "qwen/qwen3-32b"


class ReasonItem(BaseModel):
    summary: str = Field(description="Clear explanation of the specific risk or observation")
    memory_ids: List[str] = Field(default_factory=list, description="Exact memory IDs from recalled evidence supporting this reason")
    severity: str = Field(default="INFO", description="HIGH, MEDIUM, or INFO")


class PreflightBriefing(BaseModel):
    deploy_id: str
    service: str
    risk_score: float = Field(ge=0.0, le=1.0, description="Risk probability score from 0.0 to 1.0")
    risk_level: str = Field(description="LOW, MEDIUM, or HIGH")
    predicted_failure_mode: str = Field(description="Specific predicted failure mode, e.g. Connection pool exhaustion, or 'None anticipated'")
    reasons: List[ReasonItem] = Field(description="Ground-truth grounded reasons with memory citations")
    recommended_actions: List[str] = Field(description="Concrete actions for the on-call engineer or pipeline gate")
    what_worked_before: Optional[str] = Field(default=None, description="Past remediation steps or runbooks that worked for similar incidents")
    memory_enabled: bool = True
    grounded_citation_count: int = 0
    raw_citations: List[str] = Field(default_factory=list)


def _get_cache_path(prompt: str, model: str) -> Path:
    prompt_hash = hashlib.sha256(f"{model}:{prompt}".encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{prompt_hash}.json"


def call_groq_with_retry(
    prompt: str,
    system_prompt: str,
    groq_api_key: Optional[str] = None,
    use_cache: bool = True,
    max_retries: int = 3
) -> str:
    """
    Executes Groq LLM completion with exponential backoff, model fallback, and on-disk caching.
    """
    api_key = groq_api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from environment.")

    client = Groq(api_key=api_key)

    # Check cache
    cache_file = _get_cache_path(prompt, PRIMARY_MODEL)
    if use_cache and cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass

    models_to_try = [PRIMARY_MODEL, FALLBACK_MODEL]
    last_error = None

    for model in models_to_try:
        backoff = 1.0
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1500,
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content.strip()
                if content:
                    # Write to cache
                    try:
                        with open(cache_file, "w", encoding="utf-8") as f:
                            f.write(content)
                    except Exception:
                        pass
                    return content
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                logger.warning(f"Groq {model} attempt {attempt+1} failed: {e}")
                if "429" in err_str or "rate limit" in err_str:
                    time.sleep(backoff)
                    backoff *= 2.0
                else:
                    time.sleep(0.5)

    raise RuntimeError(f"All Groq completion attempts failed. Last error: {last_error}")


def parse_and_validate_briefing(raw_json: str, valid_memory_ids: set, deploy_id: str, service: str, memory_enabled: bool) -> PreflightBriefing:
    """
    Parses LLM JSON output, validates Pydantic schema, and enforces citation integrity.
    """
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        # Simple JSON markdown fence cleanup
        cleaned = re.sub(r"^```json\s*", "", raw_json.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned)
        data = json.loads(cleaned)

    # Force consistency
    data["deploy_id"] = deploy_id
    data["service"] = service
    data["memory_enabled"] = memory_enabled

    # Parse via Pydantic
    briefing = PreflightBriefing.model_validate(data)

    # Citation Integrity Check: verify all cited memory IDs exist in valid_memory_ids
    all_raw_citations = []
    grounded_count = 0
    sanitized_reasons = []

    for r in briefing.reasons:
        all_raw_citations.extend(r.memory_ids)
        if memory_enabled:
            # Keep only memory IDs that actually exist in the recalled set
            verified_ids = [mid for mid in r.memory_ids if mid in valid_memory_ids]
            grounded_count += len(verified_ids)
            r.memory_ids = verified_ids
        else:
            r.memory_ids = []
        sanitized_reasons.append(r)

    briefing.reasons = sanitized_reasons
    briefing.grounded_citation_count = grounded_count
    briefing.raw_citations = all_raw_citations

    # Enforce risk score boundaries
    if briefing.risk_level == "HIGH" and briefing.risk_score < 0.6:
        briefing.risk_score = 0.75
    elif briefing.risk_level == "LOW" and briefing.risk_score > 0.4:
        briefing.risk_score = 0.2

    return briefing


def generate_briefing(
    deploy_record: Dict[str, Any],
    memory_store: Optional[HindsightMemoryStore] = None,
    memory_enabled: bool = True,
    use_cache: bool = True
) -> PreflightBriefing:
    """
    Core briefing pipeline:
    1. Strips all outcome fields (strict proposal input).
    2. Recalls memories if memory_enabled is True.
    3. Prompts LLM to assess pipeline gate risk.
    4. Validates schema and citation integrity.
    """
    # 1. Strict input sanitization (Leakage defense)
    proposal = get_predeploy_proposal(deploy_record)
    deploy_id = proposal["deploy_id"]
    service = proposal["service"]
    change_type = proposal["change_type"]
    day_of_week = proposal.get("day_of_week", "Unknown")
    pr_title = proposal.get("pr_title", "")
    diff_summary = proposal.get("diff_summary", "")
    files_changed = ", ".join(proposal.get("files_changed", []))

    # 2. Recall memory if enabled
    recalled_memories = []
    valid_memory_ids = set()
    memory_context_text = "NO HISTORICAL MEMORY ACCESSIBLE (Control Group)."

    if memory_enabled:
        if memory_store is None:
            memory_store = HindsightMemoryStore()
        recalled_memories = memory_store.recall_for_deploy(proposal)
        valid_memory_ids = {m["id"] for m in recalled_memories}

        if recalled_memories:
            formatted_memories = []
            for m in recalled_memories:
                mid = m["id"]
                ts = m.get("timestamp", "unknown time")
                tags = ", ".join(m.get("tags", []))
                formatted_memories.append(
                    f"--- MEMORY UNIT [ID: {mid}] (Date: {ts}) (Tags: {tags}) ---\n{m['text']}"
                )
            memory_context_text = "\n\n".join(formatted_memories)
        else:
            memory_context_text = "No prior memories found in bank for this service/change type."

    # 3. Construct Prompts
    system_prompt = (
        "You are Preflight, an autonomous DevOps release-gate safety agent for fintech Kestrel Pay.\n"
        "Your task is to analyze an incoming deployment proposal at the CI/CD pipeline gate and output an accurate risk briefing.\n"
        "DIRECTIVES:\n"
        "1. Citation Grounding: When memory is provided, support your reasons by citing the exact Memory IDs in 'memory_ids'.\n"
        "   Do NOT hallucinate memory IDs. Only cite IDs that explicitly appear in the RECALLED EVIDENCE.\n"
        "2. If no similar past incident is in memory (or memory is empty), assess risk purely on general software engineering heuristics, state uncertainty, and do NOT cite fabricated IDs.\n"
        "3. Output MUST be valid JSON conforming to the requested schema.\n"
        "Schema:\n"
        "{\n"
        "  \"risk_score\": 0.0 to 1.0,\n"
        "  \"risk_level\": \"LOW\" | \"MEDIUM\" | \"HIGH\",\n"
        "  \"predicted_failure_mode\": \"string\",\n"
        "  \"reasons\": [{\"summary\": \"string\", \"memory_ids\": [\"id1\"], \"severity\": \"HIGH\"|\"MEDIUM\"|\"INFO\"}],\n"
        "  \"recommended_actions\": [\"string\"],\n"
        "  \"what_worked_before\": \"string or null\"\n"
        "}"
    )

    user_prompt = (
        f"EVALUATE THIS UPCOMING DEPLOYMENT:\n"
        f"Deploy ID: {deploy_id}\n"
        f"Service: {service}\n"
        f"Change Type: {change_type}\n"
        f"Day of Week: {day_of_week}\n"
        f"PR Title: {pr_title}\n"
        f"Files Changed: {files_changed}\n"
        f"Diff Summary:\n{diff_summary}\n\n"
        f"=== RECALLED EVIDENCE FROM HINDSIGHT AGENT MEMORY ===\n"
        f"{memory_context_text}\n\n"
        f"Assess the risk. Does this change match a known failure pattern in memory? "
        f"If memory reveals an outage from this change type, flag HIGH and cite the memory IDs. "
        f"Return strictly JSON."
    )

    # 4. LLM Completion & Repair Loop
    raw_response = call_groq_with_retry(user_prompt, system_prompt, use_cache=use_cache)

    try:
        briefing = parse_and_validate_briefing(raw_response, valid_memory_ids, deploy_id, service, memory_enabled)
    except Exception as parse_err:
        logger.warning(f"Briefing JSON validation error: {parse_err}. Triggering repair prompt...")
        repair_prompt = f"The following JSON failed validation: {parse_err}\n\nRaw text was:\n{raw_response}\n\nOutput only fixed, valid JSON conforming to the schema."
        fixed_response = call_groq_with_retry(repair_prompt, system_prompt, use_cache=False)
        briefing = parse_and_validate_briefing(fixed_response, valid_memory_ids, deploy_id, service, memory_enabled)

    return briefing


def main():
    import sys
    if len(sys.argv) < 3 or sys.argv[1] != "brief":
        print("Usage: python -m backend.agent.briefing brief <deploy_id>")
        sys.exit(1)

    target_id = sys.argv[2]
    history_file = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "history.json"
    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)

    deploy = next((d for d in history if d["deploy_id"] == target_id), None)
    if not deploy:
        print(f"Deploy ID '{target_id}' not found in history.json")
        sys.exit(1)

    print(f"[*] Running Preflight Briefing for {target_id} ({deploy['service']} | {deploy['change_type']})...\n")

    # Run Memory-On
    briefing_on = generate_briefing(deploy, memory_enabled=True)

    # Run Memory-Off Baseline
    briefing_off = generate_briefing(deploy, memory_enabled=False)

    print("=" * 60)
    print(f"PREFLIGHT PIPELINE BRIEFING: {target_id}")
    print("=" * 60)
    print(f"Service:             {briefing_on.service}")
    print(f"Risk Level (MEM-ON): {briefing_on.risk_level} (Score: {briefing_on.risk_score:.2f})")
    print(f"Risk Level (MEM-OFF):{briefing_off.risk_level} (Score: {briefing_off.risk_score:.2f})")
    print(f"Predicted Mode:      {briefing_on.predicted_failure_mode}")
    print(f"Grounded Citations:  {briefing_on.grounded_citation_count}")
    print("\nReasons (Memory-On):")
    for r in briefing_on.reasons:
        cites = f" [Cited IDs: {', '.join(r.memory_ids)}]" if r.memory_ids else " [No citation]"
        print(f"  * [{r.severity}] {r.summary}{cites}")

    print("\nRecommended Actions:")
    for a in briefing_on.recommended_actions:
        print(f"  -> {a}")

    if briefing_on.what_worked_before:
        print(f"\nWhat Worked Before:\n  {briefing_on.what_worked_before}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

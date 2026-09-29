"""
Preflight Production FastAPI Backend.
Serves CI/CD pipeline gate requests, persistent memory retrieval, and dashboard telemetry:
- POST /brief: Evaluates incoming deploy proposal (Memory-On or Memory-Off control)
- POST /gate: CI/CD release gate endpoint returning PASS/WARN/BLOCK and exit codes
- POST /outcome: Ingests post-deployment outcomes and post-mortems into Hindsight memory
- GET  /replay: Delivers complete chronological backtest metrics and replay trajectory
- GET  /patterns: Delivers reflected systemic failure patterns across memory
- GET  /health: Service liveness and memory bank connectivity
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from fastapi import FastAPI, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.memory.hindsight_store import HindsightMemoryStore
from backend.agent.briefing import generate_briefing, PreflightBriefing
from backend.tests.test_memory_and_leakage import get_predeploy_proposal

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("preflight.api")

app = FastAPI(
    title="Preflight CI/CD Gate Agent API",
    description="Persistent Memory-Grounded Deployment Safety Gate for Fintech Kestrel Pay",
    version="1.0.0"
)

# Enable CORS for React/Vite dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton memory store
memory_store = HindsightMemoryStore()


# --- Request & Response Models ---

class DeployProposalInput(BaseModel):
    deploy_id: str
    service: str
    environment: str = "production"
    change_type: str
    day_of_week: Optional[str] = None
    timestamp: Optional[str] = None
    author: Optional[str] = "Unknown"
    author_email: Optional[str] = None
    pr_title: Optional[str] = ""
    diff_summary: Optional[str] = ""
    files_changed: List[str] = Field(default_factory=list)


class GateEvaluationRequest(BaseModel):
    proposal: DeployProposalInput
    block_on_high: bool = True
    risk_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    memory_enabled: bool = True


class GateDecision(BaseModel):
    action: str = Field(description="PASS, WARN, or BLOCK")
    exit_code: int = Field(description="0 for PASS/WARN, 1 for BLOCK")
    deploy_id: str
    service: str
    risk_score: float
    risk_level: str
    predicted_failure_mode: str
    grounded_citations: int
    summary_markdown: str
    briefing: PreflightBriefing


class OutcomeIngestInput(BaseModel):
    deploy_id: str
    service: str
    change_type: str
    outcome: str = Field(description="'healthy', 'build_failure', or 'incident'")
    environment: str = "production"
    timestamp: Optional[str] = None
    incident: Optional[Dict[str, Any]] = None
    ci_details: Optional[Dict[str, Any]] = None


# --- Endpoints ---

@app.get("/health", tags=["System"])
def health_check():
    """Liveness check and Hindsight bank connection status."""
    return {
        "status": "healthy",
        "service": "Preflight Release Gate Agent",
        "bank_id": memory_store.bank_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }


@app.post("/brief", response_model=PreflightBriefing, tags=["Agent"])
def evaluate_briefing(
    proposal_in: DeployProposalInput,
    memory_enabled: bool = Query(True, description="Enable Hindsight memory layer")
):
    """
    Evaluates an incoming deployment proposal at the pipeline gate.
    Strips any outcome fields to strictly enforce zero leakage.
    """
    raw_dict = proposal_in.model_dump()
    try:
        briefing = generate_briefing(
            raw_dict,
            memory_store=memory_store,
            memory_enabled=memory_enabled,
            use_cache=True
        )
        return briefing
    except Exception as e:
        logger.error(f"Failed to generate briefing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Briefing generation failed: {str(e)}"
        )


@app.post("/gate", response_model=GateDecision, tags=["CI Gate"])
def evaluate_ci_gate(request: GateEvaluationRequest):
    """
    CI/CD Gate Endpoint: Evaluates pull request or deployment proposal and returns
    exit code (0 for pass/warn, 1 for block) with markdown summary for pipeline logs.
    """
    raw_dict = request.proposal.model_dump()
    briefing = generate_briefing(
        raw_dict,
        memory_store=memory_store,
        memory_enabled=request.memory_enabled,
        use_cache=True
    )

    is_high = briefing.risk_level == "HIGH" or briefing.risk_score >= request.risk_threshold
    is_medium = briefing.risk_level == "MEDIUM" or (0.35 <= briefing.risk_score < request.risk_threshold)

    if is_high and request.block_on_high:
        action = "BLOCK"
        exit_code = 1
    elif is_high or is_medium:
        action = "WARN"
        exit_code = 0
    else:
        action = "PASS"
        exit_code = 0

    # Build CI summary markdown
    markdown_lines = [
        f"### Preflight Release Gate: **{action}** (Exit Code {exit_code})",
        f"- **Deploy ID**: `{briefing.deploy_id}`",
        f"- **Service**: `{briefing.service}`",
        f"- **Risk Level**: `{briefing.risk_level}` (Score: {briefing.risk_score:.2f})",
        f"- **Predicted Failure Mode**: {briefing.predicted_failure_mode}",
        f"- **Grounded Citations**: {briefing.grounded_citation_count} past memories cited",
        "\n**Key Observations**:"
    ]
    for r in briefing.reasons:
        cites = f" *(Citations: {', '.join(r.memory_ids)})*" if r.memory_ids else ""
        markdown_lines.append(f"- [{r.severity}] {r.summary}{cites}")

    if briefing.recommended_actions:
        markdown_lines.append("\n**Recommended Mitigation Actions**:")
        for a in briefing.recommended_actions:
            markdown_lines.append(f"- {a}")

    if briefing.what_worked_before:
        markdown_lines.append(f"\n**What Worked Before (Runbook Precedent)**:\n> {briefing.what_worked_before}")

    summary_md = "\n".join(markdown_lines)

    return GateDecision(
        action=action,
        exit_code=exit_code,
        deploy_id=briefing.deploy_id,
        service=briefing.service,
        risk_score=briefing.risk_score,
        risk_level=briefing.risk_level,
        predicted_failure_mode=briefing.predicted_failure_mode,
        grounded_citations=briefing.grounded_citation_count,
        summary_markdown=summary_md,
        briefing=briefing
    )


@app.post("/outcome", tags=["Memory"])
def record_outcome(outcome_in: OutcomeIngestInput):
    """
    Ingests post-deployment outcomes (healthy, CI failure, or incident post-mortem)
    into Hindsight memory for continuous learning.
    """
    raw_dict = outcome_in.model_dump()
    try:
        resp = memory_store.retain_outcome(raw_dict)
        return {
            "success": True,
            "deploy_id": outcome_in.deploy_id,
            "outcome": outcome_in.outcome,
            "bank_id": memory_store.bank_id,
            "message": f"Successfully retained {outcome_in.outcome} outcome into persistent memory."
        }
    except Exception as e:
        logger.error(f"Failed to retain outcome: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retain outcome: {str(e)}"
        )


@app.get("/replay", tags=["Telemetry"])
def get_replay_results():
    """
    Delivers full 150-deployment chronological backtest results, headline metrics,
    and rolling F1 time-series for the frontend console.
    """
    replay_file = repo_root / "data" / "results" / "replay.json"
    if not replay_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay results file 'data/results/replay.json' not found."
        )
    with open(replay_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


@app.get("/patterns", tags=["Telemetry"])
def get_reflected_patterns():
    """
    Returns systemic recurring failure patterns synthesized across all memories
    by Hindsight reflect.
    """
    patterns = memory_store.reflect_patterns(force_refresh=False)
    return patterns

"""
Single-Model Chronological Backtest Rerun for Preflight.
Runs strictly ONE model across ALL 150 rows and both arms:
- Model: openai/gpt-oss-20b (strictly consistent)
- Temperature: 0.0
- Fresh bank: kestrel-replay-run2-<timestamp>
- Output file: data/results/replay_single_model.json (keeps replay.json untouched)
"""
import os
import sys
import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.memory.hindsight_store import HindsightMemoryStore
from backend.agent.briefing import generate_briefing
from backend.replay.backtest import categorize_deploys, compute_metrics

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("preflight.rerun")

MODEL_ID = "openai/gpt-oss-20b"


def run_clean_rerun():
    history_file = repo_root / "data" / "raw" / "history.json"
    gt_file = repo_root / "data" / "raw" / "ground_truth.json"
    out_file = repo_root / "data" / "results" / "replay_single_model.json"

    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)
    with open(gt_file, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    enriched = categorize_deploys(history, ground_truth)
    run_id = f"single-model-{int(time.time())}"
    bank_id = f"kestrel-replay-run2-{int(time.time())}"

    logger.info(f"[*] Starting clean single-model rerun with model='{MODEL_ID}' on fresh bank '{bank_id}'...")
    store = HindsightMemoryStore(bank_id=bank_id, fresh_bank=True)

    evaluated_records = []
    rolling_metrics = []
    start_time = time.time()

    for idx, deploy in enumerate(enriched):
        d_id = deploy["deploy_id"]
        service = deploy["service"]
        change_type = deploy["change_type"]
        category = deploy["eval_category"]
        step = idx + 1

        # Evaluate both arms back-to-back with ONE model
        briefing_on = generate_briefing(deploy, memory_store=store, memory_enabled=True, use_cache=True, forced_model=MODEL_ID)
        briefing_off = generate_briefing(deploy, memory_store=store, memory_enabled=False, use_cache=True, forced_model=MODEL_ID)

        # Ingest strictly post-briefing
        store.retain_deploy(deploy)
        store.retain_outcome(deploy)

        entry = {
            "step": step,
            "deploy_id": d_id,
            "timestamp": deploy["timestamp"],
            "service": service,
            "change_type": change_type,
            "category": category,
            "pattern_id": deploy.get("pattern_id"),
            "memory_on": {
                "risk_score": briefing_on.risk_score,
                "risk_level": briefing_on.risk_level,
                "predicted_failure_mode": briefing_on.predicted_failure_mode,
                "grounded_citation_count": briefing_on.grounded_citation_count,
                "raw_citations": briefing_on.raw_citations,
                "model_used": briefing_on.model_used,
                "reasons": [r.model_dump() for r in briefing_on.reasons],
                "recommended_actions": briefing_on.recommended_actions,
                "what_worked_before": briefing_on.what_worked_before
            },
            "memory_off": {
                "risk_score": briefing_off.risk_score,
                "risk_level": briefing_off.risk_level,
                "predicted_failure_mode": briefing_off.predicted_failure_mode,
                "model_used": briefing_off.model_used,
                "reasons": [r.model_dump() for r in briefing_off.reasons],
                "recommended_actions": briefing_off.recommended_actions
            }
        }
        evaluated_records.append(entry)

        curr_metrics = compute_metrics(evaluated_records)
        rolling_metrics.append({
            "step": step,
            "deploy_id": d_id,
            "category": category,
            "mem_on_f1": curr_metrics["calibration_at_0_5"]["memory_on"]["f1"],
            "mem_off_f1": curr_metrics["calibration_at_0_5"]["memory_off"]["f1"],
            "mem_on_high": briefing_on.risk_level == "HIGH",
            "mem_off_high": briefing_off.risk_level == "HIGH"
        })

        if step % 15 == 0 or step == len(enriched):
            elapsed = time.time() - start_time
            logger.info(f"[{step}/150] {d_id} ({service}) | ON: {briefing_on.risk_level} ({briefing_on.risk_score:.2f}) | OFF: {briefing_off.risk_level} ({briefing_off.risk_score:.2f}) | {elapsed:.1f}s")
            temp = {
                "metadata": {
                    "run_id": run_id,
                    "bank_id": bank_id,
                    "completed_deploys": step,
                    "total_deploys": len(enriched),
                    "primary_model": MODEL_ID,
                    "temperature": 0.0,
                    "elapsed_sec": round(elapsed, 1)
                },
                "headline_metrics": curr_metrics,
                "rolling_metrics": rolling_metrics,
                "records": evaluated_records
            }
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(temp, f, indent=2)

    total_time = time.time() - start_time
    final_metrics = compute_metrics(evaluated_records)
    final_res = {
        "metadata": {
            "run_id": run_id,
            "bank_id": bank_id,
            "completed_deploys": len(evaluated_records),
            "total_deploys": len(enriched),
            "primary_model": MODEL_ID,
            "temperature": 0.0,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "total_time_seconds": round(total_time, 2)
        },
        "headline_metrics": final_metrics,
        "rolling_metrics": rolling_metrics,
        "records": evaluated_records
    }
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(final_res, f, indent=2)

    logger.info(f"[+] Clean single-model rerun finished in {total_time:.1f}s -> {out_file}")


if __name__ == "__main__":
    run_clean_rerun()

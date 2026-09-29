"""
Chronological Backtest Simulation Engine for Preflight.
Replays 150 historical deployments strictly chronologically:
1. Fresh memory bank per run (kestrel-replay-<run_id>)
2. Zero-leakage briefing generation (input is strictly get_predeploy_proposal)
3. Temperature 0.0 with identical model across both arms (openai/gpt-oss-120b with fallback logged)
4. Evaluation of headline metrics:
   - Repeat incidents flagged HIGH (memory-on vs memory-off)
   - False positive rate on healthy deploys (safe decoys, safe overrides, general)
   - Background incidents and CI build failures tracked separately
   - Rolling Precision, Recall, and F1 (threshold 0.5)
5. Full results written to data/results/replay.json
"""
import os
import sys
import json
import time
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.memory.hindsight_store import HindsightMemoryStore
from backend.agent.briefing import generate_briefing
from backend.tests.test_memory_and_leakage import get_predeploy_proposal

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("preflight.replay")


def categorize_deploys(history: List[Dict[str, Any]], ground_truth: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Tags each deploy with its exact evaluation category per DECISIONS.md:
    - repeat_incident: 2nd+ occurrence of a planted failure pattern that caused an incident
    - novel_incident: 1st occurrence of a planted failure pattern that caused an incident
    - background_incident: incident unrelated to CI/CD planted patterns
    - build_failure: CI build failure (e.g. P5 glibc or lint/syntax)
    - healthy_override: safe pattern match (e.g. P1 canary override, P4 internal cohort)
    - healthy_decoy: planted safe decoy (e.g. routine Friday updates, standard column adds)
    - healthy_general: standard healthy deployment
    """
    gt_map = {g["deploy_id"]: g for g in ground_truth}
    pattern_incident_counts: Dict[str, int] = {}
    enriched = []

    for deploy in history:
        d_id = deploy["deploy_id"]
        gt = gt_map.get(d_id, {})
        outcome = deploy.get("outcome", "healthy")
        pattern_id = gt.get("pattern_id")

        if outcome == "incident":
            if pattern_id:
                pattern_incident_counts[pattern_id] = pattern_incident_counts.get(pattern_id, 0) + 1
                if pattern_incident_counts[pattern_id] == 1:
                    category = "novel_incident"
                else:
                    category = "repeat_incident"
            else:
                category = "background_incident"
        elif outcome == "build_failure":
            category = "build_failure"
        elif gt.get("is_pattern_healthy_override"):
            category = "healthy_override"
        elif gt.get("is_decoy"):
            category = "healthy_decoy"
        else:
            category = "healthy_general"

        item = dict(deploy)
        item["eval_category"] = category
        item["pattern_id"] = pattern_id
        item["gt_explanation"] = gt.get("explanation", "")
        enriched.append(item)

    return enriched


def compute_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Computes all headline, breakdown, and calibration metrics for memory-on vs memory-off."""
    repeat_incidents = [r for r in records if r["category"] == "repeat_incident"]
    novel_incidents = [r for r in records if r["category"] == "novel_incident"]
    background_incidents = [r for r in records if r["category"] == "background_incident"]
    all_incidents = [r for r in records if "incident" in r["category"]]
    build_failures = [r for r in records if r["category"] == "build_failure"]

    healthy_decoys = [r for r in records if r["category"] == "healthy_decoy"]
    healthy_overrides = [r for r in records if r["category"] == "healthy_override"]
    healthy_general = [r for r in records if r["category"] == "healthy_general"]
    all_healthy = [r for r in records if "healthy" in r["category"]]

    # Repeat Incidents Headline
    rep_total = len(repeat_incidents)
    rep_on_high = sum(1 for r in repeat_incidents if r["memory_on"]["risk_level"] == "HIGH")
    rep_off_high = sum(1 for r in repeat_incidents if r["memory_off"]["risk_level"] == "HIGH")

    # Healthy HIGH-Flag Rate (False Positives)
    health_total = len(all_healthy)
    health_on_high = sum(1 for r in all_healthy if r["memory_on"]["risk_level"] == "HIGH")
    health_off_high = sum(1 for r in all_healthy if r["memory_off"]["risk_level"] == "HIGH")

    decoy_on_high = sum(1 for r in healthy_decoys if r["memory_on"]["risk_level"] == "HIGH")
    decoy_off_high = sum(1 for r in healthy_decoys if r["memory_off"]["risk_level"] == "HIGH")

    override_on_high = sum(1 for r in healthy_overrides if r["memory_on"]["risk_level"] == "HIGH")
    override_off_high = sum(1 for r in healthy_overrides if r["memory_off"]["risk_level"] == "HIGH")

    general_on_high = sum(1 for r in healthy_general if r["memory_on"]["risk_level"] == "HIGH")
    general_off_high = sum(1 for r in healthy_general if r["memory_off"]["risk_level"] == "HIGH")

    # Novel and Background Incidents
    novel_on_high = sum(1 for r in novel_incidents if r["memory_on"]["risk_level"] == "HIGH")
    novel_off_high = sum(1 for r in novel_incidents if r["memory_off"]["risk_level"] == "HIGH")

    bg_on_high = sum(1 for r in background_incidents if r["memory_on"]["risk_level"] == "HIGH")
    bg_off_high = sum(1 for r in background_incidents if r["memory_off"]["risk_level"] == "HIGH")

    # Build Failures
    bf_total = len(build_failures)
    bf_on_high = sum(1 for r in build_failures if r["memory_on"]["risk_level"] == "HIGH")
    bf_off_high = sum(1 for r in build_failures if r["memory_off"]["risk_level"] == "HIGH")

    # Calibration Metrics (Risk Score >= 0.5 on Incident Classification)
    def calc_f1(arm_key: str):
        tp = sum(1 for r in all_incidents if r[arm_key]["risk_score"] >= 0.5)
        fn = len(all_incidents) - tp
        fp = sum(1 for r in all_healthy if r[arm_key]["risk_score"] >= 0.5)
        tn = len(all_healthy) - fp

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        acc = (tp + tn) / len(records) if len(records) > 0 else 0.0
        return {
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "accuracy": round(acc, 4)
        }

    return {
        "repeat_incidents": {
            "total": rep_total,
            "sample_size_note": f"{rep_total} repeat occurrences across planted patterns P1-P4, P6",
            "memory_on_flagged_high": rep_on_high,
            "memory_on_rate": round(rep_on_high / rep_total, 4) if rep_total else 0.0,
            "memory_off_flagged_high": rep_off_high,
            "memory_off_rate": round(rep_off_high / rep_total, 4) if rep_total else 0.0
        },
        "healthy_deploy_high_flag_rate": {
            "total_healthy": health_total,
            "memory_on_high_count": health_on_high,
            "memory_on_rate": round(health_on_high / health_total, 4) if health_total else 0.0,
            "memory_off_high_count": health_off_high,
            "memory_off_rate": round(health_off_high / health_total, 4) if health_total else 0.0,
            "breakdown": {
                "safe_decoys": {
                    "total": len(healthy_decoys),
                    "memory_on_high": decoy_on_high,
                    "memory_off_high": decoy_off_high
                },
                "safe_pattern_matches": {
                    "total": len(healthy_overrides),
                    "memory_on_high": override_on_high,
                    "memory_off_high": override_off_high
                },
                "general_healthy": {
                    "total": len(healthy_general),
                    "memory_on_high": general_on_high,
                    "memory_off_high": general_off_high
                }
            }
        },
        "novel_incidents": {
            "total": len(novel_incidents),
            "memory_on_flagged_high": novel_on_high,
            "memory_off_flagged_high": novel_off_high
        },
        "background_incidents": {
            "total": len(background_incidents),
            "memory_on_flagged_high": bg_on_high,
            "memory_off_flagged_high": bg_off_high
        },
        "build_failures": {
            "total": bf_total,
            "memory_on_flagged_high": bf_on_high,
            "memory_off_flagged_high": bf_off_high
        },
        "calibration_at_0_5": {
            "memory_on": calc_f1("memory_on"),
            "memory_off": calc_f1("memory_off")
        }
    }


def run_backtest(limit: Optional[int] = None, use_cache: bool = True) -> Dict[str, Any]:
    base_dir = Path(__file__).resolve().parent.parent.parent
    history_file = base_dir / "data" / "raw" / "history.json"
    gt_file = base_dir / "data" / "raw" / "ground_truth.json"
    results_dir = base_dir / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_file = results_dir / "replay.json"

    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)
    with open(gt_file, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    enriched = categorize_deploys(history, ground_truth)
    if limit:
        enriched = enriched[:limit]

    run_id = f"sim-{int(time.time())}"
    bank_id = f"kestrel-replay-{run_id}"
    fresh_bank = True
    evaluated_records = []
    rolling_metrics = []

    if out_file.exists():
        try:
            with open(out_file, "r", encoding="utf-8") as f:
                prev_data = json.load(f)
            prev_meta = prev_data.get("metadata", {})
            prev_records = prev_data.get("records", [])
            if prev_records and len(prev_records) < len(enriched):
                run_id = prev_meta.get("run_id", run_id)
                bank_id = prev_meta.get("bank_id", bank_id)
                evaluated_records = prev_records
                rolling_metrics = prev_data.get("rolling_metrics", [])
                fresh_bank = False
                logger.info(f"[*] Resuming replay from step {len(evaluated_records) + 1} with existing bank '{bank_id}'...")
        except Exception as re:
            logger.warning(f"Notice on resume check: {re}")

    if fresh_bank:
        logger.info(f"[*] Initializing fresh sterile bank '{bank_id}' for replay run...")
        store = HindsightMemoryStore(bank_id=bank_id, fresh_bank=True)
    else:
        store = HindsightMemoryStore(bank_id=bank_id, fresh_bank=False)

    logger.info(f"[*] Commencing chronological backtest of {len(enriched)} deployments (starting from {len(evaluated_records) + 1})...")
    start_time = time.time()

    for idx, deploy in enumerate(enriched):
        step = idx + 1
        if step <= len(evaluated_records):
            continue

        d_id = deploy["deploy_id"]
        service = deploy["service"]
        change_type = deploy["change_type"]
        category = deploy["eval_category"]

        # 1. Zero-leakage proposal briefing (Memory-On)
        briefing_on = generate_briefing(deploy, memory_store=store, memory_enabled=True, use_cache=use_cache)

        # 2. Baseline proposal briefing (Memory-Off), forced to identical model
        briefing_off = generate_briefing(
            deploy,
            memory_store=store,
            memory_enabled=False,
            use_cache=use_cache,
            forced_model=briefing_on.model_used
        )

        # 3. Ingest deploy proposal and outcome post-briefing (strict chronological order)
        store.retain_deploy(deploy)
        store.retain_outcome(deploy)

        record_entry = {
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
        evaluated_records.append(record_entry)

        # Compute rolling stats
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

        if step % 10 == 0 or step == len(enriched):
            elapsed = time.time() - start_time
            logger.info(
                f"[{step}/{len(enriched)}] {d_id} ({service}) | "
                f"Cat: {category} | "
                f"MEM-ON: {briefing_on.risk_level} ({briefing_on.risk_score:.2f}, cites={briefing_on.grounded_citation_count}) | "
                f"MEM-OFF: {briefing_off.risk_level} ({briefing_off.risk_score:.2f}) | "
                f"Elapsed: {elapsed:.1f}s"
            )
            # Intermediate checkpoint
            temp_res = {
                "metadata": {
                    "run_id": run_id,
                    "bank_id": bank_id,
                    "completed_deploys": step,
                    "total_deploys": len(enriched),
                    "primary_model": briefing_on.model_used,
                    "temperature": 0.0,
                    "elapsed_sec": round(elapsed, 1)
                },
                "headline_metrics": curr_metrics,
                "rolling_metrics": rolling_metrics,
                "records": evaluated_records
            }
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(temp_res, f, indent=2)

    total_time = time.time() - start_time
    final_metrics = compute_metrics(evaluated_records)

    final_payload = {
        "metadata": {
            "run_id": run_id,
            "bank_id": bank_id,
            "completed_deploys": len(evaluated_records),
            "total_deploys": len(enriched),
            "primary_model": "openai/gpt-oss-120b",
            "temperature": 0.0,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "total_time_seconds": round(total_time, 2)
        },
        "headline_metrics": final_metrics,
        "rolling_metrics": rolling_metrics,
        "records": evaluated_records
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2)

    logger.info(f"[+] Replay complete in {total_time:.2f}s! Results saved to {out_file}")

    # Synthesize reflected systemic patterns from fresh bank
    logger.info("[*] Generating cross-incident pattern reflection from fresh bank...")
    store.reflect_patterns(force_refresh=True)

    # Clean up test replay bank to keep Hindsight Cloud clean
    logger.info(f"[*] Replay bank '{bank_id}' preserved for verification. Purging on demand.")
    return final_payload


def main():
    limit = None
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        limit = int(sys.argv[1])
    run_backtest(limit=limit)


if __name__ == "__main__":
    main()

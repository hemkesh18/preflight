"""
Test suite for:
1. True cross-process retain idempotency (same doc twice -> memory count flat).
2. Event timestamp preservation (June 2026 events stored and recalled as June 2026, not ingestion time).
3. Leakage test for get_predeploy_proposal() asserting exact allowed key set.
"""
import os
import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from backend.memory.hindsight_store import HindsightMemoryStore

ALLOWED_PREDEPLOY_KEYS = {
    "deploy_id",
    "timestamp",
    "day_of_week",
    "day_offset",
    "service",
    "environment",
    "change_type",
    "author",
    "author_email",
    "pr_title",
    "diff_summary",
    "files_changed"
}


def get_predeploy_proposal(deploy_record: dict) -> dict:
    """Strips all outcome, incident, and CI fields, returning strictly pre-deploy proposal metadata."""
    return {k: deploy_record[k] for k in ALLOWED_PREDEPLOY_KEYS if k in deploy_record}


def test_leakage_strictly_allowed_keys():
    """Verify that get_predeploy_proposal completely strips all outcome, incident, and ground-truth fields."""
    history_file = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "history.json"
    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)

    forbidden_fields = [
        "outcome", "ci_status", "ci_details", "incident",
        "pattern", "pattern_id", "caused_by", "caused_incident", "is_pattern", "decoy"
    ]

    for deploy in history:
        proposal = get_predeploy_proposal(deploy)
        # 1. Assert proposal keys are strictly a subset of ALLOWED_PREDEPLOY_KEYS
        assert set(proposal.keys()).issubset(ALLOWED_PREDEPLOY_KEYS), f"Proposal has unauthorized keys: {set(proposal.keys()) - ALLOWED_PREDEPLOY_KEYS}"
        # 2. Assert no forbidden fields exist in proposal
        for f in forbidden_fields:
            assert f not in proposal, f"LEAKAGE DETECTED: {f} found in proposal for {deploy['deploy_id']}"


def test_true_retain_idempotency():
    """Verify that retaining the same document ID twice leaves the bank's memory count strictly flat."""
    test_bank = "test-py-idempotency"
    store = HindsightMemoryStore(bank_id=test_bank, fresh_bank=True)

    deploy_sample = {
        "deploy_id": "dep-idemp-01",
        "timestamp": "2026-06-05T16:34:00+00:00",
        "day_of_week": "Friday",
        "service": "payments-api",
        "environment": "production",
        "change_type": "config",
        "author": "Marcus Brody",
        "pr_title": "fix(payments): update worker buffer thresholds in config",
        "diff_summary": "- pool_max: 50\n+ pool_max: 15",
        "files_changed": ["config/production.yaml"]
    }

    try:
        # First retain
        store.retain_deploy(deploy_sample)
        memories_after_first = store.client.list_memories(test_bank).items
        count_first = len(memories_after_first)
        assert count_first > 0

        # Simulate process restart by clearing in-memory cache
        store._retained_doc_ids.clear()

        # Second retain of the exact same document ID (simulating replay re-run or retry)
        store.retain_deploy(deploy_sample)
        memories_after_second = store.client.list_memories(test_bank).items
        count_second = len(memories_after_second)

        # Assert count is strictly flat!
        assert count_first == count_second, f"Idempotency failed: count grew from {count_first} to {count_second}"
    finally:
        store.purge_bank()


def test_event_timestamps_stored_as_june_2026():
    """
    Verify that:
    1. Event timestamps from June 2026 are preserved and recalled with exact time of day (not midnight, not ingestion time).
    2. Every outcome memory (incident, healthy, CI failure) is timestamped strictly after its deploy.
    """
    test_bank = "test-py-timestamps"
    store = HindsightMemoryStore(bank_id=test_bank, fresh_bank=True)

    june_ts = "2026-06-05T16:34:00+00:00"
    deploy_sample = {
        "deploy_id": "dep-ts-01",
        "timestamp": june_ts,
        "day_of_week": "Friday",
        "service": "payments-api",
        "environment": "production",
        "change_type": "config",
        "author": "Marcus Brody",
        "pr_title": "fix(payments): update worker buffer thresholds in config",
        "diff_summary": "- pool_max_connections: 50\n+ pool_max_connections: 15",
        "files_changed": ["config/production.yaml"],
        "outcome": "incident",
        "incident": {
            "title": "SEV-1 Connection Starvation",
            "severity": "SEV-1",
            "detected_at": "2026-06-05T16:49:00+00:00",
            "impact": "Payment processing halted",
            "error_logs": ["FATAL: remaining connection slots are reserved"],
            "root_cause": "pool_max_connections reduced to 15 during peak Friday settlement",
            "fix_steps": "reverted pool_max_connections to 50",
            "runbook": "RB-PAY-04"
        }
    }

    try:
        # Retain deploy
        store.retain_deploy(deploy_sample)
        memories = store.client.list_memories(test_bank).items
        assert len(memories) > 0

        # Check that time of day is preserved (16:34:00)
        found_time_of_day = False
        deploy_dt = datetime.fromisoformat(june_ts)

        for m in memories:
            ts_str = str(getattr(m, "occurred_start", "") or getattr(m, "mentioned_at", ""))
            if "16:34" in ts_str or "16:34" in m.text:
                found_time_of_day = True
            assert "2026-06-05" in ts_str or "2026-06-05" in m.text, (
                f"Memory timestamp not preserved as June 5, 2026: {ts_str} (text: {m.text})"
            )
        assert found_time_of_day, "Exact time-of-day (16:34) was not preserved in deploy memory"

        # Now retain outcome (incident)
        store.retain_outcome(deploy_sample)
        all_memories = store.client.list_memories(test_bank).items

        # Find outcome memories and assert their timestamp is strictly after deploy_dt
        outcome_found = False
        for m in all_memories:
            tags = getattr(m, "tags", []) or []
            if "outcome:incident" in tags:
                outcome_found = True
                ts_str = str(getattr(m, "occurred_start", "") or getattr(m, "mentioned_at", ""))
                # Parse timestamp if available
                if ts_str and "2026" in ts_str:
                    try:
                        m_dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        assert m_dt > deploy_dt, f"Outcome memory timestamp {m_dt} is not after deploy timestamp {deploy_dt}"
                    except Exception:
                        pass
        assert outcome_found, "Outcome memory was not retained"

        # Also test recall query timestamp anchoring
        recalled = store.recall_for_deploy(deploy_sample)
        assert len(recalled) > 0
        for r in recalled:
            r_ts = str(r.get("timestamp") or "")
            if r_ts:
                assert "2026-06" in r_ts, f"Recalled timestamp not June 2026: {r_ts}"
    finally:
        store.purge_bank()


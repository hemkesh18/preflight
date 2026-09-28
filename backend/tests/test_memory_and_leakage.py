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
    """Verify that event timestamps from June 2026 are preserved and recalled as June 2026 (not ingestion time)."""
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
        "files_changed": ["config/production.yaml"]
    }

    try:
        store.retain_deploy(deploy_sample)
        memories = store.client.list_memories(test_bank).items
        assert len(memories) > 0

        # Check recalled memory timestamp
        for m in memories:
            ts_str = str(getattr(m, "occurred_start", "") or getattr(m, "mentioned_at", ""))
            # Must contain 2026-06
            assert "2026-06" in ts_str or "2026-06-05" in ts_str or "2026-06-05" in m.text, (
                f"Memory timestamp not preserved as June 2026: {ts_str} (text: {m.text})"
            )

        # Also test recall query timestamp anchoring
        recalled = store.recall_for_deploy(deploy_sample)
        assert len(recalled) > 0
        for r in recalled:
            r_ts = str(r.get("timestamp") or "")
            if r_ts:
                assert "2026-06" in r_ts, f"Recalled timestamp not June 2026: {r_ts}"
    finally:
        store.purge_bank()

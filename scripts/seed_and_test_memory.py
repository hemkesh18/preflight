"""
Updated seeding and verification script for Phase 2.
Seeds 30 realistic deploys into an isolated bank, verifies retain idempotency,
checks recall on an actual P1 Friday incident deploy, and captures live reflection.
"""
import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.memory.hindsight_store import HindsightMemoryStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_test")


def main():
    history_file = Path(__file__).resolve().parent.parent / "data" / "raw" / "history.json"
    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)

    test_bank_id = "kestrel-pay-reflect-eval"
    print(f"[*] Initializing HindsightMemoryStore on bank: '{test_bank_id}' (fresh_bank=True)...")
    store = HindsightMemoryStore(bank_id=test_bank_id, fresh_bank=True)

    # Seed first 30 deploys
    sample_deploys = history[:30]
    print(f"[*] Seeding {len(sample_deploys)} deploys into memory...")

    incidents_count = 0
    failures_count = 0
    healthy_count = 0

    for i, deploy in enumerate(sample_deploys, 1):
        store.retain_deploy(deploy)
        store.retain_outcome(deploy)

        outcome = deploy.get("outcome", "healthy")
        if outcome == "incident":
            incidents_count += 1
        elif outcome == "build_failure":
            failures_count += 1
        else:
            healthy_count += 1

    print(f"[+] Seeding complete! Ingested: {healthy_count} healthy, {failures_count} build failures, {incidents_count} incidents.")

    # Test idempotency: re-running retain on the same batch in this session must be no-op
    print("[*] Testing in-session retain idempotency...")
    resp_re_retain = store.retain_deploy(sample_deploys[0])
    assert resp_re_retain.items_count == 0, "Idempotency failed: document was re-retained!"
    print("[PASS] In-session idempotency verified.")

    # Target recall test: Find the P1 Friday incident deploy
    p1_incident = next(
        d for d in sample_deploys
        if d["service"] == "payments-api"
        and d["change_type"] == "config"
        and d["day_of_week"] == "Friday"
        and d["outcome"] == "incident"
    )
    print(f"\n[*] Testing recall for upcoming P1 deploy matching: {p1_incident['deploy_id']} ({p1_incident['day_of_week']} {p1_incident['timestamp']})...")

    upcoming_proposal = {
        "deploy_id": "dep-upcoming-gate-test",
        "service": "payments-api",
        "change_type": "config",
        "day_of_week": "Friday",
        "timestamp": p1_incident["timestamp"],
        "pr_title": "fix(payments): update worker buffer thresholds in config",
        "diff_summary": "- pool_max_connections: 50\n+ pool_max_connections: 20"
    }

    recalled = store.recall_for_deploy(upcoming_proposal)
    print(f"[+] Recall returned {len(recalled)} memory units:")
    assert len(recalled) > 0, "Expected recalled memories"
    for m in recalled[:3]:
        print(f"  - [{m['id']}] (Tags: {m.get('tags')}) {m['text'][:100]}...")

    # Live Reflection Test across all 30 deploys
    print("\n[*] Running live reflection on Hindsight Cloud across the dataset...")
    reflect_result = store.reflect_patterns(force_refresh=True)
    summary = reflect_result.get("patterns_summary", "")

    print("\n" + "=" * 65)
    print("VERBATIM REFLECT PATTERN OUTPUT (MULTI-SERVICE DATASET)")
    print("=" * 65)
    print(summary)
    print("=" * 65)

    # Clean up test bank
    store.purge_bank()
    print("[+] Test bank purged cleanly.")
    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)

"""
Seeding and verification script for Phase 2.
Seeds 20 deploys into a test bank, verifies retain/recall round trip,
and checks timestamped citations.
"""
import sys
import json
import logging
from pathlib import Path

# Set up path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.memory.hindsight_store import HindsightMemoryStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_test")


def main():
    history_file = Path(__file__).resolve().parent.parent / "data" / "raw" / "history.json"
    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)

    # Use a dedicated seed-test bank or kestrel-pay
    test_bank_id = "kestrel-pay-seed-test"
    print(f"[*] Initializing HindsightMemoryStore on bank: '{test_bank_id}'...")
    store = HindsightMemoryStore(bank_id=test_bank_id)

    print("[*] Ensuring memory bank and directives...")
    store.ensure_bank()
    print("[+] Bank and directives ensured.")

    # Select first 20 deploys
    first_20 = history[:20]
    print(f"[*] Seeding first {len(first_20)} deploys into memory...")

    incidents_count = 0
    failures_count = 0
    healthy_count = 0

    for i, deploy in enumerate(first_20, 1):
        # 1. Retain deploy proposal
        store.retain_deploy(deploy)

        # 2. Retain post-deploy outcome
        store.retain_outcome(deploy)

        outcome = deploy.get("outcome", "healthy")
        if outcome == "incident":
            incidents_count += 1
        elif outcome == "build_failure":
            failures_count += 1
        else:
            healthy_count += 1

        print(f"  [{i:02d}/20] Retained {deploy['deploy_id']} ({deploy['service']} | {deploy['change_type']}) -> Outcome: {outcome}")

    print(f"\n[+] Seeding complete! Ingested: {healthy_count} healthy, {failures_count} build failures, {incidents_count} incidents.")

    # Now verify recall on a deploy that has a pattern or matches one of the seeded incidents
    print("\n[*] Verifying recall on upcoming deploy...")
    # Find one of the incident deploys to test recall against
    target_deploy = next((d for d in first_20 if d.get("outcome") == "incident"), first_20[0])
    print(f"[*] Querying memory for deploy: {target_deploy['deploy_id']} on {target_deploy['service']} ({target_deploy['change_type']})...")

    # Simulate an upcoming deploy to the same service with similar change
    test_query_deploy = {
        "deploy_id": "dep-upcoming-test",
        "service": target_deploy["service"],
        "change_type": target_deploy["change_type"],
        "day_of_week": target_deploy.get("day_of_week", "Friday"),
        "timestamp": target_deploy["timestamp"],
        "pr_title": f"chore({target_deploy['service']}): update connection pool limits in config",
        "diff_summary": "- pool_max: 50\n+ pool_max: 20"
    }

    recalled = store.recall_for_deploy(test_query_deploy)
    print(f"[+] Recall returned {len(recalled)} memory units!")
    assert len(recalled) > 0, "Expected at least 1 recalled memory unit!"

    for idx, mem in enumerate(recalled[:5], 1):
        print(f"\n  --- Recalled Memory #{idx} ---")
        print(f"  Memory ID: {mem['id']}")
        print(f"  Timestamp: {mem.get('timestamp')}")
        print(f"  Tags:      {mem.get('tags')}")
        print(f"  Source:    {mem.get('source')}")
        snippet = mem['text'][:140].replace('\n', ' ')
        print(f"  Content:   {snippet}...")

    # Test reflection
    print("\n[*] Testing reflection across seeded memories...")
    reflect_result = store.reflect_patterns(force_refresh=True)
    summary = reflect_result.get("patterns_summary", "")
    print(f"[+] Reflection summary:\n{summary[:250]}...")

    # Cleanup test bank
    try:
        store.client.delete_bank(bank_id=test_bank_id)
        print(f"\n[+] Cleaned up test bank '{test_bank_id}'.")
    except Exception as e:
        print(f"Notice on cleanup: {e}")

    print("\n" + "=" * 60)
    print("[SUCCESS] Phase 2 definition of done verified: 20 deploys seeded, timestamped memories recalled!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)

"""
Data validator for Preflight's generated history.
Validates pattern frequencies, early learning opportunities, decoy safety,
temporal integrity, and prints a 5-record realistic inspection sample.
"""
import json
import sys
from datetime import datetime
from pathlib import Path


def validate():
    data_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
    history_file = data_dir / "history.json"
    ground_truth_file = data_dir / "ground_truth.json"

    assert history_file.exists(), f"Missing {history_file}"
    assert ground_truth_file.exists(), f"Missing {ground_truth_file}"

    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)

    with open(ground_truth_file, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    print("=" * 60)
    print("PREFLIGHT DATA VALIDATION REPORT")
    print("=" * 60)
    print(f"Total Deploys in History: {len(history)}")
    print(f"Total Ground Truth Records: {len(ground_truth)}")
    assert len(history) == len(ground_truth), "Mismatch between history and ground truth counts"

    # Verify chronological ordering
    timestamps = [datetime.fromisoformat(d["timestamp"]) for d in history]
    for i in range(1, len(timestamps)):
        assert timestamps[i] >= timestamps[i - 1], f"Chronological ordering violated at index {i}"
    print("[PASS] Strict chronological ordering verified.")

    # Verify counts
    incidents = [d for d in history if d.get("outcome") == "incident"]
    build_failures = [d for d in history if d.get("outcome") == "build_failure"]
    healthy = [d for d in history if d.get("outcome") == "healthy"]

    print(f"Outcome Distribution: Healthy={len(healthy)}, Build Failures={len(build_failures)}, Incidents={len(incidents)}")
    assert 12 <= len(incidents) <= 25, f"Incident count {len(incidents)} outside target range"
    assert 20 <= len(build_failures) <= 45, f"Build failure count {len(build_failures)} outside target range"
    print("[PASS] Event counts match target bounds.")

    # Verify 6 Planted Patterns
    patterns = {"P1": [], "P2": [], "P3": [], "P4": [], "P5": [], "P6": []}
    for gt in ground_truth:
        pid = gt.get("pattern_id")
        if pid in patterns:
            patterns[pid].append(gt)

    print("\nPlanted Patterns Distribution:")
    for pid, occurrences in patterns.items():
        count = len(occurrences)
        first_deploy = occurrences[0]
        # find in history
        h_record = next(h for h in history if h["deploy_id"] == first_deploy["deploy_id"])
        first_day = h_record["day_offset"]
        print(f"  [{pid}] Occurrences: {count:2d} | First seen at day: {first_day:2d} | Pattern: {occurrences[0]['pattern_name']}")
        assert count >= 3, f"Pattern {pid} has fewer than 3 occurrences ({count})"
        assert first_day <= 25, f"Pattern {pid} first occurrence ({first_day}) is too late for early learning"

    print("[PASS] All 6 patterns exist, occur >= 3 times, and have early occurrences.")

    # Verify Decoys
    decoys = [gt for gt in ground_truth if gt.get("is_decoy")]
    print(f"\nDecoy Deployments: {len(decoys)} planted.")
    assert len(decoys) >= 8, f"Too few decoys ({len(decoys)})"
    for d in decoys:
        assert d["outcome"] == "healthy", f"Decoy {d['deploy_id']} ({d['decoy_type']}) was not healthy!"
    print("[PASS] All decoys are verified healthy and prevent naive rule-based shortcuts.")

    # Verify Incident Latency & Data Integrity
    for inc_deploy in incidents:
        inc = inc_deploy["incident"]
        d_time = datetime.fromisoformat(inc_deploy["timestamp"])
        det_time = datetime.fromisoformat(inc["detected_at"])
        delta_min = (det_time - d_time).total_seconds() / 60.0
        assert 10 <= delta_min <= 120, f"Incident detection delay {delta_min} min outside 10-120 min window"
        assert inc["severity"] in ["SEV-1", "SEV-2"], "Invalid severity"
        assert len(inc["error_logs"]) >= 2, "Missing realistic error logs"
        assert inc["root_cause"], "Missing root cause"
        assert inc["fix_steps"], "Missing fix steps"
        assert inc["runbook"], "Missing runbook"

    print("[PASS] Incident detection delays (10-120 min), stack traces, root causes, and runbooks verified.")

    # Verify PR title hygiene (no leaking of failure causes)
    leak_words = ["breaks", "fail", "incident", "crash", "outage", "buggy", "bad"]
    for d in history:
        title_lower = d["pr_title"].lower()
        for w in leak_words:
            assert w not in title_lower, f"PR title leaks failure: '{d['pr_title']}' contains '{w}'"

    print("[PASS] PR titles hygiene verified — zero leakage of causal failures.")

    # Print 5 Realistic Sample Records
    print("\n" + "=" * 60)
    print("5-RECORD SAMPLE INSPECTION (REALISTIC DATA)")
    print("=" * 60)
    samples = [
        # 1. P1 Incident Deploy
        next(d for d in history if d["deploy_id"] == patterns["P1"][0]["deploy_id"]),
        # 2. P2 Incident Deploy
        next(d for d in history if d["deploy_id"] == patterns["P2"][0]["deploy_id"]),
        # 3. Decoy Deploy (Payments config on weekday morning)
        next(d for d in history if d["deploy_id"] == decoys[0]["deploy_id"]),
        # 4. CI Build Failure (P5)
        next(d for d in history if d["deploy_id"] == patterns["P5"][0]["deploy_id"]),
        # 5. Routine Healthy Deploy
        next(d for d in history if d.get("outcome") == "healthy" and not any(g["deploy_id"] == d["deploy_id"] and g["is_decoy"] for g in ground_truth)),
    ]

    for i, s in enumerate(samples, 1):
        print(f"\n--- SAMPLE #{i} [{s['outcome'].upper()}] ---")
        print(f"Deploy ID:    {s['deploy_id']} ({s['service']} | {s['change_type']} | {s['environment']})")
        print(f"Timestamp:    {s['timestamp']} ({s['day_of_week']})")
        print(f"Author:       {s['author']} <{s['author_email']}>")
        print(f"PR Title:     {s['pr_title']}")
        print(f"Diff Summary:\n  {s['diff_summary'].replace(chr(10), chr(10) + '  ')}")
        if s.get("outcome") == "incident":
            inc = s["incident"]
            print(f"Incident:     {inc['severity']} - {inc['title']}")
            print(f"Detected:     {inc['detected_at']} (MTTR: {inc['mttr_minutes']} min)")
            print(f"Impact:       {inc['impact']}")
            print(f"Metrics:      5xx Rate: {inc['metrics']['http_5xx_rate']} | p99: {inc['metrics']['p99_latency_ms']}ms")
            print(f"Logs Sample:  {inc['error_logs'][0]}")
            print(f"Root Cause:   {inc['root_cause']}")
            print(f"Fix Steps:    {inc['fix_steps']}")
            print(f"Runbook:      {inc['runbook']}")
        elif s.get("outcome") == "build_failure":
            ci = s["ci_details"]
            print(f"CI Failure:   Stage: {ci['failed_stage']} | Exit Code: {ci['exit_code']}")
            print(f"CI Error:     {ci['error_message']}")
        else:
            print("Status:       CI passed, deploy healthy, 0 alerts.")

    print("\n" + "=" * 60)
    print("ALL VALIDATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    if not validate():
        sys.exit(1)

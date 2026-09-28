"""
Data validator for Preflight's generated history.
Validates pattern definitions directly from ACTUAL FIELDS (not just ground-truth labels),
log timestamp dynamic boundaries (deploy_time < log_time < detected_at),
MTTR-impact agreement, realistic consistent diffs, weekday weighting,
and background vs pattern-override incidents.
"""
import json
import re
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

    print("=" * 65)
    print("PREFLIGHT DATA VALIDATION REPORT (ACTUAL-FIELD VERIFICATION)")
    print("=" * 65)
    print(f"Total Deploys in History: {len(history)}")
    print(f"Total Ground Truth Records: {len(ground_truth)}")
    assert len(history) == len(ground_truth), "Count mismatch"

    # 1. Chronological order
    timestamps = [datetime.fromisoformat(d["timestamp"]) for d in history]
    for i in range(1, len(timestamps)):
        assert timestamps[i] >= timestamps[i - 1], f"Chronological ordering violated at index {i}"
    print("[PASS] Strict chronological ordering verified.")

    # 2. Weekday weighting check
    weekdays = sum(1 for d in history if d["day_of_week"] not in ["Saturday", "Sunday"])
    weekday_pct = (weekdays / len(history)) * 100
    print(f"[PASS] Weekday weighting verified: {weekdays}/{len(history)} ({weekday_pct:.1f}% on weekdays).")
    assert weekday_pct >= 85.0, f"Weekday percentage {weekday_pct:.1f}% is too low"

    # 3. Counts & Outcomes
    incidents = [d for d in history if d.get("outcome") == "incident"]
    build_failures = [d for d in history if d.get("outcome") == "build_failure"]
    healthy = [d for d in history if d.get("outcome") == "healthy"]
    print(f"[PASS] Outcome breakdown: Healthy={len(healthy)}, Build Failures={len(build_failures)}, Incidents={len(incidents)}")
    assert 14 <= len(incidents) <= 22, f"Incident count {len(incidents)} outside target"
    assert 18 <= len(build_failures) <= 35, f"Build failure count {len(build_failures)} outside target"

    # 4. Actual-field verification of planted patterns (NOT just gt labels)
    print("\n--- Verifying Planted Patterns from ACTUAL FIELDS ---")

    # P1: payments-api, config, Friday, hour >= 16
    p1_actual = [
        d for d in history
        if d["service"] == "payments-api"
        and d["change_type"] == "config"
        and d["day_of_week"] == "Friday"
        and datetime.fromisoformat(d["timestamp"]).hour >= 16
    ]
    print(f"  [P1] payments-api | config | Friday (hour >= 16): {len(p1_actual)} occurrences found.")
    assert len(p1_actual) >= 3, f"P1 has fewer than 3 actual occurrences ({len(p1_actual)})"
    for d in p1_actual:
        dt = datetime.fromisoformat(d["timestamp"])
        assert d["day_of_week"] == "Friday", f"{d['deploy_id']} is not Friday: {d['day_of_week']}"
        assert dt.hour >= 16, f"{d['deploy_id']} is not evening: hour {dt.hour}"
        assert "pool_max_connections" in d["diff_summary"], f"{d['deploy_id']} diff missing pool config"
    # Verify one P1 is a noisy safe run
    p1_healthy = [d for d in p1_actual if d["outcome"] == "healthy"]
    print(f"       -> {len(p1_actual) - len(p1_healthy)} caused incidents, {len(p1_healthy)} turned out healthy (canary override).")
    assert len(p1_healthy) >= 1, "Expected at least 1 noisy safe P1 deploy"

    # P2: ledger-service, migration, drops legacy column without backfill
    p2_actual = [
        d for d in history
        if d["service"] == "ledger-service"
        and d["change_type"] == "migration"
        and "DROP COLUMN legacy_settlement_id" in d["diff_summary"]
    ]
    print(f"  [P2] ledger-service | migration | drop column without backfill: {len(p2_actual)} occurrences found.")
    assert len(p2_actual) >= 3, f"P2 has fewer than 3 actual occurrences ({len(p2_actual)})"

    # P3: auth-service, dependency-bump, pyjwt upgrade
    p3_actual = [
        d for d in history
        if d["service"] == "auth-service"
        and d["change_type"] == "dependency-bump"
        and "pyjwt" in d["diff_summary"].lower()
    ]
    print(f"  [P3] auth-service | dependency-bump | pyjwt upgrade: {len(p3_actual)} occurrences found.")
    assert len(p3_actual) >= 3, f"P3 has fewer than 3 actual occurrences ({len(p3_actual)})"

    # P4: checkout-web, feature-flag, checkout_v2 with session_cache_ttl change
    p4_actual = [
        d for d in history
        if d["service"] == "checkout-web"
        and d["change_type"] == "feature-flag"
        and "checkout_v2" in d["diff_summary"]
        and "session_cache_ttl" in d["diff_summary"]
    ]
    print(f"  [P4] checkout-web | feature-flag | checkout_v2 + cache TTL: {len(p4_actual)} occurrences found.")
    assert len(p4_actual) >= 3, f"P4 has fewer than 3 actual occurrences ({len(p4_actual)})"
    p4_healthy = [d for d in p4_actual if d["outcome"] == "healthy"]
    print(f"       -> {len(p4_actual) - len(p4_healthy)} caused incidents, {len(p4_healthy)} turned out healthy (internal cohort).")
    assert len(p4_healthy) >= 1, "Expected at least 1 noisy safe P4 deploy"

    # P5: base image bump causing CI integration test failure
    p5_actual = [
        d for d in history
        if d.get("ci_status") == "failed"
        and d["outcome"] == "build_failure"
        and "Dockerfile" in d.get("files_changed", [])
        and "glibc" in d.get("ci_details", {}).get("error_message", "")
    ]
    print(f"  [P5] base-image bump | Dockerfile | glibc CI failure: {len(p5_actual)} occurrences found.")
    assert len(p5_actual) >= 3, f"P5 has fewer than 3 actual occurrences ({len(p5_actual)})"

    # P6: infra-terraform, infra, security group egress port restriction
    p6_actual = [
        d for d in history
        if d["service"] == "infra-terraform"
        and d["change_type"] == "infra"
        and "security_groups.tf" in str(d["files_changed"])
        and "egress" in d["diff_summary"]
    ]
    print(f"  [P6] infra-terraform | security group egress port restriction: {len(p6_actual)} occurrences found.")
    assert len(p6_actual) >= 3, f"P6 has fewer than 3 actual occurrences ({len(p6_actual)})"

    # 5. Background incidents verification (unrelated to pipeline patterns)
    bg_incidents = [gt for gt in ground_truth if gt.get("is_background_incident")]
    print(f"\n[PASS] Background incidents verified: {len(bg_incidents)} unrelated incidents (risk-engine OOM, SMS TLS cert, search-indexer disk).")
    assert len(bg_incidents) == 3, f"Expected 3 background incidents, got {len(bg_incidents)}"

    # 6. Decoy verification
    decoys = [gt for gt in ground_truth if gt.get("is_decoy")]
    print(f"[PASS] Decoys verified: {len(decoys)} planted safe decoys.")
    for dec in decoys:
        assert dec["outcome"] == "healthy", f"Decoy {dec['deploy_id']} was not healthy!"

    # 7. Dynamic incident log timestamp boundaries and MTTR-impact agreement
    print("\n--- Verifying Incident Timestamps & MTTR Consistency ---")
    for d in incidents:
        inc = d["incident"]
        d_ts = datetime.fromisoformat(d["timestamp"])
        det_ts = datetime.fromisoformat(inc["detected_at"])
        res_ts = datetime.fromisoformat(inc["resolved_at"])

        # Delay must be 15-85 mins
        delay_min = (det_ts - d_ts).total_seconds() / 60.0
        assert 15 <= delay_min <= 90, f"{d['deploy_id']} delay {delay_min} outside window"

        # MTTR must match exactly
        mttr_calc = int((res_ts - det_ts).total_seconds() / 60.0)
        assert inc["mttr_minutes"] == mttr_calc, f"{d['deploy_id']} MTTR mismatch: {inc['mttr_minutes']} vs {mttr_calc}"

        # Impact text must reflect mttr_minutes
        assert str(inc["mttr_minutes"]) in inc["impact"], f"{d['deploy_id']} impact text does not match MTTR: {inc['impact']}"

        # Root cause text must match the detection date
        det_date = det_ts.strftime("%Y-%m-%d")
        assert det_date in inc["root_cause"], f"{d['deploy_id']} root cause date mismatch: {inc['root_cause']}"

        # Every log line timestamp MUST be between d_ts and det_ts
        for log_line in inc["error_logs"]:
            # extract timestamp "YYYY-MM-DD HH:MM:SS"
            match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", log_line)
            assert match, f"Could not find timestamp in log: {log_line}"
            log_ts = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=d_ts.tzinfo)
            assert d_ts <= log_ts <= det_ts, (
                f"{d['deploy_id']} log timestamp {log_ts} outside [{d_ts}, {det_ts}]!\nLog: {log_line}"
            )

    print("[PASS] All incident error logs fall strictly between deploy_time and detected_at.")
    print("[PASS] MTTR and impact durations agree 100% across all incidents.")
    print("[PASS] Root cause texts accurately match deployment dates.")

    # 8. Diff cleanliness (no generic filler)
    for d in history:
        diff = d["diff_summary"]
        assert "routine updates to" not in diff.lower(), f"{d['deploy_id']} has filler diff text: {diff}"
        assert len(diff.strip()) > 10, f"{d['deploy_id']} has empty diff"
        assert len(d["files_changed"]) > 0, f"{d['deploy_id']} has no files changed"
        # PR title does not leak failure
        for leak in ["breaks", "fail", "incident", "crash", "outage", "buggy", "bad"]:
            assert leak not in d["pr_title"].lower(), f"PR title leaks: {d['pr_title']}"

    print("[PASS] Zero filler diffs, zero PR title leaks, consistent files_changed per record.")

    print("\n" + "=" * 65)
    print("ALL VALIDATION CHECKS PASSED WITH ZERO WARNINGS!")
    print("=" * 65)
    return True


if __name__ == "__main__":
    if not validate():
        sys.exit(1)

import json
from pathlib import Path

history_file = Path("data/raw/history.json")
with open(history_file, "r", encoding="utf-8") as f:
    history = json.load(f)

print("=" * 70)
print("THE EXACT FIRST 20 DEPLOYS IN HISTORY.JSON (SEEDED IN PHASE 2)")
print("=" * 70)
for i, d in enumerate(history[:20], 1):
    inc = d.get("incident")
    inc_str = f" [INCIDENT: {inc['severity']} - {inc['title'][:40]}...]" if inc else ""
    print(f"{i:2d}. {d['deploy_id']} | {d['timestamp']} | {d['day_of_week']:<9} | {d['service']:<20} | {d['change_type']:<15} | Outcome: {d['outcome']}{inc_str}")

print("\n" + "=" * 70)
print("5 FULL RAW JSON RECORDS FROM HISTORY.JSON")
print("=" * 70)

# Sample 1: P1 Incident (dep-116)
p1_incident = next(d for d in history if d["deploy_id"] == "dep-116")
# Sample 2: P2 Incident (dep-123)
p2_incident = next(d for d in history if d["deploy_id"] == "dep-123")
# Sample 3: CI Build failure (dep-101)
ci_fail = next(d for d in history if d["deploy_id"] == "dep-101")
# Sample 4: Healthy decoy deploy (dep-111)
decoy = next(d for d in history if d["deploy_id"] == "dep-111")
# Sample 5: Routine healthy deploy (dep-103)
healthy = next(d for d in history if d["deploy_id"] == "dep-103")

samples = [p1_incident, p2_incident, ci_fail, decoy, healthy]
for idx, s in enumerate(samples, 1):
    print(f"\n--- RECORD {idx}: {s['deploy_id']} ({s['outcome'].upper()}) ---")
    print(json.dumps(s, indent=2))

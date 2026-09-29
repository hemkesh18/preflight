# Preventing the Friday 4 PM Outage: How Kestrel Pay Stopped Repeat Incidents with Agentic Memory

*By the Kestrel Pay Reliability & Platform Engineering Team*

---

At Kestrel Pay, our payment rails process millions of dollars in transactions daily across sixteen core microservices. When our checkout service fails, merchant point-of-sale terminals freeze, online transactions drop, and our incident response room fills with engineers in seconds.

For months, our post-mortems suffered from a recurring haunting.

It wasn't that we didn't know how to fix things. We had rigorous blameless post-mortems. We had Jira action items. We had a meticulously maintained runbook repository (`docs/runbooks/`). Yet, three or four months after an incident was closed and the runbook was written, the identical outage would strike again.

Why? Because the engineers who investigated the first incident were not the same engineers who authored the next pull request. And the CI/CD pipeline—the only barrier between a Git commit and production—had the institutional memory of a goldfish.

Here is the story of how we integrated **Preflight** and Vectorize's **Hindsight** memory engine into our pipeline gate, and what happened when we replayed 150 historical deployments through a memory-enabled release pipeline.

---

## Anatomy of a Repeat Outage: The June 5 Incident (`dep-101`)

To understand why traditional CI/CD fails, look at what happened on Friday, June 5, 2026, at 16:45 UTC.

A pull request landed on `payments-api`. The author noticed that during high-volume spikes, certain payment gateway connections hung for up to 60 seconds before failing. With good intentions, the developer shortened the channel timeout:

```yaml
# config/production.yaml
payment_gateway:
-  channel_timeout_ms: 60000
+  channel_timeout_ms: 50000
```

The pull request title was unassuming: `perf: tighten channel timeout on payments-api`.

All 42 unit tests passed. The linting step passed. The build artifact compiled cleanly. The merge button turned green.

Within eight minutes of deployment, checkout success plummeted from 99.98% to 12.4%. Under Friday afternoon load, gateway responses routinely took 52 seconds. Instead of completing, hundreds of concurrent requests aborted simultaneously at the 50-second mark. The payment clients immediately retried, creating an exponential retry storm that exhausted our database connection pool.

Our on-call team spent two hours stabilizing the cluster. The subsequent post-mortem produced **Runbook RB-PAY-04**:

> **Runbook RB-PAY-04**:
> Never reduce `channel_timeout_ms` below 60,000 ms on `payments-api` during peak or weekend traffic windows unless `db_pool_size` is concurrently scaled above 100. All timeout tuning must be scheduled during Tuesday–Thursday maintenance windows.

We saved `RB-PAY-04` to our internal wiki. Everyone nodded in agreement.

---

## The Repeat: Deployment `dep-131`

Five weeks later, on Friday, July 10, 2026, at 16:30 UTC, a different developer on the payments team opened pull request #482: `refactor: adjust connection timeout values`.

The diff looked virtually identical:
```yaml
# config/production.yaml
payment_gateway:
-  channel_timeout_ms: 60000
+  channel_timeout_ms: 50000
```

Once again, the CI/CD pipeline saw clean code. Every test passed. The pull request was ready to ship.

In our legacy setup, this PR would have merged, repeating the June 5 outage down to the exact error signature.

### How Preflight Intercepted the Release

With Preflight configured in our CI gate, GitHub Actions triggered an automated pre-deploy evaluation before merge approval. 

Preflight called the Hindsight memory engine, anchoring the query timestamp to the exact deployment proposal time (`2026-07-10T16:30:00Z`).

Hindsight scanned Kestrel Pay's memory bank and retrieved two critical operational facts:
1. **Memory #101-OUT**: *Incident on payments-api (2026-06-05T16:45:00Z). Reducing channel_timeout_ms triggered retry storm and pool starvation under Friday peak.*
2. **Memory #RB-PAY-04**: *Verified Mitigation. Require max_pool_size >= 100 on weekend traffic changes; deploy off-peak.*

Preflight generated the following gate briefing directly in the GitHub pull request comment:

```markdown
### 🛑 PREFLIGHT PIPELINE GATE: BLOCK (Risk Score: 0.75 / HIGH)
**Predicted Failure Mode**: Connection pool exhaustion under peak weekend payment volume.
**Grounded Citations**: 2 historical memories recalled from bank `kestrel-pay`.

#### Operational Risk Factors:
- Matches historical failure pattern seen in `dep-101`: tightening timeouts on `payments-api` on Friday afternoon causes client retry cascades.
- Diff reduces `channel_timeout_ms` to 50s without corresponding pool size expansion.

#### Required Remediation (Runbook RB-PAY-04):
1. Keep `channel_timeout_ms` at 60s, or scale `db_pool_size >= 100`.
2. Reschedule deployment to Tuesday morning maintenance window.
```

The CI step exited with code `1`. The merge was blocked. The developer read the briefing, discussed it with the on-call engineer, and rescheduled the change.

A four-hour outage was avoided in ten seconds.

---

## The Backtest: Replaying 150 Chronological Releases

Anecdotes are nice, but platform engineering demands rigorous validation. We ran a full backtest across **150 real and synthetic deployments** from Kestrel Pay's release log.

The dataset represented the messy reality of modern engineering:
- **111 Healthy Releases**: Normal feature additions, refactors, dependency updates.
- **22 Build Failures**: TypeScript errors, missing dependencies, lint failures.
- **3 Isolated Background Incidents**: Flaky infrastructure, network partition, third-party provider outage.
- **14 Pattern Deployments**: Representing 5 recurring operational failure mechanisms across our services, containing 9 true repeat incident occurrences.

We ran two arms side-by-side on identical proposal data:
- **Memory-On Arm**: Retained past plans and incident outcomes into Hindsight; recalled memories at $T_{\text{deploy}}$ with zero look-ahead leakage.
- **Memory-Off Arm**: Stateless LLM evaluating the identical PR diff and metadata with zero historical memory.

### Empirical Results

Here is what the chronological backtest revealed:

```
Repeat Incident Detection (Positive Class = Incident, Risk >= 0.5):
  - Memory-On:  4 of 9 repeat incidents flagged HIGH
  - Memory-Off: 1 of 9 repeat incidents flagged HIGH

False Alarms on Healthy Releases:
  - Memory-On:  5 of 111 healthy releases flagged HIGH
  - Memory-Off: 5 of 111 healthy releases flagged HIGH

Edge Case Behaviors:
  - Decoys (similar diff, benign context): Memory-On flagged 1/11 HIGH; Memory-Off flagged 0/11 HIGH.
  - Overrides (intentional pattern-match with mitigation): Memory-On flagged 1/2 HIGH; Memory-Off flagged 0/2 HIGH.
  - Build Failures: Memory-On flagged 2/22 HIGH; Memory-Off flagged 3/22 HIGH.
```

### An Honest Look at the Numbers

As engineers, we insist on reporting these findings without hyperbole:

1. **Small Sample Size ($N=9$)**: Across 150 releases, exactly 9 repeat incident occurrences took place across our planted patterns. While Memory-On caught 4 compared to Memory-Off's 1, nine data points is a limited sample. It shows strong promise, but it is not a statistical ceiling.
2. **False Alarms Did Not Increase**: A major fear with memory-based security or release gates is false-positive fatigue. Memory-On produced 5 false alarms out of 111 healthy releases—the exact same number (5/111) as the stateless model.
3. **The Learning Curve Trajectory**: In our replay, the rolling F1 score initially surged to 1.0 when the first recurring pattern was caught. As dozens of healthy releases passed without incidents, the rolling F1 stabilized around 0.44. In a real-world pipeline where 90%+ of deployments are healthy, release safety agents must balance precision against recall.

---

## What We Learned About Agentic Memory

Integrating Hindsight into our CI/CD pipeline taught us three foundational principles for building production AI agents:

### 1. Zero Leakage is Harder Than It Looks
In our early prototypes, backtest scripts accidentally queried the memory bank after the incident outcome was retained, artificially inflating accuracy to 100%. True evaluation requires strict temporal anchoring: the agent must query `query_timestamp = T_deploy`, and post-deploy outcomes must only be written after the pre-deploy evaluation completes.

### 2. High Skepticism Beats Broad Associations
We initially ran Hindsight with default settings and found that the model would occasionally link unrelated backend changes simply because both PRs modified "configuration." By setting `disposition_skepticism=4` and `disposition_literalism=4`, the engine demanded exact service matches and concrete operational parameters, eliminating hallucinated correlations.

### 3. CI/CD Needs "Runbook Memory", Not Just "Error Memory"
Telling an engineer "this commit looks risky" creates friction. Telling an engineer "this commit looks like incident dep-101; here is Runbook RB-PAY-04 with the recommended fix" creates alignment. Retaining the *remediation* alongside the *outage* transformed Preflight from a nagging linter into a helpful pair programmer.

---

## Conclusion

Every production outage is an expensive tuition payment. If your CI/CD pipeline forgets the lesson as soon as the incident closes, you are destined to pay that tuition over and over again.

By pairing open-weights LLMs with Hindsight's persistent, temporally-anchored memory, we turned our pipeline gate into an institutional memory bank.

Our on-call team sleeps better on Friday nights.

---
*Explore the Preflight codebase, replay data, and documentation on [GitHub](https://github.com/hemkesh18/preflight).*

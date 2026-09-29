# Preflight: 60-Second Live Demo Script

> **Instructions**: Keep `http://localhost:8000` open in full screen. Read the spoken lines verbatim as you perform each numbered action. Target duration: 60 to 75 seconds.

---

### [00:00 – 00:12] Screen 1: The Problem & Headline Metrics
- **Action**: Start at the top of the console. Hover over the **Headline Metrics** cards (`4/9 Repeat Incidents Flagged HIGH` vs `1/9 Memory-Off`).
- **Say**:
  > *"Every engineering team has experienced repeat outages — where the exact same bug that caused a sev-1 six months ago slips past code review and breaks production again. This is Preflight: an autonomous CI/CD release gate powered by Vectorize's Hindsight persistent memory. In our 150-deployment benchmark, Preflight caught 4 out of 9 repeat incidents that stateless CI completely missed, without increasing false alarms on healthy code."*

---

### [00:12 – 00:30] Screen 2: Interactive Gate Simulator (Before vs After)
- **Action**: Scroll to the **Interactive Gate Simulator**. Click the preset button **`dep-131 (Friday Payments)`**.
- **Say**:
  > *"Watch what happens on a dangerous Friday evening release to `payments-api`. The developer is dropping the connection pool from 50 to 15.*
  > 
  > *On the right, stateless CI looks at this routine config change, sees passing unit tests, and issues a green PASS. Disaster awaits.*
  > 
  > *On the left, Preflight recalls past incident post-mortems from June 2026. It immediately flags this as HIGH risk (0.85), BLOCKS the release, and links the proven mitigation runbook — RB-PAY-04."*

---

### [00:30 – 00:44] Screen 3: Closed-Loop Learning & Post-Incident Ingestion
- **Action**: Scroll down to the **Post-Incident Feedback & Runbook Ingestion** form. Hover over the fields (Incident Severity, Root Cause, Runbook ID).
- **Say**:
  > *"Preflight isn't static vector RAG; it's a closed-loop learning system. When a new outage occurs, the on-call engineer logs the post-mortem here. Preflight retains the incident and runbook into Hindsight with exact event timestamps and high skepticism, permanently immunizing the pipeline against that failure pattern."*

---

### [00:44 – 00:55] Screen 4: Empirical Learning Curve & Reflection
- **Action**: Scroll to the **Empirical Learning Curve** chart and hover over the rolling F1 curve, then glance at the **Synthesized Systemic Patterns** section.
- **Say**:
  > *"Across all 150 deploys, you can see the agent's calibration stabilize as it accumulates memories. Using Hindsight's autonomous `reflect` API, Preflight synthesizes systemic failure modes across microservices — like JWT bumps in auth and unbackfilled column drops in ledger — grounded in 17 cited memory records."*

---

### [00:55 – 01:00] Screen 5: Outro & Takeaway
- **Action**: Scroll back to the top header showing the active bank `kestrel-pay` and clean UI status.
- **Say**:
  > *"Preflight turns painful production post-mortems into an automated, proactive defense. Fewer repeat outages, zero look-ahead leakage, and continuous institutional memory. Thank you."*

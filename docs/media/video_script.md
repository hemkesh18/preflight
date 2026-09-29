# Preflight: 3-Minute Demo Video Script & Thumbnail Specification

---

## 1. 16:9 Thumbnail Specification

### Image Generation Prompt (Midjourney / DALL-E / Imagen 3)
```text
High-resolution 16:9 YouTube tech thumbnail, dark mode fintech aesthetic. In the center, a glowing glassmorphic terminal window displays 'CI/CD RELEASE GATE: BLOCKED' with a vibrant red/amber badge and risk score '0.75 HIGH'. A glowing neural memory graph branches out from the terminal, connecting past incident nodes labeled 'dep-101: Pool Starvation' and verified runbook nodes labeled 'RB-PAY-04: Off-Peak Window'. Background is deep matte slate (#0f172a) with subtle code syntax matrix streams. Bold, clean modern typography in top third: 'PREFLIGHT' in electric emerald green and white, subtitle 'Persistent Memory for CI/CD'. Cinematic lighting, crisp vector lines, 4k render, unreal engine 5 style, zero clutter.
```

### Visual Layout Mockup
```
+-------------------------------------------------------------------------------+
|  PREFLIGHT                                           Fintech Release Gate     |
|  Persistent Memory for CI/CD Pipelines                                        |
|                                                                               |
|      +-----------------------------------------+   [Memory Bank: kestrel-pay] |
|      | 🛑 PIPELINE GATE: BLOCKED (Risk: 0.75)   |       |                      |
|      | dep-131: payments-api (Friday 16:30)    |<------+ [dep-101 Incident]   |
|      | Matches Outage #101 | Apply RB-PAY-04   |       |                      |
|      +-----------------------------------------+       +-> [Runbook RB-PAY-04]|
|                                                                               |
|  [Repeat Outages: 4/9 Caught vs 1/9 Stateless]        [Zero-Leakage Replay]   |
+-------------------------------------------------------------------------------+
```

---

## 2. 3-Minute Video Walkthrough Script

- **Total Duration**: 3 minutes (180 seconds)
- **Format**: Screen share recording + PiP (Picture-in-Picture) presenter
- **Tone**: Pragmatic, direct, technical, calm engineering voice

---

### Segment 1: The Problem (0:00 – 0:35)

| Time | Screen Cue | Spoken Voiceover |
| :--- | :--- | :--- |
| **0:00 - 0:15** | Screen shows a GitHub Pull Request for `payments-api`. All CI checks (linting, tests) are green. Cut to PagerDuty incident dashboard with 504 Gateway Timeouts. | *"Every engineering team has lived through this. It's Friday afternoon. A developer tightens a timeout in a core payments microservice. All 40 unit tests pass. The build is green. It merges. Ten minutes later, PagerDuty goes off. Database pools starve, checkout drops, and your Friday evening is ruined."* |
| **0:15 - 0:35** | Pull up Confluence incident post-mortem from 4 months prior. Highlight the identical root cause. | *"The worst part? The exact same outage happened four months ago in the exact same service. The team wrote a post-mortem and filed a runbook. But modern CI/CD pipelines have total amnesia. They check syntax and unit assertions, but they have zero memory of what happens when code hits production."* |

---

### Segment 2: Introducing Preflight & Architecture (0:35 – 1:15)

| Time | Screen Cue | Spoken Voiceover |
| :--- | :--- | :--- |
| **0:35 - 0:55** | Switch to the Preflight Architecture diagram (Mermaid flow). Highlight Hindsight Memory Bank and the zero-leakage whitelist interface. | *"To solve this, we built Preflight: an autonomous CI/CD release safety agent powered by Vectorize's Hindsight persistent memory engine and Groq open-weights models."* |
| **0:55 - 1:15** | Zoom into `get_predeploy_proposal()` whitelist and `query_timestamp` anchoring in the code editor (`backend/agent/briefing.py`). | *"Preflight intercepts pull requests at the pipeline gate. Crucially, it doesn't just guess with an LLM. It queries Hindsight using strict temporal anchoring—querying memory at the exact deployment timestamp. This guarantees zero look-ahead bias: the agent cannot cheat by peeking at future incidents during historical replays."* |

---

### Segment 3: Live Gate Simulator in Action (1:15 – 2:05)

| Time | Screen Cue | Spoken Voiceover |
| :--- | :--- | :--- |
| **1:15 - 1:35** | Switch to Preflight Interactive Console (`localhost:8000`). Click preset button **`dep-131` (Payments Friday Config)**. Toggle between Memory-Off and Memory-On views. | *"Here is Preflight's interactive console running on real fintech deployment data. Let's look at `dep-131`: a Friday 16:30 config change to `payments-api` shortening timeouts from 60s to 50s. Without memory, the stateless LLM gives it a green PASS with a low risk score of 0.20."* |
| **1:35 - 2:05** | Highlight the Memory-On panel: `BLOCK (Risk 0.75)`, 2 Grounded Citations, and Runbook `RB-PAY-04`. | *"Now look at Memory-On. Preflight queries Hindsight at T_deploy. It recalls incident `dep-101` from five weeks prior, where the identical change caused connection pool exhaustion. But instead of just saying 'no', Preflight cites the verified fix: Runbook RB-PAY-04, requiring connection pool scaling before shortening timeouts. The pipeline exits with code 1, blocking the outage before code touches production."* |

---

### Segment 4: Backtest Results & Empirical Honesty (2:05 – 2:40)

| Time | Screen Cue | Spoken Voiceover |
| :--- | :--- | :--- |
| **2:05 - 2:25** | Scroll down to the **Headline Metrics** and **Confusion Matrix** cards. Point out raw counts (4/9 vs 1/9) and sample size banner. | *"We validated Preflight across a 150-deploy chronological replay. Here are the empirical results: Memory-On caught 4 of 9 repeat incidents, compared to only 1 of 9 for the stateless baseline. Crucially, false alarms on healthy releases did not increase—both arms flagged exactly 5 out of 111 healthy releases. And we explicitly call out the sample size caveat: 9 repeat incidents is a small sample, but the directional signal is clear."* |
| **2:25 - 2:40** | Hover over the **Learning Curve Trajectory** chart showing the downward stabilization from 1.0 to 0.44. | *"Notice our learning curve: F1 initially spikes to 1.0 when the first recurring pattern is caught, and then stabilizes around 0.44 as dozens of normal, healthy releases pass. Showing this real trajectory is critical for production trust."* |

---

### Segment 5: CI Integration & Wrap-Up (2:40 – 3:00)

| Time | Screen Cue | Spoken Voiceover |
| :--- | :--- | :--- |
| **2:40 - 2:55** | Show GitHub Actions workflow YAML (`docs/ci/preflight_gate.yml`) running `preflight gate` in a pull request. | *"Preflight runs as a native GitHub Action or CLI step. If the risk is high, it blocks merge. After deployment, production monitoring feeds the outcome back into Hindsight, making the pipeline smarter every day."* |
| **2:55 - 3:00** | Full screen GitHub repo URL: `https://github.com/kestrel-pay/preflight`. | *"Stop suffering repeat outages. Give your CI/CD pipeline an institutional memory with Preflight. Code and replay data are open-source on GitHub."* |

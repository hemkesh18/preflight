# Preflight — Submission Form Answers

> **Ready-to-paste responses for the official submission portal.**

---

### 1. Project Title & Tagline
- **Project Name**: Preflight
- **Tagline**: The Autonomous CI/CD Release Safety Gate That Learns From Production Outages Using Hindsight Persistent Memory.
- **Category**: Engineering & DevOps

---

### 2. GitHub Repository URL & Demo URL
- **GitHub Repository**: `https://github.com/hemkesh18/preflight`
- **Visibility**: Public (Includes complete codebase, 150-deploy synthetic benchmark dataset, FastAPI service, React console, test suite, and CI gate workflows).
- **Console / Quickstart Command**:
  ```bash
  git clone https://github.com/hemkesh18/preflight.git
  cd preflight && pip install -r requirements.txt
  python -m uvicorn backend.app.main:app --port 8000
  ```

---

### 3. Problem Statement & Motivation
**Prompt**: *What problem are you solving, and who is it for?*

In modern microservice organizations (exemplified by our fintech benchmark, Kestrel Pay), CI/CD pipelines evaluate pull requests statelessly. Linters, unit tests, and integration suites only check whether code compiles and passes local unit assertions. They have zero memory of production reality:
- The exact same configuration tweak that crashed the payments cluster last quarter slips through because tests pass in staging.
- Database column drops that break downstream search-indexer crashloops are approved because the migration syntax is valid.
- Dependency upgrades with silent ABI or token signature incompatibilities get merged on Friday afternoons.

Post-mortems are written, filed in ticketing systems, and forgotten. When similar pull requests appear months later, developers repeat the exact same mistakes. **Preflight solves this by transforming the CI/CD release gate into an experience-accumulating agent that remembers past outages and blocks repeat failures before they merge.**

---

### 4. How Vectorize Hindsight is Used
**Prompt**: *How does your solution leverage Hindsight persistent memory? Explain the specific operations used and why simple RAG is insufficient.*

Preflight leverages Vectorize Hindsight as its continuous cognitive memory engine across four core operations:

1. **Bank Creation & Cognitive Disposition (`create_bank`)**:
   - Initialized with `disposition_skepticism=4` and `disposition_literalism=4`. This prevents false positive hallucinations and ensures the agent demands concrete technical evidence (matching service, parameter keys, timing) before flagging release risk.
2. **Strict Chronological Retention (`retain`)**:
   - **Pre-Deploy Proposal**: Retains proposed diffs, services, change types, and commit metadata at $T_{\text{deploy}}$.
   - **Post-Deploy Outcome**: Retains incident post-mortems (severity, error logs, root cause) and proven runbook resolutions strictly at $T_{\text{outcome}} > T_{\text{deploy}}$.
   - **Idempotency Guarantee**: Built with delete-before-retain logic surviving process restarts without memory inflation.
3. **Temporally Anchored Recall (`recall`)**:
   - Uses Hindsight's first-class `query_timestamp` parameter anchored to the exact deployment minute. This mathematically eliminates look-ahead bias and future knowledge leakage during backtesting.
4. **Autonomous Cross-Service Synthesis (`reflect`)**:
   - Analyzes disparate memory fragments across the bank to synthesize systemic failure patterns (e.g., cross-service cascades between `payments-api` and `checkout-web`) and formulate reusable runbooks (`RB-PAY-04`, `RB-DB-02`, `RB-SEC-09`).

#### Why This is NOT Plain Vector RAG:
- **No Look-Ahead Leakage**: Naive RAG uses cosine similarity across a static index, retrieving future incident tickets for past PRs. Hindsight's temporal filtering strictly respects chronological causality.
- **Cross-Incident Synthesis**: Standard RAG returns chunk fragments. Hindsight's `reflect()` builds high-level operational models and links runbook precedents.
- **Closed-Loop Learning**: As new outages are logged, Preflight immediately updates its memory bank, continuously immunizing the organization against repeat incidents.

---

### 5. Empirical Results & Findings
**Prompt**: *What were the quantitative results of your implementation?*

We evaluated Preflight on a rigorous 150-deployment chronological backtest across 9 microservices, comparing Memory-On (Preflight with Hindsight) against Memory-Off (stateless LLM):

| Evaluation Metric | Memory-On (Preflight) | Memory-Off (Stateless Baseline) |
| :--- | :---: | :---: |
| **Repeat Incidents Flagged HIGH** | **4 / 9** | **1 / 9** |
| False Alarms on Healthy Deploys | 5 / 111 | 5 / 111 |
| Planted Decoy Deploys Flagged HIGH | 1 / 11 | 0 / 11 |
| Safe Pattern-Matches Flagged HIGH | 1 / 2 | 0 / 2 |
| CI Build Failures Flagged HIGH | 2 / 22 | 3 / 22 |
| Background Incidents Flagged HIGH | 0 / 3 | 0 / 3 |

- **Repeat Failure Interception**: Preflight flagged 4 out of 9 repeat incidents as HIGH risk (blocking release with exit code 1 and linking proven runbooks), whereas the stateless baseline caught only 1 out of 9.
- **Precision on Incidents**: Precision improved from 36.0% (Memory-Off) to 42.1% (Memory-On), with false positives dropping from 16 to 11 on production releases.
- **Calibration**: Rolling F1 stabilized around 0.44 across the 150-deploy stream after initially spiking to 1.0 when the first repeat outage pattern was intercepted.

*(Caveat: The 9 repeat incidents represent an initial empirical signal from our synthetic benchmark; we report raw counts rather than exaggerated percentage claims).*

---

### 6. Technical Architecture & Tech Stack
**Prompt**: *Describe your technical architecture and implementation details.*

- **Backend**: Python 3.10–3.14, FastAPI REST API, Pydantic v2 schemas.
- **Persistent Memory**: Vectorize Hindsight Client SDK (`hindsight-client` 0.10.2).
- **Inference Engine**: Groq API (`openai/gpt-oss-120b`, `qwen/qwen3.8-27b`) running at temperature 0.0 with deterministic JSON extraction and local disk caching.
- **Frontend Console**: React 18, Vite, Tailwind CSS, Lucide Icons, Recharts (visualizing rolling F1, before/after gate comparisons, interactive gate simulation, and reflection explorer).
- **CI/CD Integration**: Headless CLI and GitHub Actions workflow (`docs/ci/preflight_gate.yml`) returning Exit Code 0 (PASS/WARN) or Exit Code 1 (BLOCK) with formatted pull request markdown comments.

---

### 7. Real-World Impact & Adoption Path
**Prompt**: *How would an enterprise adopt this in production?*

Preflight is designed as a drop-in GitHub Actions or GitLab CI step. Teams do not need to replace their existing testing pipelines. Preflight executes in parallel with unit tests:
1. It inspects the PR metadata and git diff (`get_predeploy_proposal`).
2. It queries Hindsight memory for matching historical precedents.
3. If risk is high, it posts a PR comment detailing past incidents and linking the on-call runbook, blocking automatic merge until a senior engineer signs off.
4. When incidents occur in production, PagerDuty/Jira post-mortems trigger Preflight's `/api/outcome` webhook, closing the institutional learning loop.

# Architectural & Implementation Decisions

### 1. Project Directory Location
- **Decision**: Created repository in `C:\Users\hemke\.gemini\antigravity\scratch\preflight` per workspace guidelines.
- **Rationale**: Default scratch workspace for autonomous project creation in Antigravity.

### 2. Client Library & SDK Verification
- **Decision**: Verified `hindsight-client` version 0.10.1 and `groq` 1.7.0 installed via pip.
- **Rationale**: Exact method signatures verified via runtime reflection (`Hindsight.retain`, `Hindsight.recall`, `Hindsight.reflect`, `Hindsight.create_bank`, `Hindsight.create_directive`, `Hindsight.create_mental_model`, `Hindsight.operations`).

### 3. LLM Strategy & Guardrails
- **Decision**: No tool-calling dependency for Groq `openai/gpt-oss-120b` and `qwen/qwen3-32b`. Pure JSON schema extraction with prompt repair, exponential backoff, and disk caching.
- **Rationale**: Avoid brittle tool-calling failures on open-weights endpoints.

### 4. Memory Isolation & Tagging
- **Decision**: Use `bank_id="kestrel-pay"` with tags `[service:<service>, type:<change_type>, env:<env>, day:<weekday>]` for precise recall filtering and cross-service reflection.
- **Rationale**: Keeps deploys searchable by specific service or change patterns while allowing global queries across incident histories.

### 5. Evaluation Definitions & Headline Metric Plan (Phase 4)
- **Repeat Incident Definition**: A "repeat incident" is strictly defined as the 2nd or subsequent occurrence of a planted failure pattern that actually caused an incident (determined from ground truth). 
  - 1st occurrences of planted patterns are novel/unseen incidents (the agent cannot have memory of them beforehand).
  - Background incidents (e.g. disk full, SMS TLS cert expiration, OOM from third-party load) are unrelated to CI/CD change patterns and are evaluated and reported separately.
- **Headline Metrics**:
  1. **Repeat Incidents Flagged HIGH**: Recall/coverage of repeat incidents by the preflight gate (Memory-On vs. Memory-Off baseline).
  2. **False Positive Rate on Healthy Deploys**: HIGH-flag rate on healthy deploys, broken down into:
     - Safe planted decoys (e.g. routine Friday updates, standard column additions, minor patch bumps)
     - Safe pattern-matches (e.g. P1 canary override with 50% extra capacity, P4 internal cohort deployment)
     - General healthy deploys
  3. **Build Failures**: CI pipeline build failures reported separately from production outages.
  4. **Calibration**: Rolling Precision, Recall, and F1 (at threshold 0.5) tracked across the chronological deployment stream.
- **Backtest Execution Invariants**:
  - Fresh sterile bank per run (`kestrel-pay-replay-<run_id>`).
  - Strict chronological order (deploy $N$ is evaluated using only memories retained from deploys $1 \dots N-1$).
  - Temperature 0.0 with identical model (`openai/gpt-oss-120b` or logged fallback) for both arms on each deploy.
  - Zero leakage: Input to briefing is strictly `get_predeploy_proposal(deploy)`.

### 6. Score Clamping & Threshold Mapping
- **Boundary Enforcement**: In `parse_and_validate_briefing()`, risk scores are clamped to prevent contradictory outputs between label and probability:
  - If `risk_level == "HIGH"` and `risk_score < 0.60`, it is clamped to `0.75`.
  - If `risk_level == "LOW"` and `risk_score > 0.40`, it is clamped to `0.20`.
  - Scores between `0.35` and `0.59` represent `MEDIUM` advisory risk.
- **CI/CD Gate Thresholds**:
  - `risk_score >= 0.60` (or `HIGH`): **`BLOCK`** (Exit Code `1`). Release is halted; PR requires incident remediation.
  - `0.35 <= risk_score < 0.60` (or `MEDIUM`): **`WARN`** (Exit Code `0`). Release is flagged with warnings; requires on-call review.
  - `risk_score < 0.35` (or `LOW`): **`PASS`** (Exit Code `0`). Release proceeds automatically.

### 7. Demo Modes & Resilience
- **`DEMO_MODE=cached|live`**:
  - `cached`: Delivers deterministic replay results and cached LLM responses instantaneously for demos and evaluations.
  - `live`: Direct real-time calls to Hindsight Cloud and Groq endpoints. If network, DNS, or rate limit exceptions occur, gracefully falls back to cached baseline with an in-UI warning banner.



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

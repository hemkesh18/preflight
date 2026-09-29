# Social Media Posts

---

## Post 1: LinkedIn / Long-Form (Karpathy Style)

```
Most CI/CD pipelines have complete amnesia. 

A PR changes connection timeout from 60s to 50s on a Friday afternoon. All 40 unit tests pass. Linter is green. It merges. Production crashes 10 minutes later under peak load. 

The worst part? The exact same outage happened 4 months ago in the same service. The post-mortem existed, but the CI gate had zero memory of it.

We built Preflight to test if giving CI/CD persistent memory could prevent repeat outages.

Using Vectorize’s Hindsight API, Preflight retains past incidents, stack traces, and runbooks. When a PR arrives, it recalls prior failures at T_deploy with strict temporal anchoring (zero look-ahead leakage).

In a 150-deploy chronological replay:
- Caught 4 of 9 repeat incidents (vs 1 of 9 without memory)
- False alarms on healthy releases stayed flat (5/111 on both arms)
- Early F1 hit 1.0, then stabilized around 0.44 as healthy deploys accumulated

Key takeaway: AI agents shouldn’t just memorize failures; they need runbooks ("what worked before") to suggest fixes, not just block PRs.

Code + replay dataset: https://github.com/kestrel-pay/preflight

#AIAgents #AI #Hindsight #AgentMemory #LLM #DevOps
```

*(Character count: 778 characters)*

---

## Post 2: X (Twitter) / Thread Starter

```
Why do teams suffer repeat production outages? 

Because post-mortems live in docs, while CI/CD pipelines have zero memory. Linters check syntax; they don't remember that changing this specific timeout on Friday breaks checkout.

We built Preflight: an agentic CI gate with persistent memory via Hindsight.

Tested across 150 chronological deploys:
• Caught 4/9 repeat incidents (stateless LLM caught 1/9)
• 0 increase in false alarms on healthy code (5/111 on both)
• Strictly zero look-ahead leakage via temporal anchoring

The difference between a nagging linter and an operational agent is runbook recall: citing past incident dep-101 + Runbook RB-PAY-04 turns a gate block into actionable pair-programming.

Repo: https://github.com/kestrel-pay/preflight

#AIAgents #AI #Hindsight #AgentMemory #LLM
```

*(Character count: 785 characters)*

---

## Post 3: Short Technical Takeaway (X / LinkedIn)

```
Interesting finding from our 150-deploy CI memory backtest:

Giving an LLM release gate persistent memory (Hindsight) flagged 4/9 repeat outages (vs 1/9 baseline) without increasing false alarms on healthy releases (5/111 on both).

Three things made it work:
1. High skepticism (skepticism=4) to prevent hallucinated correlations
2. Temporal anchoring (query_timestamp = T_deploy) to eliminate look-ahead bias
3. Storing runbooks alongside incidents so the agent suggests the verified fix, not just a generic warning.

Full architecture & interactive replay dashboard:
https://github.com/kestrel-pay/preflight

#AIAgents #AgentMemory #Hindsight #LLM #DevOps
```

*(Character count: 681 characters)*

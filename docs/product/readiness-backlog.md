# Release-Readiness Backlog

Measured from the 2026-07-18 scorecard. Priority score is
`(impact x reach x confidence) / effort`, using 1-5 impact/reach/effort and
0-1 confidence. Severity remains the release-order override.

| Priority | Severity | Work item | I | R | C | E | Score | Exit evidence |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | P0 | Resolve every real draft/unscored artifact | 5 | 5 | 0.95 | 3 | 7.92 | Each real artifact is confirmed, rejected, retired, or explicitly queued for rerun; all-zero shared judge outputs are rerun or retired; no silent draft authority |
| 2 | P1 | Persist explicit model role and role provenance | 4 | 4 | 0.95 | 2 | 7.60 | Registry and inventory distinguish declared from inferred roles; migrations and tests pass |
| 3 | P1 | Backfill or rerun missing throughput, RAM, and quantization evidence | 5 | 5 | 0.90 | 3 | 7.50 | Every frontier candidate has tokens/sec and peak RAM; quant source is measured, declared, or inferred |
| 4 | P1 | Add service-health and action preflight summary | 4 | 4 | 0.90 | 2 | 7.20 | Home shows judge, reviewer, provider, Qdrant, runtime commands, and precise remediation before actions |
| 5 | P1 | Publish one end-to-end confirmed decision case study | 5 | 4 | 0.90 | 3 | 6.00 | A sanitized case covers candidate, capture, config, scoring, independent review, confirmation, comparison, and decision |
| 6 | P1 | Convert dense mobile rows to summary plus details | 4 | 4 | 0.80 | 4 | 3.20 | Inventory, Runs, Reviews, and Radar pass 390x844 without hidden actions or ambiguous horizontal scrolling |
| 7 | P1 | Add retrieval evaluation for embedding/reranker models | 4 | 3 | 0.85 | 4 | 2.55 | Local dataset reports retrieval quality, latency, index size, memory, and role-specific recommendation |
| 8 | P1 | Prove interrupted-batch retry and idempotency | 4 | 3 | 0.80 | 4 | 2.40 | Controlled interruption cleans up model state and resumes without duplicate artifacts/imports |
| 9 | P2 | Add evidence-completeness score per run/model | 3 | 4 | 0.90 | 2 | 5.40 | Missing fields and authority states collapse into an explainable completeness percentage and next action |
| 10 | P2 | Measure cold startup and active-batch resource cost | 3 | 3 | 0.80 | 3 | 2.40 | Extend the completed warmed-route and idle-process baseline with cold startup, active-batch CPU/RAM, queue latency, and model-load churn on the target Mac |
| 11 | P2 | Prototype resource-aware batch ordering | 4 | 3 | 0.65 | 5 | 1.56 | Experiment predicts load fit and reduces avoidable model churn without hiding queue order |
| 12 | P3 | Prototype multi-judge consensus | 3 | 2 | 0.55 | 5 | 0.66 | Offline experiment improves agreement analysis without granting automatic confirmation authority |

## Release Sequence

1. Close the P0 authority backlog before adding new evaluation breadth.
2. Complete metadata, preflight, recovery, and mobile work until every readiness
   criterion reaches at least 4.0/5.
3. Raise utility, trust, reliability, and privacy to at least 4.5/5 with live
   evidence.
4. Start P2 innovation only after trust and reliability both clear 4.5/5.

Do not raise the readiness score for code presence alone. A backlog item moves a
score only after its exit evidence is captured.

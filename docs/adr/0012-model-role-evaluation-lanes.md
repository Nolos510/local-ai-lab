# ADR 0012: Separate model roles into evidence-specific evaluation lanes

## Status

Accepted

## Context

The local inventory can contain chat generators, embedding models, rerankers,
and multimodal models. Treating every installed model as a chat generator made
retrieval-only models eligible for generative benchmark queues and LLM scoring.
That produced misleading failures and could create meaningless portfolio
recommendations.

Machine-generated evaluation scores also need a clear authority boundary. A
single local judge is useful for drafting, but its output is not strong enough
to become canonical without independent evidence review and an explicit owner
decision.

## Decision

- Classify models conservatively as `generator`, `embedding`, `reranker`,
  `multimodal`, or `unknown` using explicit runtime metadata first and known
  naming signals second.
- Keep unknown and multimodal models eligible for generation unless stronger
  metadata says otherwise; never silently exclude an unfamiliar generator.
- Exclude embedding and reranker models from generative Run All, LLM scoring,
  generative comparisons, and the tokens/sec versus RAM efficiency frontier.
- Keep non-generative models visible in inventory with an explanation and a
  retrieval-evaluation next action.
- Treat judge output as `draft-scores.json`. Require an independent local
  reviewer record before exposing confirmation controls.
- Require explicit human acknowledgement to create canonical `scores.json` and
  import the confirmed result.
- Never infer a benchmark score or fabricate missing run metrics.

## Consequences

- Inventory status becomes more honest: installed does not mean generatively
  runnable.
- Retrieval-model quality still needs a dedicated benchmark lane before those
  models can be compared usefully.
- Independent review adds local compute and time, but preserves a clear human
  authority boundary.
- Conservative `unknown` handling avoids false negatives while keeping role
  provenance visible.

## Alternatives considered

- **Score every installed model with the LLM rubric.** Rejected because the
  rubric is invalid for vector encoders and rerankers.
- **Hide non-generative models.** Rejected because inventory should explain all
  detected model files and support storage decisions.
- **Automatically confirm close judge agreement.** Rejected because two local
  model outputs are supporting evidence, not owner approval.
- **Require complete hand-maintained role metadata.** Rejected for initial
  inventory discovery; safe classification signals provide useful defaults
  while explicit metadata remains authoritative.

## Follow-up work

- Add retrieval datasets and metrics for embedding and reranker evaluation.
- Persist explicit role/provenance metadata in the registry schema.
- Add workload-aware portfolio recommendations only after each lane has
  trustworthy evidence.

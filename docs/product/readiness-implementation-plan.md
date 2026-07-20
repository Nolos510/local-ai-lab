# Release-Readiness Implementation Plan

This plan turns the readiness scorecard into narrow implementation packets. It
does not authorize parallel edits to shared files. Before starting a packet,
claim its paths in `docs/agent-ledger.md`, inspect the current dirty tree, and
read `AGENTS.md`.

## Delivery Order

| Packet | Gate | Depends on | Outcome |
|---|---|---|---|
| R0 | P0 | Human owner | Every real score artifact has explicit authority or a superseding rerun |
| R1 | P1 | R0 inventory decisions | Model role and role provenance persist across import/export |
| R2 | P1 | R0 | Frontier candidates have complete, source-labeled run configuration and resource evidence |
| R3 | P1 | Stable R0-R2 behavior | Interrupted batches recover without duplicate artifacts or leaked model state |
| R4 | P1 | Stable page contracts | Core pages pass desktop, tablet, mobile, and keyboard verification |
| R5 | P1 | R0-R4 | One sanitized case study proves the full decision workflow |
| R6 | P1 | New ADR plus R1 | Embedding and reranker models receive retrieval-specific evaluation |

Do not start optional recommendation, scheduling, or multi-judge experiments
until Evaluation trust and Reliability and recovery both reach `4.5/5`.

## R0: Close Recommendation Authority

**Owner:** Human product owner, supported by the evaluation lead.

**Inputs:**

- `reports/readiness/2026-07-18/draft-disposition.md`
- `/reviews`
- artifact detail pages and their local evidence

**Procedure:**

1. Retire or reclassify the BGE-M3 LLM-lane artifact.
2. Rerun or retire capture-error, empty-evidence, and shared-zero artifacts.
3. Adjudicate label-only disagreements.
4. Resolve metric disagreements through human review, advisory third-judge
   evidence, or a clean rerun.
5. Regenerate imports, reports, and the readiness scorecard.

**Acceptance:**

- The P0 exit evidence in the disposition report passes.
- No machine-only action grants confirmed authority.
- Published recommendations cite confirmed artifacts only.

**Non-goals:** changing rubric thresholds to make drafts easier to confirm;
silently deleting inconvenient evidence; treating judge agreement as owner
approval.

## R1: Persist Model Role And Provenance

**Expected paths:**

- `apps/model-dashboard/model_dashboard/db.py`
- `apps/model-dashboard/model_dashboard/csv_io.py`
- `apps/model-dashboard/model_dashboard/model_roles.py`
- `apps/model-dashboard/model_dashboard/pages/inventory.py`
- `apps/model-dashboard/model_dashboard/pages/runs.py`
- corresponding dashboard tests

**Contract:**

- Persist `model_role` and `model_role_source` using a backward-compatible
  migration.
- Supported roles begin with `generator`, `embedding`, `reranker`,
  `multimodal`, and `unknown`.
- Provenance distinguishes declared registry metadata from runtime inspection
  and conservative inference.
- `unknown` never enters Run All or generative scoring automatically.
- CSV export/import round-trips both fields without converting inferred role to
  declared role.

**Tests and exit evidence:**

- Legacy databases migrate without data loss.
- Declared role survives export and import.
- Embedding, reranker, and unknown fixtures remain excluded from LLM scoring.
- Inventory displays role, source, explanation, and the correct evaluation lane.

**Non-goals:** adding a second vector database; building retrieval evaluation in
this packet; expanding inference heuristics to guess aggressively.

## R2: Complete Run And Frontier Evidence

**Expected paths:**

- `apps/model-dashboard/model_dashboard/run_config.py`
- `apps/model-dashboard/model_dashboard/pages/actions.py`
- `apps/model-dashboard/model_dashboard/csv_io.py`
- `apps/model-dashboard/model_dashboard/pages/runs.py`
- `evals/local-llm-benchmark/harness.py`
- dashboard and harness tests

**Contract:**

- Every future benchmark records quantization, context window, temperature, and
  top-p in its command metadata and import rows.
- Every field carries `measured`, `declared`, or `inferred` provenance.
- Quantization inference may use a recognized model name, registry value, LM
  Studio source path, or GGUF filename; the UI never labels inference as
  measured.
- Throughput and peak RAM are required for efficiency-frontier eligibility.
- Missing performance evidence produces an explicit exclusion and rerun action,
  not a zero value.
- Rerun-missing-evidence creates a fresh run ID and never overwrites the old
  artifact.

**Tests and exit evidence:**

- New Ollama and LM Studio fixtures preserve all four run settings and their
  sources through artifact, CSV, database, and report.
- Frontier tests reject either missing tokens/sec or missing peak RAM.
- A live rerun records both fields and explains any remaining exclusion.
- Historical inferred quantization remains visibly labeled.

**Non-goals:** inventing RAM data for old runs; running all installed models;
changing the benchmark rubric.

## R3: Prove Batch Recovery And Idempotency

**Expected paths:**

- `apps/model-dashboard/model_dashboard/pages/actions.py`
- `apps/model-dashboard/model_dashboard/server.py`
- `apps/model-dashboard/model_dashboard/pages/inventory.py`
- `apps/model-dashboard/tests/test_run_all.py`
- `evals/local-llm-benchmark/harness.py` only when lifecycle behavior requires it

**Contract:**

- Distinct states remain queued, loading, running, captured, scoring, reviewing,
  completed, skipped, and failed.
- Capture success plus score failure reads `Capture passed / Scoring pending`.
- Dashboard-loaded LM Studio models unload in cleanup after success,
  interruption, timeout, and scoring failure; preloaded models remain loaded.
- Retry resumes only incomplete stages and reuses valid raw evidence.
- Import is idempotent by artifact identity and never duplicates a run on retry.

**Tests and exit evidence:**

- Unit tests interrupt during loading, capture, scoring, and import.
- Each failure leaves truthful status and deterministic next action.
- A controlled live interruption returns the runtime to its prior model state.
- Resume completes without duplicate database or ledger rows.

**Non-goals:** parallel model execution; distributed queues; background cloud
workers.

## R4: Responsive And Accessible Workflow Closure

**Expected paths:**

- `apps/model-dashboard/model_dashboard/layout.py`
- `apps/model-dashboard/model_dashboard/components.py`
- `apps/model-dashboard/model_dashboard/pages/inventory.py`
- `apps/model-dashboard/model_dashboard/pages/runs.py`
- `apps/model-dashboard/model_dashboard/pages/review.py`
- `apps/model-dashboard/model_dashboard/pages/radar.py`
- page rendering tests

**Contract:**

- Each row keeps model/artifact identity, authority state, and next action visible
  at narrow widths.
- Secondary metadata moves into native disclosure or a contained data region.
- The page itself does not gain accidental horizontal overflow.
- Long identifiers do not overlap actions or adjacent content.
- Skip link, focus visibility, logical tab order, touch targets, labels, and
  destructive-action acknowledgement remain intact.
- Charts show units, authority, exclusion counts, and decision meaning.

**Tests and exit evidence:**

- Rendering tests assert summary/detail semantics and stable action labels.
- Complete `reports/readiness/2026-07-18/human-verification-checklist.md` at all
  three required viewports.
- Every failure has a severity, owner, sanitized screenshot, and exit test.

**Non-goals:** a framework rewrite; a new frontend application; decorative
redesign that does not improve workflow closure.

## R5: Publish One Confirmed Decision Case Study

**Expected paths:**

- `docs/case-studies/`
- sanitized `reports/` output
- README link after review

**Contract:**

- Follow one candidate from inventory through capture, run configuration,
  scoring, independent review, human confirmation, comparison, and a keep,
  watch, retest, or remove decision.
- Explain exclusions and uncertainty, not only the winning score.
- Include measured Apple Silicon throughput and peak RAM.
- Exclude raw prompts, raw responses, private paths, tokens, and credentials.

**Tests and exit evidence:**

- Automated privacy scan passes.
- A second person can identify the conclusion, authority, exclusions, and next
  action without developer guidance.
- The case links only to sanitized or repository-safe evidence.

**Non-goals:** marketing claims beyond the tested workload; publishing the local
database; presenting draft evidence as confirmed.

## R6: Add Retrieval Evaluation

**Prerequisite:** a focused ADR defining dataset, metrics, artifact schema, and
privacy boundary.

**Expected paths:**

- new `evals/local-retrieval-benchmark/`
- role-specific report/import adapter
- inventory and model detail integration
- focused tests and documentation

**Contract:**

- Evaluate embedding models with a local, versioned corpus and queries.
- Report Recall@k plus MRR or nDCG, embedding latency, index time, index size,
  peak memory, dimensions, and language/document coverage.
- Evaluate rerankers only against a fixed retrieved candidate set.
- Keep retrieval results out of LLM score labels and the generative efficiency
  frontier.
- Preserve dataset, parser, chunker, embedding model, and Qdrant collection
  versions in every artifact.

**Tests and exit evidence:**

- Deterministic fixture corpus proves metric calculations.
- Nomic and BGE candidates can be compared in their proper lane.
- The dashboard explains which retrieval model to use, for what corpus, and at
  what local resource cost.

**Non-goals:** graph RAG; agentic retrieval; remote benchmark datasets; hidden
cloud embedding calls.

## Validation Per Packet

Run the narrow tests while developing, then before handoff run:

```text
uv sync
docker compose config
uv run ruff check .
uv run pytest -q
python3 -m unittest discover -s apps/model-dashboard/tests
python3 -m unittest discover -s evals/local-llm-benchmark/tests
python3 scripts/model_dashboard_smoke.py --probe-server
```

Live runtime checks are evidence only when the named local service and model
actually ran. Record unavailable services as environmental limitations rather
than passes.

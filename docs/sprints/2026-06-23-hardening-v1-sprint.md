# AI Lab OS — Hardening & v1.0.0 Sprint (2026-06-23)

The 4 parallel tracks (RAG, bench-breadth, UI/UX, onboarding) are merged into
`main` and green (214 tests). This sprint closes the **security audit findings**,
runs the lab **for real** to validate end-to-end, and ships **v1.0.0**.

After the multi-branch merge complexity last round, this sprint is **tighter**:
one hardening agent + two user-gated validation milestones + a release step.
Source of truth for findings: [reports/security/2026-06-23-audit.md](../../reports/security/2026-06-23-audit.md).

## Validation gate (every loop)

```bash
python3 -m unittest discover -s apps/model-dashboard/tests
python3 -m unittest discover -s evals/local-llm-benchmark/tests
python3 scripts/model_dashboard_smoke.py
uv run pytest -q
uv run ruff check .
```

Constraints unchanged (AGENTS.md): stdlib-only dashboard, no new default deps
beyond the pinned upgrades below, no external/network calls from the dashboard,
default `/ask` privacy-narrow, model execution only behind the approval gate, no
architecture change without an ADR.

---

## Track A — Security hardening (Codex agent: `codex/hardening`)

### H1 — SEC-001: stop duplicating raw model output into capture logs (Medium, privacy)

The new `run_llama_cpp` / `run_mlx_lm` / `run_lmstudio_cli` runners write raw model
stdout/stderr into `*-capture.log` files **in addition to** `raw_responses.jsonl`.
Prompts/responses can contain private local data → conflicts with the "logs don't
dump prompts/responses by default" invariant. (The Ollama runner is already
metadata-only — match it.)

- Files: `evals/local-llm-benchmark/harness.py` (the three capture-log writers),
  `evals/local-llm-benchmark/tests/test_harness.py`, benchmark README/spec.
- Make the `.log` files **metadata-only by default** (prompt id, return code,
  latency, token counts, stop reason, sanitized/truncated error). Keep
  `raw_responses.jsonl` as the **explicit** raw artifact. If full raw stdout/stderr
  is ever needed, gate it behind an explicit, clearly-named flag (off by default).
- Tests: assert capture logs contain no raw response text by default; assert
  `raw_responses.jsonl` still has the raw output.
- ADR only if the artifact contract changes materially (the audit says likely not).

### H2 — SEC-002/003/004: dependency hygiene + doc fix

- Bump `starlette >= 1.3.1` (CVE-2026-54282/54283), `pydantic-settings >= 2.14.2`
  (GHSA-4xgf-cpjx-pc3j), and evaluate `pytest >= 9.0.3` (CVE-2025-71176, dev-only —
  if incompatible, document as accepted dev risk). Update `pyproject.toml` +
  regenerate `uv.lock`; full gate green.
- Doc fix: `evals/local-llm-benchmark/README.md` still mentions private-LAN
  endpoints, but the validator (`harness.py:201-218`) is loopback-only. Correct it.

### H3 — (optional) complete the Codex Deep Security Scan

The official deep scan was **blocked** (needs `agents.max_depth >= 2` in Codex
config; default is 1). If you approve that config change, run the deep scan and
remediate any new findings on this branch.

**Track A DoD.** Audit findings SEC-001–004 fixed or documented-accepted; bench
capture logs metadata-only by default; deps upgraded; gate green.

---

## Track B — Validate for real (user-gated milestones)

These need **your approval** (model execution / real data) — not autonomous loops.

### V1 — Run one real approved benchmark

```bash
uv run ai-lab bench execute --candidate <id> --model-id gpt-oss:20b \
  --runner ollama --run-id <date>-gptoss-r1 --i-approve-local-run --import-dashboard
```
Populates the perf charts (Throughput/RAM/TTFT) with **live data**, validates the
5-runtime engine end-to-end, and gives the portfolio real numbers.

### V2 — Run the RAG retrieval eval with real embeddings

Ingest a small real corpus, set `LOCAL_AI_LAB_EMBEDDING_PROVIDER=ollama` +
`bge-m3` (`ollama pull bge-m3`), and run the `evals/rag-retrieval/` scorer to get
**real recall@k / MRR** — and confirm reranker/hybrid actually help vs. baseline.

---

## Track C — Release v1.0.0 (after A + B)

### R1 — Finalize and tag (Codex `docs` + user-approved tag)

- Update `CHANGELOG.md` + the v1.0.0 release notes with **real validation
  evidence** (the green gate + the V1/V2 real numbers). Truthful only.
- Confirm CI green on `main`.
- Create the annotated `v1.0.0` tag and push it — **only with your explicit
  approval** (the onboarding goal correctly held this).

**Release DoD.** v1.0.0 reflects the hardened, validated state; tag pushed with
evidence.

---

## Sequence

1. **H1** (privacy — blocks a clean v1) → **H2** (deps + doc).
2. **V1 / V2** (your real runs — fills charts + RAG numbers).
3. **R1** — tag v1.0.0 with real evidence.
4. **H3** optional (deep scan) any time.

Recommendation: run **one** `codex/hardening` agent for Track A (don't re-fan into
5 parallel branches — last merge showed the cost). Keep the integrator `/loop` on
`main` verifying each commit.

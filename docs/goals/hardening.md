# Goal — Security hardening (Track A)

- **Branch:** `codex/hardening`
- **Area:** `evals/local-llm-benchmark/`, `pyproject.toml` + `uv.lock`, benchmark docs
- **Reserved ADR:** 0010 (only if the artifact contract changes materially)

```text
GOAL: Close the 2026-06-23 security audit findings in the local-ai-lab repo, on a
single branch codex/hardening. Read AGENTS.md and
reports/security/2026-06-23-audit.md (the findings) and
docs/sprints/2026-06-23-hardening-v1-sprint.md (Track A) first.

HARD CONSTRAINTS: stdlib-only dashboard; no external/network calls from the
dashboard; default /ask stays privacy-narrow; model execution only via the
approval gate; the only sanctioned external call is the quant advisor --lookup-hf.
Preserve passing tests. No architecture change without an ADR.

LOOPS (one cohesive commit each; run the FULL gate before every commit):

H1 — SEC-001 (Medium, privacy): The llama.cpp, MLX-LM, and LM Studio CLI runners
   write raw model stdout/stderr into *-capture.log files in addition to
   raw_responses.jsonl. Make those .log files METADATA-ONLY by default (prompt id,
   return code, latency, token counts, stop reason, sanitized/truncated error) —
   match the Ollama runner, which is already metadata-only. Keep raw_responses.jsonl
   as the explicit raw artifact. If full raw stdout/stderr is ever needed, gate it
   behind an explicit off-by-default flag. Files: evals/local-llm-benchmark/harness.py
   (run_llama_cpp ~1251-1271, run_mlx_lm ~1346-1366, run_lmstudio_cli ~1436-1453) +
   tests. Add tests asserting capture logs contain NO raw response text by default
   and raw_responses.jsonl still does. ADR 0010 only if the artifact contract
   changes materially.

H2 — SEC-002/003/004 (deps) + doc: In pyproject.toml bump starlette>=1.3.1,
   pydantic-settings>=2.14.2, and evaluate pytest>=9.0.3 (dev-only; if it breaks
   tests, document as accepted dev risk and leave pinned). Regenerate uv.lock
   (uv lock). Run the full gate green. Also fix evals/local-llm-benchmark/README.md
   wording that still allows private-LAN endpoints — the validator (harness.py
   ~201-218) is loopback-only.

H3 — (optional, only if the user approves a Codex config change agents.max_depth=2)
   complete the official deep-security-scan and remediate any new findings here.

VALIDATION GATE (every loop):
   python3 -m unittest discover -s apps/model-dashboard/tests
   python3 -m unittest discover -s evals/local-llm-benchmark/tests
   python3 scripts/model_dashboard_smoke.py
   uv run pytest -q
   uv run ruff check .

Commit scope: security / bench / docs. After each loop, STOP and report (files,
tests, gate lines, residual findings). Never claim a command passed unless run.
Begin with H1.
```

# AI Lab Radar

Local-first workflow scaffold for tracking interesting local and open-weight AI
models as review candidates.

## Purpose

AI Lab Radar turns manually approved model discovery notes into candidate records
for later evaluation. It does not download models, run models, call cloud APIs,
or require secrets.

## Radar Lanes

### Local Radar

Local Radar uses only repo-local, user-approved source packets and prior local
benchmark artifacts. This is the default lane for creating durable candidate
records.

### External Radar

External Radar is an on-demand metadata scan over curated public sources such as
official model cards, Hugging Face pages, GitHub release/readme pages, and
official project docs. External Radar may collect source links and public claims,
but it must write an unapproved source packet first. External candidates do not
enter `data/model_registry/candidates.csv` until the user explicitly approves
them.

External Radar still must not download models, run models, call model APIs, add
API clients, use secrets, or create install instructions.

## Inputs

Use only user-approved local inputs, such as:

- User-provided release notes, model cards, benchmark notes, or links.
- Local research notes copied into a thread or report.
- Prior AI Lab OS benchmark reports and dashboard decisions.

For Local Radar, do not add crawler code, automatic web fetching, package
downloads, model downloads, or API clients to this automation.

For External Radar, perform public metadata discovery manually/on demand and
write a source packet with `Approved for radar review: no` and `Safe to commit:
no` until the user approves it.

## Outputs

Radar work should produce:

- Candidate summaries using `candidate-schema.md`.
- Optional report notes using `templates/radar-report.md`.
- Plain-language project explainers that state what a project does, who uses it,
  and what the local demo would look like.
- Project action cards with a one-week deliverable and explicit stop conditions.
- Dated cost ranges adjusted for the local lab profile when one is present.
- Candidate registry records under `data/model_registry` when a candidate is
  ready to track.
- Follow-up task recommendations for local benchmark or dashboard work.

No-op runs should not create tracked reports. If an automation finds no new
approved packet, leave a console/status message or ignored runtime note instead
of writing `*no-new-approved-source-packet.md` into the tracked report set.

## Workflow

1. Collect source notes and record where they came from.
2. Normalize each candidate using `candidate-schema.md`.
3. Record the candidate security gate: provenance, license review state,
   download approval, artifact/file-format risk, and local runtime isolation.
4. Mark the candidate as `watchlist`, `ready_for_eval`, `skip`, or
   `needs_more_info`.
5. Recommend the next local action without downloading or running the model.
6. If a model is ready for evaluation, point it at
   `evals/local-llm-benchmark/SPEC.md` and `skills/local-llm-eval`.

For External Radar, insert an approval gate between steps 1 and 2. The first
packet/report is candidate-only and must not edit `data/model_registry`.

## Local Lab Profile

Copy `lab-profile.example.json` to the ignored
`lab-profile.local.json` file and record available hardware, preferred budget
tiers, maximum DIY hours, and priority categories. The automation reads the
local profile before estimating project cost so already-owned equipment is not
priced repeatedly. Unknown preferences stay `null`; do not invent them.

The local profile may contain private inventory details and machine-specific
notes. It is ignored by git and must not be quoted into tracked packets or
reports. Reports may state only the planning effect, such as "existing host
available" or "budget limit not confirmed."

## Daily And Weekly Outputs

Daily External Radar is a delta digest. A previously reported item returns only
after a material price, release, license, maintenance, or risk change. Each
reported item records `first_seen`, `last_seen`, `change_status`, and a concise
`change_summary`.

On Sunday, the automation also writes a concise weekly rollup using
`templates/weekly-rollup.md` when the preceding seven days contain useful radar
reports. The rollup names the best project, best model candidate, cheapest
useful build, and strongest portfolio opportunity without creating a composite
score or registry decision.

## Project Explainers

Every reported project opportunity includes a concise non-technical explainer.
It must answer what the project is, the problem it solves, who it is for, common
uses, how it works in practice, what the AI Lab version would demonstrate, and
important limitations. Expand unavoidable acronyms on first use and avoid
assuming software, AI, radio, or robotics expertise.

## Security Due Diligence

Radar recommendations must separate interest from approval. A candidate can be
interesting and still have `download_approval=not_approved`.

Before a model is approved for download, update, or execution, record:

- source provenance and whether the publisher/artifact source is explicit;
- license posture, without inferring compatibility from popularity;
- file format and runtime path, with GGUF, MLX, Safetensors, LM Studio, Ollama,
  and llama.cpp preferred over custom code paths;
- checksum/hash, release, or artifact evidence when available;
- whether any model-card code, custom loader, script, notebook, or repo code
  would need to run; and
- isolation guidance for the local benchmark run.

Do not run untrusted code, notebooks, install scripts, or custom loaders as part
of radar review. If a candidate requires that path, mark it `blocked` or
`needs_review` until the user explicitly approves a separate security task.

## Validation

For documentation-only radar updates, inspect the diff and confirm no runtime
dependencies, network calls, secrets, or download logic were added.

Validate a generated report and its referenced source packet with:

```bash
python3 scripts/radar_report_check.py \
  automations/ai-lab-radar/reports/YYYY-MM-DD-daily-external-radar.md
```

If radar output feeds dashboard CSV import, run:

```bash
python3 scripts/model_dashboard_smoke.py
```

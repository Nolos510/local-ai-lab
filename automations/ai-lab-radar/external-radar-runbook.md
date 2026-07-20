# External Radar Runbook

External Radar is an on-demand public metadata scan for finding local-testable
model candidates before they enter the approved local registry.

## Daily External Radar

The daily automation may use External Radar when no new Local Radar source
packet exists. This mode is a curated public metadata digest, not a crawler,
installer, benchmark, or registry writer.

Daily scan categories:

- AI Lab OS product loop: local LLM runtimes, RAG, evals, MCP, agents, workflow
  automation, dashboards, and local-first developer tooling.
- Business and portfolio: tools that could become resume projects, client
  automations, internal ops workflows, or product features.
- OSINT/SIGINT-adjacent learning: passive, legal, educational tools only; do
  not recommend offensive exploitation workflows.
- Edge hardware: Raspberry Pi, edge AI, SDR/radio learning, sensors, and local
  field systems.
- Drone and robotics: PX4, ArduPilot, ROS2, UAV tooling, simulation,
  telemetry, mapping, and computer vision.
- Model radar: local-testable GGUF, MLX, Ollama, LM Studio, and llama.cpp
  candidates. Keep model candidates separate from project opportunities.

Keep daily source sets capped and auditable. Review roughly 20-40 public
metadata items and report only the 5-10 highest-signal items. If network access
or source lookup fails, report `external scan blocked` with the concrete
blocker instead of inventing findings.

Daily output remains unapproved by default:

```text
Approved for radar review: no
Safe to commit: no
```

Do not edit `data/model_registry/candidates.csv` or
`data/project_registry/github_repos.csv` from the daily scan. Registry updates
require a later explicit user approval step.

Before estimating projects, read the ignored
`automations/ai-lab-radar/lab-profile.local.json` when it exists. Fall back to
`lab-profile.example.json` only for schema/default category guidance. Never copy
private inventory details or machine-specific notes into a tracked packet or
report.

## Boundary

- Use curated public metadata sources only: official model cards, Hugging Face
  pages, GitHub release/readme pages, and official project docs.
- Record metadata only: model name, provider, family, parameter count, runtime
  hints, explicit license, explicit context length, source URL, source date,
  why interesting, and risks.
- Do not download models, run models, call model APIs, add API clients, use API
  keys, use secrets, write crawler code, or create install instructions.
- Do not edit `data/model_registry/candidates.csv` until the user approves the
  specific candidates.
- Do not convert source claims into dashboard scores or decisions.
- Do not treat popularity, stars, likes, downloads, or benchmark claims as a
  security review.
- Do not run model-card code, custom Python loaders, install scripts, notebooks,
  or repository code while preparing a recommendation.
- Do not treat a daily scan as approval to clone, install, download, benchmark,
  score, or run anything.

## Priority Rubric

Assign `priority_score` from 1-5 for project opportunities and keep the
rationale explicit:

- `5`: strong AI Lab OS/product loop fit, clear local/self-hosted path, high
  learning or business value, and reviewable risk posture.
- `4`: strong learning/business value or local fit, but with unresolved license,
  operational, telemetry, or dependency questions.
- `3`: interesting future lane, useful reference, or niche personal-interest
  project that needs scoping before action.
- `2`: watchlist/reference item with stale maintenance, unclear fit, or high
  review burden.
- `1`: skip unless a later user goal makes it relevant.

Capture `priority_rationale`, `why_interesting`, `business_tie_in`,
`learning_value`, `local_fit`, `security_risk`, and `recommended_next_step`.
Stars, downloads, likes, and trending position are adoption/context signals
only; they are not quality, trust, license, or security approvals.

## Plain-Language Project Explainers

Every reported `project_opportunity` must include a concise explainer for a
non-technical reader:

- `plain_language_summary`: one or two sentences describing what the project is
  without marketing language or unexplained acronyms;
- `problem_it_solves`: the practical problem or frustration it addresses;
- `who_it_is_for`: the people, teams, or situations that benefit from it;
- `common_use_cases`: two to four concrete examples;
- `how_it_works_in_practice`: a short, command-free description of the normal
  input, processing, and output flow;
- `ai_lab_use_case`: the specific safe local demo or learning artifact AI Lab OS
  would build; and
- `limitations`: what the project does not do, where it becomes complex, or why
  the proposed demo is narrower than the upstream project.

Use everyday language, expand unavoidable acronyms on first use, and distinguish
the upstream project from the smaller AI Lab prototype. Do not turn an explainer
into install instructions or imply that the project has been approved to run.

## Project Cost Estimates

For each reported `project_opportunity`, define the smallest credible, safe,
local-first MVP consistent with its `why_interesting` and then include a dated
cost estimate. Use ranges, not a single total, and keep these scenarios
separate:

- `cost_scope`: the concrete MVP being priced, including whether it is a
  metadata/design prototype, software-only local demo, passive hardware demo,
  or connected hardware build;
- `incremental_cost`: cash needed when the user already owns the required host
  hardware or infrastructure;
- `from_scratch_cost`: minimum credible cost for a functional prototype;
- `portfolio_build_cost`: optional, for a presentable enclosure, mounting,
  storage, or other project-specific finish work; and
- `recurring_monthly_cost`: ongoing power, hosting, subscription, or data costs
  when they are material and publicly knowable.

Record `cost_currency`, `cost_as_of`, `cost_assumptions`, `cost_exclusions`,
`diy_effort_hours`, `cost_confidence`, `cost_source_urls`,
`source_last_checked`, `price_valid_until`, and `refresh_reason`. Hardware price
observations expire after 30 days. A report may use an earlier expiration when a
sale, limited stock, currency conversion, or uncertain compatibility makes the
price less durable. Software with no purchase price should show a `$0` software
or existing-lab cash baseline plus a DIY effort range; it must not be presented
as costless work. Prefer official product pages, official pricing, and approved
resellers. Treat retailer prices as observations that can change, not quotes or
purchasing recommendations. Do not enter a cart, sign in, submit personal data,
or perform a purchase action.

If a useful estimate would require guessing an implementation scope, private
pricing, credentials, regional tax, or unavailable component prices, write
`unknown` for the unresolved line item and name the missing inputs. Do not leave
every cost field `unknown` solely because the source did not define an MVP;
scope the smallest safe prototype first. Cost metadata is not approval to buy,
clone, install, download, run, or register anything. Do not rank a project more
highly only because it is inexpensive.

## Delta Tracking

Daily reports are delta digests, not cumulative catalogs. De-dupe against model
and project registries, prior packets, and prior reports. Every reported item
must include:

- `first_seen`: first radar date for the same model artifact or project;
- `last_seen`: date of the current material observation;
- `change_status`: `new` or `material_change`; and
- `change_summary`: concise evidence of what appeared or changed.

A previously reported item may reappear only after a material price, release,
license, maintenance, or risk change. New commentary, popularity counts, or an
unchanged source access date are not material changes. The weekly rollup may
reference unchanged finalists, but it must identify the original daily report.

## MVP Action Cards

Every reported `project_opportunity` must include a planning-only action card:

- `one_week_deliverable`: reviewable output achievable within seven days;
- `success_criteria`: observable completion criteria without invented metrics;
- `demo_artifact`: sanitized local artifact expected at the end;
- `prerequisites`: approvals, inventory confirmations, or source evidence;
- `first_three_tasks`: exactly three ordered, concrete tasks;
- `blockers`: known impediments or missing inputs;
- `stop_conditions`: conditions that end or rescope the project; and
- `safety_notes`: project-specific privacy, legal, execution, or physical-risk
  boundaries.

An action card does not approve cloning, installation, execution, credentials,
hardware purchases, live radio transmission, or flight/control operations.

## Effort Versus Value

Group project recommendations where applicable into:

- weekend projects;
- sub-$300 builds; and
- larger portfolio investments.

Show cash range, DIY hours, learning value, business value, and risk as separate
dimensions. Do not calculate a composite opportunity, ROI, or value score. Use
the local profile's budget and time preferences when confirmed; otherwise mark
the relevant constraint as unconfirmed.

## Model Practicality

Every external `model_candidate` must record:

- `estimated_artifact_size`;
- `estimated_disk_requirement`;
- `expected_memory_range`;
- `compatible_local_runtimes`; and
- `benchmark_gap`.

Use source-declared values where available, label conservative inferences, and
write `unknown` when an exact artifact/quantization/runtime has not been chosen.
The benchmark gap must name the specific missing review or benchmark lane that
prevents evaluation. These fields are planning metadata, not local benchmark
evidence.

## Weekly Rollup

On Sunday, use `templates/weekly-rollup.md` to summarize useful daily reports
from the preceding seven days. The shortlist must name the best project, best
model candidate, cheapest useful build, and strongest portfolio opportunity.
Keep the dimensions independent and carry forward approval/safety boundaries.
If the week has no useful daily deltas, do not create a tracked no-op rollup.

## Workflow

1. Search the curated sources manually and keep the scan scope small enough to
   audit.
2. Write an unapproved packet under `automations/ai-lab-radar/inputs/` with:

   ```text
   Approved for radar review: no
   Safe to commit: no
   ```

3. Use `automations/ai-lab-radar/candidate-schema.md` to write a reviewer report
   under `automations/ai-lab-radar/reports/`.
4. Record delta/freshness fields and exclude unchanged prior items from the
   daily digest.
5. Assign each candidate one disposition: `ready_for_eval`, `watchlist`, `skip`,
   or `needs_more_info`.
6. Add a plain-language explainer, sourced project cost ranges, and MVP action
   cards. Keep cash, effort, learning value, business value, and risk separate.
7. Add model practicality fields and the exact benchmark gap.
8. Assign each candidate conservative security fields:
   `security_review_status=needs_review`,
   `download_approval=not_approved`, license review state, provenance state,
   security notes, and isolation notes.
9. Leave `data/model_registry` and `data/project_registry` unchanged until
   approval.
10. Validate the report with `python3 scripts/radar_report_check.py <report>`.
11. After approval, normalize only approved candidates into the appropriate
   registry.

## Security Screening Checklist

For each candidate, capture what is known and what remains unknown:

- Publisher/source: official page, mirror, quantizer, or user-local artifact.
- Artifact format: GGUF, MLX, Safetensors, Ollama, LM Studio, or custom.
- License: explicit license and any unresolved use restrictions.
- Runtime path: local runtime that loads weights without executing upstream code.
- Hash/release evidence: checksum, release metadata, or model-card file listing
  when available.
- Red flags: custom code requirement, pickled weights, install scripts,
  notebooks, unclear publisher chain, missing license, or mismatched local
  inventory name.

## Validation

Run these checks before handing the packet back to the user:

```bash
python3 scripts/radar_report_check.py \
  automations/ai-lab-radar/reports/YYYY-MM-DD-daily-external-radar.md
git diff -- automations/ai-lab-radar data/model_registry data/project_registry
rg -n "download|snapshot_download|from_pretrained|api_key|token|openai|anthropic|huggingface_hub|requests|httpx" automations/ai-lab-radar data/model_registry data/project_registry
```

Review any search hits. Guardrail text is expected; runtime code, dependency
adds, secrets, or download logic are not.

Run `python3 scripts/model_dashboard_smoke.py` only when dashboard-related
files, dashboard imports, or registry import paths changed.

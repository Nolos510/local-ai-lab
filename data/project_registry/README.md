# Project Registry

Local registry area for non-model AI projects, GitHub repositories, business
ideas, and product integrations that may feed the AI Lab OS roadmap.

## Intended Flow

```text
external radar scan
  -> project source packet
  -> project registry records
  -> lab dashboard project lane
  -> prototype / integration task
```

Project records are not model candidates and must not create eval scores,
benchmark labels, or dashboard decisions. They are product opportunities:
things to inspect, prototype, self-host, integrate, or learn from.

## Boundary

- Record public metadata and local fit only.
- Do not clone, install, run, download packages, or create API keys from project
  radar.
- Do not treat GitHub stars as quality scores. Stars are adoption/context
  signals that need technical review.
- Prefer projects with a clear local or self-hosted path when they affect the
  AI Lab OS product loop.

## Daily Radar Categories

The daily external radar may surface project opportunities from these lanes:

- AI Lab OS product loop: local runtimes, RAG, evals, MCP, agents, workflow
  automation, dashboards, and developer tooling.
- Business and portfolio: client automation, internal ops, resume-grade
  prototypes, and product features.
- OSINT/SIGINT-adjacent learning: passive, legal, educational tooling only.
- Edge hardware: Raspberry Pi, edge AI, SDR/radio learning, sensors, and local
  field systems.
- Drone and robotics: PX4, ArduPilot, ROS2, UAV tooling, telemetry, mapping,
  simulation, and computer vision.

Model candidates belong in `data/model_registry`, not this registry. If a
source includes both a project and a model, split the records and keep model
benchmark/scoring decisions out of the project lane.

## Priority Rubric

Use `priority_score` from 1-5:

- `5`: strong AI Lab OS/product loop fit, clear local/self-hosted path, high
  learning or business value, and manageable review risk.
- `4`: strong value but unresolved license, telemetry, dependency, or
  operational questions.
- `3`: useful reference or future lane with unclear immediate action.
- `2`: watchlist item with stale maintenance, weak fit, or high review burden.
- `1`: skip unless a future user goal makes it relevant.

Each row should explain `priority_rationale`, `why_interesting`,
`business_tie_in`, `learning_value`, `local_fit`, `risk_notes`, and
`recommended_next_step` when those fields are available. A high priority score
is not permission to install, clone, run, or add a dependency.

## Plain-Language Explainers

Every reported project should be understandable without prior software, AI,
radio, or robotics knowledge. Include:

- `plain_language_summary`
- `problem_it_solves`
- `who_it_is_for`
- `common_use_cases`
- `how_it_works_in_practice`
- `ai_lab_use_case`
- `limitations`

Keep each answer concise, expand unavoidable acronyms, and distinguish what the
upstream project can do from the smaller local demo the lab is considering.
These descriptions remain planning metadata and do not approve execution.

## Cost Metadata

Daily radar packets and reports should include dated, sourced cost ranges for a
project when public metadata supports a credible estimate. Separate the cost of
using already-owned equipment from a from-scratch prototype and any optional
portfolio finish work. Record the currency, assumptions, exclusions, confidence,
price source URLs, and a DIY effort range. Define the smallest credible, safe,
local-first MVP being priced. Software-only projects should show their `$0`
software or existing-lab cash baseline without hiding the time required to build
the prototype. Use `unknown` only for unresolved line items, not as a substitute
for scoping a basic project.

Cost is advisory metadata. It does not change `priority_score`, approve a
purchase, or authorize installation or execution. Keep cost details in the
source packet and report for now; do not change `github_repos.csv` solely to add
cost fields without a separately approved registry-schema change.

Price records should include `source_last_checked`, `price_valid_until`, and
`refresh_reason`. Hardware prices expire after 30 days. A stale price is a
refresh trigger, not permission to purchase or a reason to repeat an unchanged
project in a daily digest.

## MVP Action Cards

Every reported project opportunity needs a one-week action card containing:

- `one_week_deliverable`
- `success_criteria`
- `demo_artifact`
- `prerequisites`
- `first_three_tasks`
- `blockers`
- `stop_conditions`
- `safety_notes`

Action cards are planning records. They must keep download, install, execution,
credential, purchase, and registry approval gates explicit.

## Delta And Value Views

Daily packets record `first_seen`, `last_seen`, `change_status`, and
`change_summary`. Previously reported projects return only after a material
price, release, license, maintenance, or risk change.

Reports group projects into weekend projects, sub-$300 builds, and larger
portfolio investments where applicable. Show cash, DIY hours, learning value,
business value, and risk independently; do not collapse them into a composite
value score.

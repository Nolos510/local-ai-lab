# AI Lab Radar Source Packet

Packet title:
Packet date:
Prepared by:
Approved for radar review: no
Safe to commit: no

## Scope

Briefly state what this packet covers and where the notes came from. Use only
local user-approved material. Do not fetch links or add new source claims during
radar review.

## Source References

| Source ID | Source type | Source date | Link or local reference | Notes |
| --- | --- | --- | --- | --- |
| A | model card / release note / benchmark snippet / user note | unknown |  |  |

## Copied Notes Or Excerpts

### Source A

Paste or summarize approved source material here. Keep source claims separate
from evaluator conclusions.

```text
Copied excerpt or user-approved note.
```

## Model Candidate Notes

Repeat this section for each model candidate named in the packet. For Daily
External Radar, use the exact heading shape below so the validator can parse it.

### model_candidate: Exact model name

| Field | Value |
| --- | --- |
| `candidate_id` |  |
| `model_name` |  |
| `model_family` | unknown |
| `provider_or_org` | unknown |
| `format_or_runtime` | unknown |
| `license` | unknown |
| `source_url` |  |
| `why_interesting` |  |
| `estimated_artifact_size` | unknown |
| `estimated_disk_requirement` | unknown |
| `expected_memory_range` | unknown |
| `compatible_local_runtimes` | unknown |
| `benchmark_gap` |  |
| `risk_notes` |  |
| `security_review_status` | `needs_review` |
| `download_approval` | `not_approved` |
| `provenance_status` | `source_metadata_only` |
| `recommended_next_step` | `needs_more_info` |
| `source_last_checked` | YYYY-MM-DD |
| `first_seen` | YYYY-MM-DD |
| `last_seen` | YYYY-MM-DD |
| `change_status` | `new` or `material_change` |
| `change_summary` |  |

## Project Opportunity Notes

Repeat for every project in an External Radar daily packet.

### project_opportunity: Exact project name

| Field | Value |
| --- | --- |
| `project_id` |  |
| `project_name` |  |
| `source_url` |  |
| `item_type` | `project_opportunity` |
| `priority_score` | 1-5 |
| `priority_rationale` |  |
| `plain_language_summary` |  |
| `problem_it_solves` |  |
| `who_it_is_for` |  |
| `common_use_cases` |  |
| `how_it_works_in_practice` |  |
| `ai_lab_use_case` |  |
| `limitations` |  |
| `why_interesting` |  |
| `business_tie_in` |  |
| `learning_value` |  |
| `local_fit` |  |
| `risk_notes` |  |
| `recommended_next_step` | `watchlist`, `ready_for_review`, `skip`, or `needs_more_info` |
| `cost_currency` | USD |
| `cost_as_of` | YYYY-MM-DD |
| `cost_scope` |  |
| `incremental_cost` |  |
| `from_scratch_cost` |  |
| `portfolio_build_cost` |  |
| `diy_effort_hours` |  |
| `recurring_monthly_cost` |  |
| `cost_confidence` | Low, Medium, or High with rationale |
| `cost_assumptions` |  |
| `cost_exclusions` |  |
| `cost_source_urls` |  |
| `source_last_checked` | YYYY-MM-DD |
| `price_valid_until` | No more than 30 days after source check |
| `refresh_reason` |  |
| `first_seen` | YYYY-MM-DD |
| `last_seen` | YYYY-MM-DD |
| `change_status` | `new` or `material_change` |
| `change_summary` |  |
| `one_week_deliverable` |  |
| `success_criteria` |  |
| `demo_artifact` |  |
| `prerequisites` |  |
| `first_three_tasks` | 1.  2.  3.  |
| `blockers` |  |
| `stop_conditions` |  |
| `safety_notes` |  |

## Reviewer Notes

- Candidate records must follow `automations/ai-lab-radar/candidate-schema.md`.
- `ready_for_eval` candidates should point to
  `evals/local-llm-benchmark/SPEC.md` and `skills/local-llm-eval`.
- Do not create dashboard scores or decisions until a real local benchmark run
  exists.
- Do not add install instructions unless the user separately asks for a local
  install plan.
- Treat GitHub/Hugging Face links as metadata only. Do not run model-card code,
  custom loaders, install scripts, notebooks, or repository code during radar
  review.
- Default new external candidates to `download_approval=not_approved` until a
  specific artifact, license, provenance, checksum/hash evidence, and local
  runtime path are reviewed.
- Run `python3 scripts/radar_report_check.py <report-path>` for generated Daily
  External Radar and weekly rollup reports.

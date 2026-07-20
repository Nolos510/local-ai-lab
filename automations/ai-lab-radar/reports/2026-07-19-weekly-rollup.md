# AI Lab Radar Weekly Rollup

Week ending: 2026-07-19
Source daily reports: `automations/ai-lab-radar/reports/2026-07-18-daily-external-radar.md`; `automations/ai-lab-radar/reports/2026-07-19-daily-external-radar.md`
Approved for radar review: no
Safe to commit: no
Dashboard: [Radar candidates](http://127.0.0.1:8765/radar) after starting the
local dashboard.

## Weekly Shortlist

This first Sunday rollup covers 19 new radar deltas from two public-metadata
reports. It does not repeat the full catalog or create registry decisions,
evaluation scores, purchase approval, or execution approval.

| Selection | Item | Cash | DIY hours | Why it leads |
| --- | --- | --- | --- | --- |
| Best project | agentevals | $0-$25 planning MVP | 10-16h | Strongest direct fit for AI Lab evidence and confirmation workflows. |
| Best model candidate | SmolLM3-3B-GGUF | No purchase estimate; artifact not approved | Benchmark effort unknown | Clearest compact general-model artifact sizes and familiar local-runtime metadata. |
| Cheapest useful build | SigMF capture catalog | $0-$15 metadata MVP | 6-10h | Useful stdlib-first schema/provenance project with synthetic data only. |
| Strongest portfolio opportunity | Raspberry Pi AI Camera + IMX500 Model Zoo | $195-$225 recommended; $250-$350 field-ready | 10-18h | Tangible edge-vision demo with a clear first-week review packet. |

## Best Project

- Project: agentevals
- In plain English: It checks whether a multi-step AI assistant took the expected actions by reading a saved activity timeline instead of running the assistant again.
- Who it helps and what problem it solves: It helps automation teams identify which tool call or intermediate step caused a failure and makes repeatable quality review easier.
- AI Lab demo: Map one sanitized benchmark artifact into a trace-like fixture and define three deterministic checks plus a human-confirmation storyboard.
- Why this week: It is the only new project with priority 5 and directly strengthens the AI Lab evidence loop without requiring hardware or model execution for the first review.
- Cash range: $0-$25 for the planning-only MVP on confirmed lab compute; $0-$75 for polished portfolio documentation.
- DIY hours: 10-16 hours; maximum weekly DIY hours remain unconfirmed.
- Learning value: High for trace schemas, deterministic evaluation, evidence lineage, and failure diagnosis.
- Business value: High for client-facing quality controls around tool-using automations.
- Risk: Trace data can contain prompts, responses, arguments, and private paths; direct adoption would add dependencies and optional cloud surfaces.
- Next approval task: Approve a static, sanitized trace/evaluator mapping only.

## Best Model Candidate

- Candidate: SmolLM3-3B-GGUF
- Why this week: Its source lists explicit 1.92 GB Q4, 3.28 GB Q8, and 6.16 GB F16 artifacts, making practicality easier to review than candidates with unspecified or custom-runtime packaging.
- Artifact/disk/memory practicality: Source-declared 1.92 GB Q4; inferred 4-8 GB disk and roughly 4-8 GB memory at moderate context, pending exact artifact selection.
- Compatible local runtimes: Source metadata mentions llama.cpp, LM Studio, Ollama, ONNX, MLX, and MLC; no exact local model ID is approved.
- Benchmark gap: Exact artifact/hash, license/provenance confirmation, Jinja thinking template, context target, approved local runner, and execution approval.
- Next approval task: Approve an exact-artifact security review, not a download or run.

## Cheapest Useful Build

- Project: SigMF capture catalog
- In plain English: A local catalog that checks and organizes the labels attached to passive signal recordings so important technical and privacy details are not lost.
- Existing-lab cash: $0-$15 for synthetic metadata fixtures and a static catalog mockup.
- From-scratch cash: $0-$25 for the defined metadata-only MVP; an optional receiver expansion is $40-$100 and remains unapproved.
- DIY hours: 6-10 hours.
- Useful deliverable: Minimal schema, six synthetic validation cases, privacy rules, and a searchable catalog storyboard.
- Risk: Metadata may expose location/equipment; stop before live capture, private interception, decoding, or transmission.

## Strongest Portfolio Opportunity

- Project: Raspberry Pi AI Camera + IMX500 Model Zoo
- In plain English: A small camera with its own AI chip that can recognize visual patterns locally and send compact results to a Raspberry Pi.
- Portfolio build range: $195-$225 for the recommended prototype; roughly $250-$350 for a field-ready version after deployment requirements are defined.
- Demo artifact: A local object/event timeline, architecture diagram, license-reviewed model choice, and short walkthrough using a consented scene.
- Business value: Strong for private inspection, inventory, workspace safety, and low-connectivity field prototypes.
- Stop condition: Stop if the exact model license is unsuitable, the project requires biometric identification or covert monitoring, or final cost exceeds the approved budget.

## Delta Summary

| Item | Type | Change | Source last checked | Next refresh |
| --- | --- | --- | --- | --- |
| Raspberry Pi AI Camera + IMX500 Model Zoo | project | New 2026-07-18; contained edge-vision build with sourced price | 2026-07-18 | 2026-08-17 or material price/license change |
| SmolLM3-3B-GGUF | model | New 2026-07-18; explicit compact GGUF sizes | 2026-07-18 | Exact-artifact approval or material source change |
| Dagu | project | New 2026-07-18; local workflow-governance reference | 2026-07-18 | Material release/license/risk change |
| agentevals | project | New 2026-07-19; local-first trace evaluation | 2026-07-19 | 2026-08-18 or material release/trace change |
| Raspberry Pi AI HAT+ 2 | project | New 2026-07-19; official $200 edge generative-AI add-on | 2026-07-19 | 2026-08-18 or stock/inventory change |
| PlotJuggler | project | New 2026-07-19; passive log visualization with July beta | 2026-07-19 | Stable v4 or material telemetry/license change |
| SigMF capture catalog | project | New 2026-07-19; synthetic passive-data catalog | 2026-07-19 | 2026-07-26 for optional receiver pricing |

## Expiring Costs

| Project | Price valid until | Refresh reason |
| --- | --- | --- |
| SigMF optional receiver expansion | 2026-07-26 | Vendor price/stock post is old; refresh before any hardware approval. |
| Raspberry Pi AI Camera + IMX500 Model Zoo | 2026-08-17 | Refresh official/reseller camera, Pi, power, cooling, and storage prices. |
| agentevals | 2026-08-18 | Refresh only for material license, release, trace-format, or local-first change. |
| Raspberry Pi AI HAT+ 2 | 2026-08-18 | Refresh Pi tier, HAT stock, accessory prices, and confirmed inventory. |
| PlotJuggler | 2026-08-18 | Refresh after stable v4, telemetry, license, or selected file-format change. |

## Next Approval Task

- Approval requested: Approve the one-week `agentevals` static trace/evaluator mapping using one sanitized benchmark artifact shape. This is the strongest no-purchase improvement to the AI Lab product loop.
- Explicitly not approved: package or model downloads, installation, execution, cloud/model APIs, credentials, trace export, registry entry, score import, hardware purchase, radio capture/transmission, or flight/control activity.
- Profile confirmation still needed: owned Raspberry Pi/accessories, software-defined radio hardware, drone/controller/Android hardware, maximum DIY hours, and portfolio investment budget.

## Safety Posture

- Metadata-only boundaries: The rollup summarizes two unapproved public-metadata reports and planning artifacts only.
- Registry changes: None; model and project CSV registries remain unchanged.
- Downloads, installs, execution, APIs, and secrets: None. No repository, package, model, or model-card code was downloaded or run; no cloud/model API, key, secret, purchase, live radio, or flight action occurred.

# AI Lab Radar Source Packet

Packet title: Daily External Radar Delta Scan
Packet date: 2026-07-19
Prepared by: Codex automation
Approved for radar review: no
Safe to commit: no

## Scope

Daily External Radar ran because no new user-approved Local Radar packet was
present. This packet records public metadata only. It does not approve registry
entry, downloads, installation, model or repository execution, benchmark
scoring, purchases, radio transmission, flight operations, or dashboard
decisions.

Source access date: 2026-07-19.

The ignored local profile confirms an existing Apple Silicon host. Raspberry Pi,
software-defined radio, drone inventory, maximum DIY hours, and the portfolio
budget remain unconfirmed. No private inventory details are copied here.

## Reviewed Source Set

The scan reviewed 30 public metadata items and de-duplicated them against the
model and project registries and all prior radar packets and reports. Only six
new, high-signal items are normalized below.

| # | Item | Type | Source URL | Scan note |
| --- | --- | --- | --- | --- |
| 1 | Ornith-1.0-9B-GGUF | model_candidate | https://huggingface.co/deepreinforce-ai/Ornith-1.0-9B-GGUF | Shortlisted; compact coding GGUF with explicit sizes, but parser and template review are unresolved. |
| 2 | MiniCPM5-1B-Agentic-Tooluse-GGUF | model_candidate | https://huggingface.co/ewinregirgojr/MiniCPM5-1B-Agentic-Tooluse-GGUF | Shortlisted; very small tool-use candidate with explicit provenance and a declared clean-stop weakness. |
| 3 | gemma-4-12b-it-GGUF | model_candidate | https://huggingface.co/unsloth/gemma-4-12b-it-GGUF | Not shortlisted; multimodal scope overlaps yesterday's vision candidate and the current benchmark is text-first. |
| 4 | tinygemma3-GGUF | model_candidate | https://huggingface.co/ggml-org/tinygemma3-GGUF | Not shortlisted; tiny CIFAR-10 CI fixture is not a useful general assistant candidate. |
| 5 | Ternary-Bonsai-27B-gguf | model_candidate | https://huggingface.co/prism-ml/Ternary-Bonsai-27B-gguf | Not shortlisted; custom low-bit runtime concerns overlap yesterday's Bonsai review. |
| 6 | Qwythos-9B-Claude-Mythos-5-1M-GGUF | model_candidate | https://huggingface.co/empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF | Not shortlisted; derivative provenance and very large context claims need a separate source review. |
| 7 | Qwythos-9B-v2-GGUF | model_candidate | https://huggingface.co/empero-ai/Qwythos-9B-v2-GGUF | Not shortlisted; weaker provenance fit than the two selected model candidates. |
| 8 | ThinkingCap-Qwen3.6-27B-GGUF | model_candidate | https://huggingface.co/bottlecapai/ThinkingCap-Qwen3.6-27B-GGUF | Not shortlisted; larger derivative overlaps the existing Qwen coding lane. |
| 9 | DeepSeek-V4-Flash-GGUF | model_candidate | https://huggingface.co/unsloth/DeepSeek-V4-Flash-GGUF | Not shortlisted; 284B class creates a larger artifact and review burden than today's compact candidates. |
| 10 | gemma-4-26B-A4B-it-GGUF | model_candidate | https://huggingface.co/unsloth/gemma-4-26B-A4B-it-GGUF | Not shortlisted; multimodal and mixture-of-experts scope needs a future benchmark lane. |
| 11 | GLM-5.2-GGUF | model_candidate | https://huggingface.co/unsloth/GLM-5.2-GGUF | Not shortlisted; 754B class is not practical for the next local evaluation task. |
| 12 | MiniCPM5-1B Claude Opus Fable variants | model_candidate | https://huggingface.co/models?library=gguf | Discovery context only; less explicit provenance than the selected MiniCPM artifact. |
| 13 | agentevals | project_opportunity | https://github.com/agentevals-dev/agentevals | Shortlisted; local-first trace evaluation maps directly to AI Lab evidence workflows. |
| 14 | Agent Replay | project_opportunity | https://github.com/agentreplay/agentreplay | Not shortlisted; alpha status, mixed licensing, and broad Rust/TypeScript/Python scope increase review cost. |
| 15 | LangWatch | project_opportunity | https://github.com/langwatch/langwatch | Not shortlisted; gateway, keys, and provider features are broader than the local evidence need. |
| 16 | Arize Phoenix | project_opportunity | https://github.com/Arize-ai/phoenix | Not shortlisted; mature reference but heavier and more provider-oriented than the selected trace-eval concept. |
| 17 | OpenLIT | project_opportunity | https://github.com/openlit/openlit | Not shortlisted; broad providers, vault, telemetry, and fleet-management surface raise scope risk. |
| 18 | traceAI | project_opportunity | https://github.com/future-agi/traceai | Not shortlisted; overlaps the Future AGI item reported yesterday. |
| 19 | Harness Evals | project_opportunity | https://github.com/harness/harness-evals | Not shortlisted; useful reference, but optional cloud graders and dependency extras weaken immediate local fit. |
| 20 | Raspberry Pi AI HAT+ 2 | project_opportunity | https://www.raspberrypi.com/products/ai-hat-plus-2/ | Shortlisted; official current edge generative-AI hardware with a clear local demo path. |
| 21 | Raspberry Pi AI HAT documentation | project_opportunity | https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html | Supporting source for hardware, memory, model-size, cooling, and compatibility limits. |
| 22 | Raspberry Pi AI product archive | project_opportunity | https://www.raspberrypi.com/news/category/raspberry-pi-products/raspberry-pi-ai/ | Discovery context; no separate project delta. |
| 23 | PlotJuggler | project_opportunity | https://github.com/PlotJuggler/PlotJuggler | Shortlisted; current beta and local file visualization fit passive robotics learning. |
| 24 | PX4 pyulog | project_opportunity | https://github.com/PX4/pyulog | Supporting parser reference; not a separate end-user project today. |
| 25 | PX4 Flight Review | project_opportunity | https://github.com/PX4/flight_review | Not shortlisted; local mode exists but the web stack is heavier and older than the PlotJuggler path. |
| 26 | PX4 flight-review-rs | project_opportunity | https://github.com/PX4/flight-review-rs | Supporting future backend reference; not yet the clearest one-week demo. |
| 27 | ArduPilot UAVLogViewer | project_opportunity | https://github.com/ArduPilot/UAVLogViewer | Not shortlisted; Cesium credential assumptions and older release reduce local-first fit. |
| 28 | SigMF | project_opportunity | https://github.com/sigmf/SigMF | Shortlisted; standard metadata can organize passive signal recordings without an offensive workflow. |
| 29 | Ground Station | project_opportunity | https://github.com/sgoudelis/ground-station | Not shortlisted; live satellite scheduling, hardware control, and external metadata sync expand safety scope. |
| 30 | OpenWebRX+ | project_opportunity | https://github.com/0xAF/openwebrxplus | Not shortlisted; receive-only potential is useful, but multi-user exposure and many decoders create a larger hardening task. |

## Supplemental Cost Sources

| Project | Source URL | Public pricing or scope evidence |
| --- | --- | --- |
| agentevals | https://github.com/agentevals-dev/agentevals | Apache-2.0 project with a local-first mode; the defined planning MVP reuses confirmed lab compute. |
| Raspberry Pi AI HAT+ 2 | https://www.raspberrypi.com/products/ai-hat-plus-2/ | Official product page showed $200, Raspberry Pi 5 requirement, 8 GB on-board RAM, and included HAT mounting hardware. |
| Raspberry Pi 5 | https://www.raspberrypi.com/products/raspberry-pi-5/ | Official product page showed Raspberry Pi 5 variants and required power/cooling context. |
| Raspberry Pi 2026 price context | https://www.raspberrypi.com/news/a-new-3gb-raspberry-pi-4-for-83-75-and-more-memory-driven-price-increases/ | Official April 2026 price-change metadata; final reseller stock, tax, and shipping still vary. |
| PlotJuggler | https://github.com/PlotJuggler/PlotJuggler | MPL-2.0 software, macOS arm64 metadata, and a July 2026 beta release; planning MVP reuses confirmed lab compute. |
| SigMF | https://github.com/sigmf/SigMF | CC-BY-SA-4.0 specification and JSON metadata shape; planning MVP needs no paid software. |
| Optional passive receiver | https://www.rtl-sdr.com/rtl-sdr-blog-v4-dongle-initial-release/ | Vendor page lists $29.95 dongle-only and $39.95 with antennas, but its stock note is old and requires refresh before any purchase decision. |

## Highest-Signal Items

### model_candidate: Ornith-1.0-9B-GGUF

| Field | Value |
| --- | --- |
| `candidate_id` | `20260719-ornith-1-0-9b-gguf` |
| `model_name` | Ornith-1.0-9B-GGUF |
| `model_family` | Qwen 3.5-derived Ornith |
| `provider_or_org` | DeepReinforce |
| `params_b` | 9, source-declared |
| `format_or_runtime` | GGUF |
| `claimed_context_window` | Source benchmark recipes use 128K to 256K contexts; practical local target is unverified. |
| `license` | MIT shown by the source page; still needs artifact-level review. |
| `source_url` | https://huggingface.co/deepreinforce-ai/Ornith-1.0-9B-GGUF |
| `public_adoption_signal` | Source page showed about 2.35 million downloads last month and 531 likes; context only, not trust evidence. |
| `why_interesting` | A compact coding-agent model with an ordinary GGUF path and explicit Q4/Q5 sizes could provide a more practical coding comparison than much larger agent models. |
| `local_fit` | Strong size fit for the confirmed 256 GB Apple Silicon host, but local runner and parser compatibility remain unverified. |
| `estimated_artifact_size` | Source-declared: 5.63 GB Q4_K_M or 6.47 GB Q5_K_M. |
| `estimated_disk_requirement` | Inferred: about 8-10 GB for one selected artifact plus local runtime metadata and evidence. |
| `expected_memory_range` | Inferred: roughly 8-16 GB at modest context for Q4/Q5; long-context cache needs could be materially higher. |
| `compatible_local_runtimes` | Source metadata lists llama.cpp, LM Studio, and Ollama for GGUF; exact parser/template behavior is unverified. |
| `benchmark_gap` | Exact file and hash, artifact license/provenance, chat template, reasoning/tool parser, context cap, approved local runner, and a coding-agent comparison lane are missing. |
| `risk_notes` | Source recipes require special reasoning/tool parsing and discuss a modified template; non-GGUF recipes include remote-code execution flags that are outside radar boundaries. |
| `security_review_status` | `needs_review` |
| `download_approval` | `not_approved` |
| `license_review_status` | `needs_review` |
| `provenance_status` | `source_metadata_only` |
| `security_notes` | Review the exact GGUF file, hash, publisher chain, template, and parser without using source install scripts or remote code. |
| `isolation_notes` | If separately approved later, use only a reviewed GGUF path in an existing local runtime and keep raw evidence local. |
| `recommended_next_step` | `needs_more_info` pending exact-artifact security and benchmark-lane review. |
| `proposed_eval` | After separate approval only, compare a fixed Q4/Q5 artifact against the existing coding lane using `evals/local-llm-benchmark/SPEC.md` and `skills/local-llm-eval`. |
| `source_last_checked` | 2026-07-19 |
| `first_seen` | 2026-07-19 |
| `last_seen` | 2026-07-19 |
| `change_status` | `new` |
| `change_summary` | First radar appearance of this exact 9B GGUF coding candidate. |

### model_candidate: MiniCPM5-1B-Agentic-Tooluse-GGUF

| Field | Value |
| --- | --- |
| `candidate_id` | `20260719-minicpm5-1b-agentic-tooluse-gguf` |
| `model_name` | MiniCPM5-1B-Agentic-Tooluse-GGUF |
| `model_family` | MiniCPM5 |
| `provider_or_org` | Community fine-tune by ewinregirgojr from OpenBMB base metadata |
| `params_b` | 1, source-declared |
| `format_or_runtime` | GGUF |
| `claimed_context_window` | unknown |
| `license` | Source page reports `other`; exact base, adapter, and merged-artifact terms need review. |
| `source_url` | https://huggingface.co/ewinregirgojr/MiniCPM5-1B-Agentic-Tooluse-GGUF |
| `public_adoption_signal` | Source page showed 12,750 downloads last month and 61 likes; context only. |
| `why_interesting` | The 688 MB Q4 artifact is small enough for a cheap tool-call parser experiment and the source documents exact conversion revisions and known stopping limitations. |
| `local_fit` | Excellent size fit, but tool-call correctness needs a dedicated local fixture rather than the current general text benchmark alone. |
| `estimated_artifact_size` | Source-declared: 688 MB Q4_K_M, 1.15 GB Q8_0, or 2.17 GB F16. |
| `estimated_disk_requirement` | Inferred: about 2-4 GB for one selected artifact, tokenizer/template evidence, and benchmark output. |
| `expected_memory_range` | Inferred: about 2-6 GB depending on quantization, context, and runtime overhead. |
| `compatible_local_runtimes` | Source metadata lists llama.cpp, LM Studio, and Ollama; exact XML tool-call parser support is unverified. |
| `benchmark_gap` | Exact artifact/hash and license approval, matching chat template, bounded stopping behavior, and a deterministic tool-selection/argument fixture are missing. |
| `risk_notes` | The source says clean stopping remained weak and source-model evaluation was not repeated independently for every quantization. Parser-side validation is essential. |
| `security_review_status` | `needs_review` |
| `download_approval` | `not_approved` |
| `license_review_status` | `needs_review` |
| `provenance_status` | `source_metadata_only` |
| `security_notes` | Treat source benchmark tables as claims. Review the base, adapter, merged checkpoint, conversion revisions, license chain, and exact file hash. |
| `isolation_notes` | If approved later, expose only fake local tools with no filesystem, network, secret, or shell authority during parser evaluation. |
| `recommended_next_step` | `needs_more_info` pending license-chain and deterministic tool-call fixture review. |
| `proposed_eval` | After approval only, add a non-executing tool-selection fixture alongside `evals/local-llm-benchmark/SPEC.md`; do not give the model real tools. |
| `source_last_checked` | 2026-07-19 |
| `first_seen` | 2026-07-19 |
| `last_seen` | 2026-07-19 |
| `change_status` | `new` |
| `change_summary` | First radar appearance of this exact compact tool-use GGUF. |

### project_opportunity: agentevals

| Field | Value |
| --- | --- |
| `project_id` | `20260719-agentevals-trace-review` |
| `project_name` | agentevals |
| `source_url` | https://github.com/agentevals-dev/agentevals |
| `item_type` | `project_opportunity` |
| `priority_score` | 5 |
| `priority_rationale` | Directly supports AI Lab's evidence and confirmation loop, runs locally according to source metadata, and can first be evaluated using static traces without model execution. |
| `plain_language_summary` | agentevals checks whether a multi-step AI assistant followed the expected sequence of actions. It works from a saved activity record instead of asking the assistant to repeat the task. |
| `problem_it_solves` | Teams often know an AI assistant produced a bad outcome but cannot see which tool call or intermediate step caused it. Re-running the assistant also costs time and can produce a different result. |
| `who_it_is_for` | Teams building task-oriented assistants, quality reviewers, and developers who need repeatable checks for tool use. |
| `common_use_cases` | Confirming that the right tools were called; comparing an observed action sequence with an expected one; reviewing failures from saved traces; creating release gates from deterministic checks. |
| `how_it_works_in_practice` | An instrumented application produces an OpenTelemetry trace, which is a structured timeline of what happened. agentevals compares that saved timeline with an expected behavior definition and produces review results. |
| `ai_lab_use_case` | Build a no-install design spike that maps one sanitized benchmark artifact into a trace-like fixture and defines deterministic checks without creating or importing scores. |
| `limitations` | It does not currently fit long coding-agent sessions well, expects a particular trace shape, and its optional language-model judges or cloud integrations are outside the proposed demo. |
| `why_interesting` | OpenTelemetry-based offline review could strengthen the distinction between machine-generated evidence and human-confirmed AI Lab decisions. |
| `business_tie_in` | A trace-review demo is a credible client-facing quality-control feature for automations that use several tools. |
| `learning_value` | High: trace schemas, deterministic evaluation, evidence lineage, and failure diagnosis. |
| `local_fit` | High for a static-fixture design review on the confirmed Mac; direct integration would require a later dependency and schema review. |
| `risk_notes` | The repository has Python/UI/Kubernetes surfaces and optional cloud graders. Direct adoption would add dependencies and trace data may contain prompts, tool arguments, or private paths. |
| `recommended_next_step` | `ready_for_review`: approve a one-week static trace/evaluator mapping only, with no package installation or score import. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-19 |
| `cost_scope` | Planning-only static trace fixture, evaluator matrix, and UI storyboard on confirmed lab compute; no installation or execution. |
| `incremental_cost` | $0-$25 project-specific cash on the confirmed lab host. |
| `from_scratch_cost` | $0-$25 for the defined software/design MVP when a general-purpose computer is available. |
| `portfolio_build_cost` | $0-$75 for polished fixtures, diagrams, and a recorded walkthrough; no dedicated hardware. |
| `diy_effort_hours` | 10-16 hours. |
| `recurring_monthly_cost` | $0 for the local static-fixture scope. |
| `cost_confidence` | High for cash scope; Medium for effort because trace adaptation complexity is untested. |
| `cost_assumptions` | Reuses the confirmed Mac, existing editor, and sanitized repo-local fixtures. |
| `cost_exclusions` | Package installation, direct integration, cloud graders, hosted telemetry, dedicated compute, and paid support. |
| `cost_source_urls` | https://github.com/agentevals-dev/agentevals |
| `source_last_checked` | 2026-07-19 |
| `price_valid_until` | 2026-08-18 |
| `refresh_reason` | Refresh if license, release, local-first claim, trace format, or optional cloud behavior changes. |
| `first_seen` | 2026-07-19 |
| `last_seen` | 2026-07-19 |
| `change_status` | `new` |
| `change_summary` | First radar appearance; source showed Apache-2.0, local-first metadata, 149 stars, and v0.9.7 dated 2026-07-10. |
| `one_week_deliverable` | A sanitized trace schema map, three deterministic evaluator definitions, and an AI Lab evidence-flow storyboard. |
| `success_criteria` | Reviewers can trace each proposed check to a fixture field, identify where human confirmation occurs, and verify that no score or model run is implied. |
| `demo_artifact` | Markdown design note plus sanitized JSON fixtures and static UI mockup. |
| `prerequisites` | User approval for a design-only spike and selection of one sanitized benchmark artifact shape. |
| `first_three_tasks` | 1. Select and sanitize one existing artifact shape. 2. Map it to a minimal trace and expected-action schema. 3. Draft three deterministic checks and a review storyboard. |
| `blockers` | Existing AI Lab artifacts may not contain OpenTelemetry-compatible events; score semantics and import boundaries require review. |
| `stop_conditions` | Stop if useful checks require raw private prompts, direct package execution, cloud judges, or changing confirmed-score semantics. |
| `safety_notes` | Keep prompts, tool arguments, responses, paths, and trace IDs local and sanitized; no package, model, cloud API, or dashboard import is approved. |

### project_opportunity: Raspberry Pi AI HAT+ 2

| Field | Value |
| --- | --- |
| `project_id` | `20260719-raspberry-pi-ai-hat-plus-2` |
| `project_name` | Raspberry Pi AI HAT+ 2 |
| `source_url` | https://www.raspberrypi.com/products/ai-hat-plus-2/ |
| `item_type` | `project_opportunity` |
| `priority_score` | 4 |
| `priority_rationale` | Strong edge-AI and portfolio value with official local-processing support, but it exceeds the confirmed $300 tier from scratch and requires unconfirmed Raspberry Pi inventory. |
| `plain_language_summary` | The AI HAT+ 2 is an add-on board that gives a Raspberry Pi 5 extra hardware for running small language and vision AI locally. It includes its own memory so the Pi can handle more than basic camera recognition. |
| `problem_it_solves` | A normal Raspberry Pi can struggle with useful generative-AI tasks, while cloud services add latency, recurring cost, and privacy concerns. |
| `who_it_is_for` | Edge-computing learners, prototype builders, educators, and teams that need small AI workloads to run without a continuous internet connection. |
| `common_use_cases` | Local document question answering; small coding or translation assistants; camera scene descriptions; private speech or vision experiments. |
| `how_it_works_in_practice` | The add-on connects to a Raspberry Pi 5 and handles supported AI calculations using its accelerator and 8 GB of dedicated memory. The Pi manages the application, storage, camera, and user interface. |
| `ai_lab_use_case` | Design a local field-assistant demo that compares a small document question-answering task with a camera scene-summary task and records practical limits. |
| `limitations` | It supports models only up to roughly 6-7 billion parameters, requires a Raspberry Pi 5 and supported Hailo software, and will not match the broad knowledge or flexibility of the Mac Studio. |
| `why_interesting` | It creates a tangible edge-AI portfolio project and a useful contrast with the AI Camera's vision-only accelerator. |
| `business_tie_in` | Could demonstrate private kiosks, field manuals, inspection assistants, or low-connectivity client prototypes. |
| `learning_value` | High: edge deployment constraints, accelerator compatibility, memory budgeting, thermals, and local UI design. |
| `local_fit` | Good category fit, but owned Raspberry Pi 5, power, storage, cooler, and camera inventory are unconfirmed. |
| `risk_notes` | Hailo model compatibility, software supply chain, thermal limits, camera privacy, and the cost premium over a software-only Mac demo require review. |
| `recommended_next_step` | `needs_more_info`: confirm Raspberry Pi inventory and approve a bill-of-materials and compatibility review before any purchase. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-19 |
| `cost_scope` | Eventual Raspberry Pi 5 plus AI HAT+ 2 local document/camera demo; the one-week action card remains design-only. |
| `incremental_cost` | $200-$230 if a compatible Raspberry Pi 5, power supply, cooling, and storage are already owned. |
| `from_scratch_cost` | $290-$350 for AI HAT+ 2, a minimal Raspberry Pi 5 host, power, cooling, and storage. |
| `portfolio_build_cost` | $360-$500 with case, camera, better storage, cables, and presentation finish. |
| `diy_effort_hours` | 12-20 hours after hardware and artifact approval; 6-10 hours for the design-only week. |
| `recurring_monthly_cost` | Approximately $1-$4 in electricity under intermittent local use; no cloud subscription assumed. |
| `cost_confidence` | Medium: official $200 HAT price is clear, but Pi tier, reseller stock, accessories, tax, and shipping vary. |
| `cost_assumptions` | Uses a low-memory Pi 5 because the HAT has 8 GB dedicated memory; includes basic power, cooling, and storage. |
| `cost_exclusions` | Tax, shipping, display, keyboard, battery, enclosure fabrication, paid datasets, model licensing, and replacement parts. |
| `cost_source_urls` | https://www.raspberrypi.com/products/ai-hat-plus-2/ ; https://www.raspberrypi.com/products/raspberry-pi-5/ ; https://www.raspberrypi.com/news/a-new-3gb-raspberry-pi-4-for-83-75-and-more-memory-driven-price-increases/ |
| `source_last_checked` | 2026-07-19 |
| `price_valid_until` | 2026-08-18 |
| `refresh_reason` | Refresh within 30 days or sooner if Raspberry Pi memory pricing, reseller stock, or hardware inventory changes. |
| `first_seen` | 2026-07-19 |
| `last_seen` | 2026-07-19 |
| `change_status` | `new` |
| `change_summary` | First radar appearance; official page showed a current $200 price and local 8 GB accelerator hardware. |
| `one_week_deliverable` | A compatibility matrix, sourced bill of materials, two-screen demo storyboard, and go/no-go review note. |
| `success_criteria` | The review identifies a supported small-model path, complete hardware assumptions, privacy boundaries, total cost range, and a stop condition without purchasing or installing anything. |
| `demo_artifact` | Sanitized architecture diagram, bill of materials, interaction storyboard, and risk checklist. |
| `prerequisites` | Confirm owned Raspberry Pi 5/accessories and select either document Q&A or camera scene summaries as the primary demo. |
| `first_three_tasks` | 1. Confirm hardware inventory and preferred use case. 2. Compare official HAT model/runtime support with the proposed task. 3. Finalize the bill of materials, storyboard, and approval gates. |
| `blockers` | Inventory, budget over $300, exact supported artifact, thermal plan, camera scope, and Hailo software review are unresolved. |
| `stop_conditions` | Stop if the useful task needs an unsupported model, mandatory cloud account, hidden telemetry, more than the approved budget, or unsafe camera collection. |
| `safety_notes` | No purchase, model/package download, installation, camera deployment, biometric identification, covert monitoring, or cloud connection is approved. |

### project_opportunity: PlotJuggler

| Field | Value |
| --- | --- |
| `project_id` | `20260719-plotjuggler-passive-log-review` |
| `project_name` | PlotJuggler |
| `source_url` | https://github.com/PlotJuggler/PlotJuggler |
| `item_type` | `project_opportunity` |
| `priority_score` | 4 |
| `priority_rationale` | Mature local visualization, current maintenance, macOS arm64 metadata, and passive file analysis provide a safe robotics learning path without flight control. |
| `plain_language_summary` | PlotJuggler turns recorded sensor and machine data into interactive charts. It helps a person line up many signals on one timeline and see what happened before a failure or unusual event. |
| `problem_it_solves` | Robot and drone logs contain thousands of time-stamped measurements that are hard to understand as raw numbers. |
| `who_it_is_for` | Robotics learners, test engineers, drone-log reviewers, and developers troubleshooting sensors or control systems. |
| `common_use_cases` | Reviewing a saved drone flight log; comparing commanded and actual motion; inspecting robot sensor timing; building reusable chart layouts for repeated tests. |
| `how_it_works_in_practice` | A user opens a supported data file, selects measurements, and arranges charts on a shared timeline. Saved layouts make later recordings easier to compare. |
| `ai_lab_use_case` | Design a passive flight-log review storyboard using synthetic or explicitly approved recorded data, with charts for position, battery, and estimator health. |
| `limitations` | It visualizes and transforms data but does not explain every anomaly automatically. File-format plugins, beta releases, and complex robot logs still require domain knowledge. |
| `why_interesting` | It supports a legal, passive drone/robotics lane and could inspire an AI-assisted explanation layer without connecting to a live vehicle. |
| `business_tie_in` | A clear post-run review dashboard is portfolio evidence for maintenance, inspection, fleet, and field-system workflows. |
| `learning_value` | High: time-series analysis, flight-log structure, visualization design, and anomaly triage. |
| `local_fit` | Good: source metadata lists macOS arm64 and local file loading; direct use still requires separate installation approval. |
| `risk_notes` | Beta 4 release, plugins, anonymous telemetry notes in changelog, native binaries, and untrusted log files need review before execution. |
| `recommended_next_step` | `ready_for_review`: approve a static log-dashboard storyboard and file-format threat review, not installation. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-19 |
| `cost_scope` | Static dashboard storyboard and sanitized sample-data specification on confirmed lab compute; no binary download or log execution. |
| `incremental_cost` | $0-$20 project-specific cash. |
| `from_scratch_cost` | $0-$25 for the defined software/design MVP when a general-purpose computer is available. |
| `portfolio_build_cost` | $0-$75 for polished synthetic fixtures, diagrams, and recorded walkthrough. |
| `diy_effort_hours` | 8-14 hours. |
| `recurring_monthly_cost` | $0 for local file-based planning scope. |
| `cost_confidence` | High for cash; Medium for effort because real ULog mapping is not yet tested. |
| `cost_assumptions` | Reuses confirmed lab compute and synthetic or explicitly approved sanitized log metadata. |
| `cost_exclusions` | Binary installation, ROS 2, live vehicles, real flight data collection, plugins, sensors, and commercial support. |
| `cost_source_urls` | https://github.com/PlotJuggler/PlotJuggler |
| `source_last_checked` | 2026-07-19 |
| `price_valid_until` | 2026-08-18 |
| `refresh_reason` | Refresh on stable PlotJuggler 4 release, license/telemetry change, or selected log-format change. |
| `first_seen` | 2026-07-19 |
| `last_seen` | 2026-07-19 |
| `change_status` | `new` |
| `change_summary` | First radar appearance; source showed about 6,000 stars and PlotJuggler 4 beta 1 released 2026-07-02. |
| `one_week_deliverable` | A three-panel flight-log review storyboard, synthetic data dictionary, and file-handling threat checklist. |
| `success_criteria` | The artifact shows how three useful signals align in time, names the questions each chart answers, and contains no live control or private flight data. |
| `demo_artifact` | Static dashboard mockup plus synthetic CSV/ULog field map and review checklist. |
| `prerequisites` | User approval of passive recorded-data scope and selection of PX4 ULog or generic CSV as the first format. |
| `first_three_tasks` | 1. Choose the passive file format and three review questions. 2. Define synthetic fields and chart layouts. 3. Draft the threat checklist and narrated storyboard. |
| `blockers` | Real log provenance, macOS binary review, plugin requirements, and telemetry behavior are unresolved. |
| `stop_conditions` | Stop if the demo requires live vehicle connection, flight commands, unapproved private logs, unsafe binary execution, or cloud upload. |
| `safety_notes` | Passive offline review only; no drone connection, flight/control operation, real-person tracking, log upload, binary download, or installation is approved. |

### project_opportunity: SigMF capture catalog

| Field | Value |
| --- | --- |
| `project_id` | `20260719-sigmf-capture-catalog` |
| `project_name` | SigMF capture catalog |
| `source_url` | https://github.com/sigmf/SigMF |
| `item_type` | `project_opportunity` |
| `priority_score` | 4 |
| `priority_rationale` | A standards-based metadata catalog is a low-cost, receive-only learning project that can begin with synthetic files and preserve strong legal/privacy boundaries. |
| `plain_language_summary` | SigMF is a standard way to label recorded radio or sensor signals so people and software know when, where, and how the recording was made. A capture catalog would organize those labels without needing to understand raw signal bytes. |
| `problem_it_solves` | Signal recordings become unusable when details such as sample rate, frequency, equipment, and timestamps are lost or written inconsistently. |
| `who_it_is_for` | Radio learners, researchers, educators, and teams archiving passive signal recordings for reproducible analysis. |
| `common_use_cases` | Cataloging receive-only recordings; validating required metadata; annotating interesting time ranges; sharing a sanitized dataset description without sharing private raw data. |
| `how_it_works_in_practice` | Each recording has a data file and a small JSON metadata file. The catalog reads only approved metadata, checks it against the standard, and presents searchable summaries and annotations. |
| `ai_lab_use_case` | Build a no-capture design prototype with synthetic metadata, validation rules, and a local catalog mockup for passive educational recordings. |
| `limitations` | SigMF is a specification rather than a complete user application. Raw recordings can be large, local radio laws still apply, and metadata may reveal location or equipment details. |
| `why_interesting` | It creates a safe foundation for future SDR learning while emphasizing provenance, reproducibility, and metadata hygiene. |
| `business_tie_in` | The same catalog pattern applies to sensor archives, lab datasets, quality evidence, and field-data handoffs. |
| `learning_value` | High: schemas, provenance, validation, signal metadata, and privacy-aware dataset design. |
| `local_fit` | Excellent for a stdlib-only metadata prototype on the confirmed Mac; no receiver is needed for the first week. |
| `risk_notes` | Metadata may include coordinates, operator identity, or sensitive frequency notes. Live capture and decoding can create legal/privacy issues outside the synthetic scope. |
| `recommended_next_step` | `ready_for_review`: approve a synthetic metadata catalog specification only. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-19 |
| `cost_scope` | Stdlib-only synthetic SigMF metadata validator/catalog design; optional passive receiver is portfolio expansion only. |
| `incremental_cost` | $0-$15 on confirmed lab compute. |
| `from_scratch_cost` | $0-$25 for the synthetic metadata-only MVP. |
| `portfolio_build_cost` | $40-$100 if a later approved passive receiver, antenna, and storage are added. |
| `diy_effort_hours` | 6-10 hours for metadata MVP; 12-20 hours with later passive capture review. |
| `recurring_monthly_cost` | $0-$2 for local storage/power at small scale. |
| `cost_confidence` | High for metadata-only cash; Low for receiver expansion because the public vendor price/stock note is old. |
| `cost_assumptions` | First week uses synthetic metadata and existing compute; optional receiver pricing uses a public V4 dongle observation only. |
| `cost_exclusions` | Tax, shipping, live capture, antennas beyond a starter set, filters, large storage, paid mapping data, and legal advice. |
| `cost_source_urls` | https://github.com/sigmf/SigMF ; https://www.rtl-sdr.com/rtl-sdr-blog-v4-dongle-initial-release/ |
| `source_last_checked` | 2026-07-19 |
| `price_valid_until` | 2026-07-26 |
| `refresh_reason` | Refresh the optional receiver price and stock within seven days before any hardware approval; metadata-only software remains $0. |
| `first_seen` | 2026-07-19 |
| `last_seen` | 2026-07-19 |
| `change_status` | `new` |
| `change_summary` | First radar appearance of the SigMF standard as a local passive-data catalog opportunity. |
| `one_week_deliverable` | A synthetic SigMF metadata schema subset, six validation cases, and a searchable catalog storyboard. |
| `success_criteria` | Fixtures cover valid, missing, malformed, and privacy-sensitive metadata; the storyboard works without raw recordings or network access. |
| `demo_artifact` | Markdown specification, sanitized JSON fixtures, validation matrix, and static catalog mockup. |
| `prerequisites` | User approval of synthetic-only receive-side scope and confirmation that no private location/equipment metadata will be committed. |
| `first_three_tasks` | 1. Select the minimal SigMF fields and privacy rules. 2. Draft six synthetic validation fixtures. 3. Design the local catalog and review flow. |
| `blockers` | Future capture hardware, jurisdiction-specific radio rules, storage policy, and private metadata handling are unconfirmed. |
| `stop_conditions` | Stop if the MVP requires live interception, transmission, private coordinates, unapproved raw recordings, or package installation. |
| `safety_notes` | Synthetic metadata and passive educational scope only; no transmission, interception of private communications, live capture, decoding, location disclosure, or hardware purchase is approved. |

## Reviewer Notes

- None of the model candidates is ready for evaluation. Each needs an exact
  artifact, hash, license/provenance review, approved local runner, and specific
  benchmark fixture before using `evals/local-llm-benchmark/SPEC.md` and
  `skills/local-llm-eval`.
- Project action cards are planning-only and do not approve installation,
  execution, purchase, credentials, radio capture/transmission, or flight.
- `data/model_registry/candidates.csv` and
  `data/project_registry/github_repos.csv` remain unchanged.

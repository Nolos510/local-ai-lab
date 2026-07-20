# AI Lab Radar Source Packet

Packet title: Daily External Radar Delta Scan
Packet date: 2026-07-20
Prepared by: Codex automation
Approved for radar review: no
Safe to commit: no

## Scope

Daily External Radar ran because no new user-approved Local Radar packet was
present. This packet records public metadata and planning estimates only. It
does not approve registry entry, downloads, installation, model or repository
execution, benchmark scoring, purchases, radio reception or transmission,
flight operations, or dashboard decisions.

Source access date: 2026-07-20.

The ignored local profile confirms an existing Apple Silicon host. Raspberry
Pi, software-defined radio, drone inventory, maximum DIY hours, and portfolio
budget remain unconfirmed. No private inventory details are copied here.

## Reviewed Source Set

The scan reviewed 39 public metadata items and de-duplicated them against the
model and project registries and all prior radar packets and reports. Only five
new, high-signal items are normalized below.

| # | Item | Type | Source URL | Scan note |
| --- | --- | --- | --- | --- |
| 1 | Inkling | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; the 952B scale is not practical for the next local benchmark task. |
| 2 | Ternary-Bonsai-27B-gguf | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; custom low-bit runtime concerns overlap prior Bonsai review. |
| 3 | Bonsai-27B-gguf | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; already covered by the prior Bonsai source set. |
| 4 | GLM-5.2 | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; 753B scale is not practical for the next local evaluation task. |
| 5 | Qwythos-9B-Claude-Mythos-5-1M-GGUF | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; derivative provenance and extreme context claims remain unresolved. |
| 6 | krea2-identity-edit | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; image identity editing is outside the current benchmark lane. |
| 7 | Unlimited-OCR | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; optical character recognition overlaps the stronger Docling project review and needs custom-loader review. |
| 8 | OvisOCR2 | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; runtime and artifact path were not clear enough for conservative review. |
| 9 | ThinkingCap-Qwen3.6-27B | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; derivative scope overlaps the existing Qwen coding lane. |
| 10 | Qwen3.6-35B-A3B community derivative | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; provenance and safety modifications add review burden. |
| 11 | MOSS-Transcribe-Diarize | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; speech processing is outside the current benchmark lane. |
| 12 | Hy3-GGUF | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; 295B scale and artifact lineage reduce practicality. |
| 13 | MiniCPM5-1B Fable variant | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; weaker provenance than the MiniCPM artifact reported on 2026-07-19. |
| 14 | Bonsai-27B-mlx-1bit | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; custom low-bit MLX path overlaps prior Bonsai review. |
| 15 | Wan-Dancer-14B | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; image-to-video is outside current model evaluation scope. |
| 16 | MiniCPM5-1B Fable V2 GGUF | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; no stronger benchmark fit than yesterday's MiniCPM candidate. |
| 17 | Ternary-Bonsai-27B-mlx-2bit | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; custom runtime path and prior overlap. |
| 18 | Qwythos-9B-v2-GGUF | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; derivative provenance is weaker than selected candidates. |
| 19 | Cactus needle | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; task and role metadata were insufficient. |
| 20 | Inkling-GGUF community quantization | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; artifact size is impractical despite quantization. |
| 21 | Qwen3.6-27B Fable community derivative | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; provenance and benchmark overlap. |
| 22 | Hy3 | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; 299B scale is not a near-term local benchmark priority. |
| 23 | GLM-5.2-colibri-int4 | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; exact local runtime and artifact burden remain unclear. |
| 24 | Qwen fixed chat templates | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; template files are not a model candidate. |
| 25 | LTX face identity adapter | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; image identity editing is outside scope and privacy sensitive. |
| 26 | MOSS-VL-Realtime | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; realtime video and custom runtime needs exceed the current lane. |
| 27 | Gemma 4 31B IT | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; larger multimodal scope offers less immediate value than Lemma's explicit Apple Silicon artifacts. |
| 28 | LTX CrossView adapter | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; video adapter scope is outside the current benchmark. |
| 29 | Agents-A1 | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; exact artifact and safe local runtime path were not explicit. |
| 30 | M87 image model | model_candidate | https://huggingface.co/models?format=gguf | Not shortlisted; task is outside the current local language-model benchmark. |
| 31 | Lemma 8B GGUF and MLX | model_candidate | https://huggingface.co/lthn/lemma | Shortlisted; explicit Apple Silicon artifacts, sizes, context, and local runtime claims support a conservative review. |
| 32 | llama-swap | project_opportunity | https://github.com/mostlygeek/llama-swap | Shortlisted; directly addresses local model routing and memory management. |
| 33 | Docling | project_opportunity | https://github.com/docling-project/docling | Shortlisted; local document normalization maps directly to the RAG ingestion loop. |
| 34 | WebODM | project_opportunity | https://github.com/WebODM/WebODM | Shortlisted; a 2026-07-19 release and clear offline aerial-imagery output make a strong portfolio opportunity. |
| 35 | SatDump | project_opportunity | https://github.com/SatDump/SatDump | Shortlisted; offline processing provides a passive, educational radio-learning path, but release freshness is a concern. |
| 36 | Frigate | project_opportunity | https://github.com/blakeblackshear/frigate | Not shortlisted; camera privacy, dedicated hardware, storage, and container hardening make it less suitable than today's design-first items. |
| 37 | promptfoo | project_opportunity | https://github.com/promptfoo/promptfoo | Not shortlisted; strong evaluation reference but broad provider, remote-content, and trusted-code surfaces overlap yesterday's agentevals review. |
| 38 | OpenTelemetry Collector | project_opportunity | https://github.com/open-telemetry/opentelemetry-collector | Not shortlisted; useful infrastructure reference but too broad for the next one-week AI Lab deliverable. |
| 39 | Argilla | project_opportunity | https://github.com/argilla-io/argilla | Not shortlisted; human-feedback value is clear, but its service stack is broader than the current evidence task. |

## Supplemental Cost Sources

| Project | Source URL | Public pricing or scope evidence |
| --- | --- | --- |
| llama-swap | https://github.com/mostlygeek/llama-swap | MIT project described as one binary and one configuration file; the planning MVP reuses confirmed lab compute. |
| Docling | https://github.com/docling-project/docling | MIT project with local execution and macOS arm64 metadata; model licenses and runtime dependencies remain separate review gates. |
| WebODM | https://github.com/WebODM/WebODM | AGPL-3.0 project says official installers are free and lists a 2026-07-19 release; the planning MVP reuses confirmed lab compute. |
| SatDump | https://github.com/SatDump/SatDump | GPL-3.0 project supports offline recorded-data processing and provides dependency-free macOS builds; no installation is approved here. |
| Optional passive receiver | https://www.rtl-sdr.com/rtl-sdr-blog-v4-dongle-initial-release/ | Vendor page lists a low-cost receiver and antenna kit, but the price observation is old and must be refreshed before any purchase decision. |

## Highest-Signal Items

### model_candidate: Lemma 8B GGUF and MLX

| Field | Value |
| --- | --- |
| `candidate_id` | `20260720-lemma-8b-gguf-mlx` |
| `model_name` | Lemma 8B GGUF and MLX |
| `model_family` | Gemma 4 E4B-derived Lemma |
| `provider_or_org` | Lethean / lthn |
| `params_b` | Source-declared 7.9B total and 4.5B effective |
| `format_or_runtime` | GGUF with separate MLX repositories |
| `claimed_context_window` | Source-declared 128K tokens |
| `license` | EUPL-1.2 shown by the source page; base-model and merged-weight compatibility still need review. |
| `source_url` | https://huggingface.co/lthn/lemma |
| `public_adoption_signal` | Source page showed 230 downloads last month; context only, not trust or quality evidence. |
| `why_interesting` | The source publishes explicit 5-15.1 GB artifact sizes, GGUF and MLX paths, a 128K context claim, and Apple Silicon verification for a compact multimodal model. |
| `local_fit` | Strong size fit for the confirmed 256 GB Apple Silicon host, but the current benchmark is text-first and does not cover its image or audio claims. |
| `estimated_artifact_size` | Source-declared: 5.34 GB Q4_K_M, 5.76 GB Q5_K_M, 6.22 GB Q6_K, 8.03 GB Q8_0, or 15.1 GB BF16. |
| `estimated_disk_requirement` | Inferred: about 8-12 GB for one Q4-Q6 artifact plus template, provenance, and benchmark evidence. |
| `expected_memory_range` | Inferred: about 8-18 GB at modest text context for Q4-Q6; image, audio, or long-context use could require materially more. |
| `compatible_local_runtimes` | Source-declared GGUF paths for Ollama, llama.cpp, GPT4All, and LM Studio, plus separate MLX builds; exact local versions are unverified. |
| `benchmark_gap` | Exact artifact and hash, EUPL/base-license review, merged-weight provenance, chat template, runtime version, text-only context cap, and separate multimodal fixtures are missing. |
| `risk_notes` | The source is a third-party fine-tune with merged ethical-kernel weights, includes install scripts and agent integrations that are outside radar boundaries, and publishes its own incomplete benchmark program. |
| `security_review_status` | `needs_review` |
| `download_approval` | `not_approved` |
| `license_review_status` | `needs_review` |
| `provenance_status` | `source_metadata_only` |
| `security_notes` | Review one exact GGUF or MLX artifact, hash evidence, source chain, EUPL/base terms, template, and runtime without executing model-card scripts or custom loaders. |
| `isolation_notes` | If separately approved later, use only an existing reviewed local runtime, disable agent/tool authority, and keep prompts and outputs local. |
| `recommended_next_step` | `needs_more_info` pending exact-artifact security, license, and benchmark-lane review. |
| `proposed_eval` | After separate approval only, connect a fixed text-capable artifact to `evals/local-llm-benchmark/SPEC.md` and `skills/local-llm-eval`; multimodal claims require separate fixtures. |
| `source_last_checked` | 2026-07-20 |
| `first_seen` | 2026-07-20 |
| `last_seen` | 2026-07-20 |
| `change_status` | `new` |
| `change_summary` | First radar appearance of this exact Lemma artifact family with explicit Apple Silicon metadata. |

### project_opportunity: llama-swap local model router

| Field | Value |
| --- | --- |
| `project_id` | `20260720-llama-swap-local-router` |
| `project_name` | llama-swap local model router |
| `source_url` | https://github.com/mostlygeek/llama-swap |
| `item_type` | `project_opportunity` |
| `priority_score` | 5 |
| `priority_rationale` | It directly addresses how AI Lab OS could select among local model servers while limiting how many models stay loaded, and the source presents a small MIT-licensed Go binary. |
| `plain_language_summary` | llama-swap is a traffic controller for local AI models. An application asks for a named model, and llama-swap starts or selects the matching local server while unloading another when resources are needed. |
| `problem_it_solves` | A local lab can own many models but cannot keep every one in memory at once or force every application to know how each runtime starts. |
| `who_it_is_for` | Local AI developers, small teams sharing one inference machine, and application builders who want one stable local endpoint. |
| `common_use_cases` | Switching between a coding and chat model; routing embedding requests separately; unloading idle models; presenting one local API to several tools. |
| `how_it_works_in_practice` | A client sends a request naming a model. The router checks its configuration, starts the appropriate local server if needed, forwards the request, and manages idle processes. |
| `ai_lab_use_case` | Produce a design-only compatibility map for the existing provider harness, two local runtimes, model roles, logging boundaries, and failure behavior without installing or running the router. |
| `limitations` | It does not supply models, verify their safety, or guarantee every server behaves identically. Its configuration can launch commands and hooks, so it creates a meaningful execution boundary. |
| `why_interesting` | A reviewed router could reduce duplicated provider configuration and make local model selection more predictable across the dashboard, benchmark harness, and RAG app. |
| `business_tie_in` | A single local endpoint with controlled model switching is a credible private-AI operations feature for client prototypes. |
| `learning_value` | High: process lifecycle, resource scheduling, compatible APIs, failure isolation, and observability. |
| `local_fit` | High concept fit for the confirmed Mac Studio, but Apple Silicon process behavior and existing provider boundaries need a static architecture review first. |
| `risk_notes` | Model definitions can execute local commands, hooks, environment variables, and filters; logs may include request or response data; remote binding could expose model endpoints. |
| `recommended_next_step` | `ready_for_review`: approve a static architecture and threat-model spike only, with no binary, package, model, or process execution. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-20 |
| `cost_scope` | Planning-only provider compatibility matrix, process lifecycle diagram, and threat model on confirmed lab compute. |
| `incremental_cost` | $0-$25 project-specific cash on the confirmed lab host. |
| `from_scratch_cost` | $0-$25 for the defined software/design MVP when a general-purpose computer is available. |
| `portfolio_build_cost` | $0-$75 for polished diagrams, failure-state mockups, and a recorded walkthrough; no dedicated hardware. |
| `diy_effort_hours` | 8-14 hours. |
| `recurring_monthly_cost` | $0 for the local design scope. |
| `cost_confidence` | High for cash scope; Medium for effort because provider-boundary complexity is untested. |
| `cost_assumptions` | Reuses the confirmed Mac, existing editor, existing provider documentation, and synthetic request examples. |
| `cost_exclusions` | Installation, binaries, models, runtime execution, benchmark runs, electricity, paid support, and any remote exposure. |
| `cost_source_urls` | https://github.com/mostlygeek/llama-swap |
| `source_last_checked` | 2026-07-20 |
| `price_valid_until` | 2026-08-19 |
| `refresh_reason` | Refresh if license, release, command or hook behavior, API compatibility, logging, or telemetry posture changes. |
| `first_seen` | 2026-07-20 |
| `last_seen` | 2026-07-20 |
| `change_status` | `new` |
| `change_summary` | First radar appearance; source showed MIT licensing, about 5.1k stars, and current model-switching and monitoring features. |
| `one_week_deliverable` | Provider compatibility matrix, lifecycle diagram, failure-state storyboard, and command/logging threat model. |
| `success_criteria` | Reviewers can identify how two existing local runtimes would be addressed, where processes start and stop, what is logged, and which boundaries require approval. |
| `demo_artifact` | Markdown architecture note plus sanitized configuration sketch and static dashboard flow. |
| `prerequisites` | User approval for a design-only spike and selection of two existing provider shapes; no model identifiers need to be disclosed in tracked files. |
| `first_three_tasks` | 1. Map existing provider request and model-role boundaries. 2. Diagram router process, port, timeout, and failure behavior. 3. Draft a sanitized configuration sketch and threat checklist. |
| `blockers` | Exact provider lifecycle behavior, local port policy, logging requirements, and whether the router duplicates existing CLI orchestration are unresolved. |
| `stop_conditions` | Stop if the value depends on exposing a non-loopback endpoint, running unreviewed hooks, leaking prompts, or replacing the existing provider abstraction without an architecture decision record. |
| `safety_notes` | Planning only; no binary, package, model, command, hook, server, network listener, or benchmark execution is approved. |

### project_opportunity: Docling ingestion compatibility spike

| Field | Value |
| --- | --- |
| `project_id` | `20260720-docling-ingestion-compatibility` |
| `project_name` | Docling ingestion compatibility spike |
| `source_url` | https://github.com/docling-project/docling |
| `item_type` | `project_opportunity` |
| `priority_score` | 4 |
| `priority_rationale` | Document normalization is directly relevant to the RAG backbone, and the source declares local arm64 execution, but its broad parser, model, and dependency surface requires review before integration. |
| `plain_language_summary` | Docling turns many document types into a consistent structured form. It tries to preserve useful details such as headings, reading order, tables, formulas, and page layout instead of returning a flat block of text. |
| `problem_it_solves` | Retrieval systems lose accuracy when PDFs, slides, spreadsheets, and scans are converted inconsistently or their structure disappears. |
| `who_it_is_for` | Teams building document search, research assistants, compliance archives, or internal knowledge tools. |
| `common_use_cases` | Converting PDFs to Markdown; extracting tables; normalizing office files; preparing scanned pages for retrieval; creating structured document JSON. |
| `how_it_works_in_practice` | A document enters a conversion pipeline, format-specific parsers and optional recognition models identify its content and layout, and the result is exported in a consistent structure. |
| `ai_lab_use_case` | Create a no-install mapping from five existing sample-document shapes to AI Lab's ingestion metadata, chunking expectations, and failure cases. |
| `limitations` | Complex documents can still be parsed incorrectly, optional recognition models add downloads and licenses, and direct adoption would add a large dependency and model-cache surface. |
| `why_interesting` | A structured parser could improve citations and table handling while reducing custom format-specific ingestion code. |
| `business_tie_in` | Better document normalization is useful in client knowledge bases, document review, finance operations, and internal search products. |
| `learning_value` | High: document structure, optical character recognition, provenance, chunking, parser evaluation, and dependency review. |
| `local_fit` | Strong functional fit and source-declared macOS arm64 support, but current v0 scope and dependency rules favor a compatibility study before any code change. |
| `risk_notes` | The project supports URLs, many file parsers, optional models, service and MCP surfaces, and third-party integrations. Documents may contain active content or private data, and individual model licenses vary. |
| `recommended_next_step` | `needs_more_info`: approve a static ingestion-schema and dependency review with no package, model, URL, or document processing. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-20 |
| `cost_scope` | Planning-only five-format compatibility matrix, metadata mapping, parser-risk checklist, and benchmark fixture plan on confirmed lab compute. |
| `incremental_cost` | $0-$25 project-specific cash on the confirmed lab host. |
| `from_scratch_cost` | $0-$25 for the defined design MVP when a general-purpose computer and safe sample documents are available. |
| `portfolio_build_cost` | $0-$100 for polished before-and-after document mockups and a narrated ingestion storyboard. |
| `diy_effort_hours` | 10-18 hours. |
| `recurring_monthly_cost` | $0 for the local design scope. |
| `cost_confidence` | High for cash scope; Medium for effort because format edge cases and model requirements are not tested. |
| `cost_assumptions` | Reuses the confirmed Mac and sanitized existing sample-document shapes without processing them during radar. |
| `cost_exclusions` | Installation, parser execution, model artifacts, optical character recognition weights, cloud services, private documents, dependency additions, and paid support. |
| `cost_source_urls` | https://github.com/docling-project/docling |
| `source_last_checked` | 2026-07-20 |
| `price_valid_until` | 2026-08-19 |
| `refresh_reason` | Refresh if license, release, supported formats, model-download behavior, local execution, security policy, or dependency surface changes. |
| `first_seen` | 2026-07-20 |
| `last_seen` | 2026-07-20 |
| `change_status` | `new` |
| `change_summary` | First radar appearance; source showed MIT licensing, about 63.5k stars, local arm64 support, and v2.113.0 dated 2026-07-14. |
| `one_week_deliverable` | Five-format compatibility matrix, AI Lab metadata map, ten parser failure cases, and a dependency/model review checklist. |
| `success_criteria` | Each format has expected structure, citation metadata, failure handling, and an explicit decision on whether it needs models, network access, or a new dependency. |
| `demo_artifact` | Markdown design note, sanitized input/output examples, fixture inventory, and static ingestion-flow mockup. |
| `prerequisites` | User approval for a design-only spike and confirmation that existing sample files are safe to describe at a schema level. |
| `first_three_tasks` | 1. Select five sanitized document shapes and desired outputs. 2. Map Docling fields to current ingestion and citation metadata. 3. Draft failure fixtures and dependency, model, and network review gates. |
| `blockers` | Exact optional-model behavior, cache paths, dependency size, parser sandboxing, and compatibility with current chunking are unresolved. |
| `stop_conditions` | Stop if useful analysis requires processing private files, fetching URL content, downloading model weights, adding dependencies, or widening the v0 architecture without an architecture decision record. |
| `safety_notes` | No document, URL, package, model, parser, service, or MCP execution is approved; keep private documents and machine paths out of tracked artifacts. |

### project_opportunity: WebODM offline aerial mapping portfolio

| Field | Value |
| --- | --- |
| `project_id` | `20260720-webodm-offline-aerial-mapping` |
| `project_name` | WebODM offline aerial mapping portfolio |
| `source_url` | https://github.com/WebODM/WebODM |
| `item_type` | `project_opportunity` |
| `priority_score` | 4 |
| `priority_rationale` | It offers a strong drone-mapping portfolio story without requiring live flight, and the source shows a current release and free local software, but processing, licensing, and data provenance need review. |
| `plain_language_summary` | WebODM turns overlapping aerial photographs into measurable maps, elevation views, three-dimensional point clouds, and textured models. The proposed AI Lab project uses approved existing images and does not operate a drone. |
| `problem_it_solves` | A folder of aerial photographs is difficult to inspect or measure until the images are aligned into one consistent view of the area. |
| `who_it_is_for` | Surveying learners, construction and agriculture teams, environmental researchers, drone photographers, and mapping portfolio builders. |
| `common_use_cases` | Creating site maps; comparing terrain; measuring areas and distances; building a three-dimensional scene; documenting construction or land changes. |
| `how_it_works_in_practice` | A user supplies many overlapping images and basic project settings. Processing estimates camera positions, matches shared features, and produces map and three-dimensional outputs for review. |
| `ai_lab_use_case` | Design an offline workflow and dashboard storyboard for one sanitized, pre-approved aerial image set, with source provenance and no live flight or location-sensitive publication. |
| `limitations` | Results depend on image overlap, location metadata, camera quality, compute time, and processing settings. It is not a substitute for licensed surveying, and current WebODM is no longer the same project as OpenDroneMap. |
| `why_interesting` | The output is visually demonstrable, locally processable, and relevant to drone, computer-vision, geospatial, and client-reporting skills. |
| `business_tie_in` | A sanitized mapping demo can support construction progress, property documentation, agriculture, inspection, or environmental-monitoring portfolio conversations. |
| `learning_value` | High: photogrammetry, geospatial provenance, image quality, compute planning, licensing, and result communication. |
| `local_fit` | Good compute fit for the confirmed Mac at planning level, but actual architecture support, containers, storage, and processing engine behavior require review. |
| `risk_notes` | Aerial images may reveal people, private property, precise locations, or regulated sites. The AGPL license, decoupling from OpenDroneMap, container stack, and processing engine terms need review. |
| `recommended_next_step` | `ready_for_review`: approve an offline dataset-provenance and output-storyboard spike only, with no download, installation, image processing, or flight activity. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-20 |
| `cost_scope` | Planning-only dataset provenance checklist, processing architecture, output storyboard, and client-style report outline on confirmed lab compute. |
| `incremental_cost` | $0-$25 project-specific cash when an approved image set and existing host are available. |
| `from_scratch_cost` | $0-$50 for the defined software/design MVP with a general-purpose computer and approved existing images; no drone purchase. |
| `portfolio_build_cost` | $50-$200 for polished digital map views, a narrated case study, and optional physical print or storage after separate approval. |
| `diy_effort_hours` | 12-20 hours for the design MVP; actual processing effort is untested. |
| `recurring_monthly_cost` | $0 for a local offline design and future one-dataset demo. |
| `cost_confidence` | High for software cash baseline; Medium for presentation scope; Low for actual processing effort until architecture is verified. |
| `cost_assumptions` | Reuses the confirmed Mac and a sanitized image set that the user already owns or is separately approved to use. |
| `cost_exclusions` | Drone, camera, travel, flight authorization, surveying services, cloud processing, paid support, tax, printing vendor quotes, and storage beyond the small demo. |
| `cost_source_urls` | https://github.com/WebODM/WebODM |
| `source_last_checked` | 2026-07-20 |
| `price_valid_until` | 2026-08-19 |
| `refresh_reason` | Refresh if release, AGPL terms, OpenDroneMap relationship, installer price, processing engines, architecture support, or dataset scope changes. |
| `first_seen` | 2026-07-20 |
| `last_seen` | 2026-07-20 |
| `change_status` | `new` |
| `change_summary` | First radar appearance; source showed AGPL-3.0, free official installers, about 4.1k stars, project decoupling, and release 3.2.7 dated 2026-07-19. |
| `one_week_deliverable` | Dataset provenance checklist, offline processing diagram, four-output storyboard, and client-style case-study outline. |
| `success_criteria` | The design identifies an approved image source, four understandable outputs, privacy redactions, compute and storage assumptions, and a clear no-flight boundary. |
| `demo_artifact` | Markdown case-study plan, static map and three-dimensional output mockups, data lineage sheet, and risk checklist. |
| `prerequisites` | User approval for design-only work and confirmation of a sanitized image source with permission for local processing and portfolio display. |
| `first_three_tasks` | 1. Define the mapping question and approved image provenance. 2. Diagram local processing, storage, and four output types. 3. Draft privacy controls and the narrated case-study storyboard. |
| `blockers` | Approved imagery, architecture support, storage need, processing engine behavior, AGPL obligations, and output accuracy are unverified. |
| `stop_conditions` | Stop if the project requires live flight, restricted-site imagery, private coordinates, cloud processing, unapproved containers, or claims of survey-grade accuracy. |
| `safety_notes` | Offline approved imagery only; no drone purchase, flight, control, live telemetry, private-property surveillance, installation, container execution, or publication is approved. |

### project_opportunity: SatDump offline satellite-data learning

| Field | Value |
| --- | --- |
| `project_id` | `20260720-satdump-offline-learning` |
| `project_name` | SatDump offline satellite-data learning |
| `source_url` | https://github.com/SatDump/SatDump |
| `item_type` | `project_opportunity` |
| `priority_score` | 3 |
| `priority_rationale` | Offline recorded-data processing is a useful passive radio-learning path, but the latest visible tagged release is from 2024 and live reception introduces hardware, legal, storage, and RF safety questions. |
| `plain_language_summary` | SatDump converts certain recorded satellite radio signals into understandable products such as images and measurement files. The proposed AI Lab project starts with an offline storyboard and approved recordings, not live interception or transmission. |
| `problem_it_solves` | Raw satellite recordings are large streams of numbers that are not useful until the signal is decoded, checked, and organized into meaningful outputs. |
| `who_it_is_for` | Radio and space learners, weather-satellite hobbyists, educators, and researchers working with authorized public broadcasts or saved recordings. |
| `common_use_cases` | Processing weather-satellite recordings; visualizing decoded imagery; checking signal quality; learning how satellite data moves from radio samples to products. |
| `how_it_works_in_practice` | A user selects a recording and the matching satellite pipeline. The software demodulates and decodes the signal, then writes images, telemetry, or other products for offline review. |
| `ai_lab_use_case` | Produce a synthetic and approved-recording workflow storyboard that explains one weather-satellite pipeline, storage needs, metadata, and legal boundaries without receiving or decoding anything during radar. |
| `limitations` | It assumes radio and satellite knowledge, supported pipelines vary, recordings can be large, and successful live reception depends on location, antenna, timing, hardware, and local rules. |
| `why_interesting` | It combines passive radio, signal processing, data provenance, visualization, and edge-field-system learning in a tangible project. |
| `business_tie_in` | Direct commercial value is niche, but the workflow demonstrates sensor ingestion, offline field processing, and explainable data lineage useful in monitoring products. |
| `learning_value` | High: digital signal processing, satellite pipelines, metadata, storage planning, and legal receive-only boundaries. |
| `local_fit` | The source lists dependency-free macOS builds and offline processing, but architecture, binary provenance, and SDR inventory are unverified. |
| `risk_notes` | Live radio reception can implicate local law, privacy, antenna placement, bias power, and large untrusted files. The tagged release appears stale despite extensive repository history. |
| `recommended_next_step` | `needs_more_info`: confirm receive-only legal scope, approved recording provenance, current release status, storage budget, and SDR inventory before any execution plan. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-20 |
| `cost_scope` | Planning-only offline pipeline explainer, storage worksheet, provenance schema, and output storyboard; optional receiver cost is shown separately for future review. |
| `incremental_cost` | $0-$25 project-specific cash on the confirmed host for the planning-only scope. |
| `from_scratch_cost` | $0-$25 for an offline design MVP with a general-purpose computer and approved existing recording. |
| `portfolio_build_cost` | $60-$180 for an eventual receive-only learning kit and polished case study, pending fresh prices, inventory, and legal approval. |
| `diy_effort_hours` | 8-14 hours for the offline design; 16-30 hours for a future reviewed receive-only build. |
| `recurring_monthly_cost` | $0-$3 for local storage and power at small demo scale. |
| `cost_confidence` | High for design cash; Medium for effort; Low for hardware because the public receiver price observation is old. |
| `cost_assumptions` | Reuses the confirmed Mac, uses synthetic metadata or an explicitly approved recording, and treats hardware as optional and unowned. |
| `cost_exclusions` | Antenna mounting, travel, weatherproofing, specialist antennas, tax, shipping, live capture, private signals, paid satellite data, and replacement parts. |
| `cost_source_urls` | https://github.com/SatDump/SatDump ; https://www.rtl-sdr.com/rtl-sdr-blog-v4-dongle-initial-release/ |
| `source_last_checked` | 2026-07-20 |
| `price_valid_until` | 2026-07-27 |
| `refresh_reason` | Refresh hardware within seven days because the receiver price source is old; refresh software on a new release, license, binary, pipeline, or safety change. |
| `first_seen` | 2026-07-20 |
| `last_seen` | 2026-07-20 |
| `change_status` | `new` |
| `change_summary` | First radar appearance; source showed GPL-3.0, about 2k stars, offline processing, macOS builds, and latest visible tagged release 1.2.2 dated 2024-11-29. |
| `one_week_deliverable` | Plain-language weather-satellite pipeline explainer, storage worksheet, provenance schema, six safety cases, and output storyboard. |
| `success_criteria` | A reviewer can follow recording-to-output stages, estimate storage, identify permitted data provenance, and see explicit boundaries against transmission and private interception. |
| `demo_artifact` | Markdown explainer, synthetic metadata fixtures, storage calculator table, and static decoded-output mockups. |
| `prerequisites` | User confirmation of jurisdiction, receive-only intent, SDR inventory, and an approved public or synthetic recording source. |
| `first_three_tasks` | 1. Select one public weather-satellite pipeline at a metadata level. 2. Map recording, storage, decoding, and output stages. 3. Draft provenance, legal, privacy, and hardware review gates. |
| `blockers` | Current release freshness, binary provenance, exact Mac architecture, SDR inventory, approved recording, local receive rules, antenna scope, and storage need are unconfirmed. |
| `stop_conditions` | Stop for encrypted or private signals, transmission, unsafe antenna work, unapproved recordings, unclear legal status, stale unverified binaries, or hidden network dependence. |
| `safety_notes` | Synthetic or explicitly approved offline data only; no reception, transmission, interception, antenna work, bias power, package, binary, or repository execution is approved. |

## Approval Gate

No item is approved for registry entry, download, installation, execution,
purchase, benchmark, radio activity, flight activity, or dashboard decision.
The next approval task is a static `llama-swap` provider-boundary and threat-model
review. Lemma remains `needs_more_info` and is not ready for evaluation.

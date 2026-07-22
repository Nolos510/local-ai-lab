# AI Lab Radar Daily External Source Packet

Packet title: 2026-07-22 Daily External Radar
Packet date: 2026-07-22
Prepared by: Codex automation
Approved for radar review: no
Safe to commit: no

## Scope

This metadata-only packet records a capped review of 35 public items: 20
Hugging Face model entries and 15 official project or documentation pages.
Five new project opportunities cleared the relevance, local-fit, freshness,
and risk threshold. No model candidate cleared the exact-artifact and
benchmark-gap threshold.

The scan did not clone repositories, download packages or models, install or
remove software, skills, plugins, Model Context Protocol servers, or
connectors, run code or models, call inference APIs, use credentials, or edit
either registry. Popularity is context only, not quality, trust, or approval.

## Source Set

All sources were accessed on 2026-07-22.

| # | Item | Type | Public source | Disposition note |
| --- | --- | --- | --- | --- |
| 1 | Inkling | model_candidate | https://huggingface.co/thinkingmachines/Inkling | Not shortlisted; source lists a roughly 952B multimodal model with no practical approved local artifact path. |
| 2 | Ternary-Bonsai-27B-gguf | model_candidate | https://huggingface.co/prism-ml/Ternary-Bonsai-27B-gguf | Not shortlisted; overlaps the previously reported Bonsai family and still depends on unusual low-bit runtime assumptions. |
| 3 | Unlimited-OCR | model_candidate | https://huggingface.co/baidu/Unlimited-OCR | Not shortlisted; optical character recognition task and custom execution path do not fit the current language-model benchmark. |
| 4 | Bonsai-27B-gguf | model_candidate | https://huggingface.co/prism-ml/Bonsai-27B-gguf | Not repeated; this family was already reported and no material artifact, license, runtime, or risk change was established. |
| 5 | GLM-5.2 | model_candidate | https://huggingface.co/zai-org/GLM-5.2 | Not shortlisted; source lists a 753B model and no practical reviewed local artifact. |
| 6 | Qwen3.6-27B Fable Fusion GGUF | model_candidate | https://huggingface.co/DavidAU/Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF | Not shortlisted; complex uncensored derivative provenance and benchmark overlap. |
| 7 | Qwythos-9B Claude Mythos GGUF | model_candidate | https://huggingface.co/empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF | Not shortlisted; third-party derivative and long-context claims lack a distinct benchmark priority. |
| 8 | Laguna-S-2.1 | model_candidate | https://huggingface.co/poolside/Laguna-S-2.1 | Not shortlisted; source lists 118B parameters but no reviewed GGUF or MLX artifact path. |
| 9 | OvisOCR2 | model_candidate | https://huggingface.co/ATH-MaaS/OvisOCR2 | Not shortlisted; custom vision-language execution and OCR evaluation are outside the current benchmark. |
| 10 | ThinkingCap-Qwen3.6-27B | model_candidate | https://huggingface.co/bottlecapai/ThinkingCap-Qwen3.6-27B | Not shortlisted; derivative provenance and no specific new benchmark gap. |
| 11 | Bonsai-27B-mlx-1bit | model_candidate | https://huggingface.co/prism-ml/Bonsai-27B-mlx-1bit | Not repeated; previously reported family with no established material change. |
| 12 | Kimi-K3 | model_candidate | https://huggingface.co/reteetzad/Kimi-K3 | Not shortlisted; artifact purpose, provenance, license, and local runtime path are insufficiently clear. |
| 13 | MiniCPM-RobotManip | model_candidate | https://huggingface.co/openbmb/MiniCPM-RobotManip | Not shortlisted; robotics manipulation needs custom runtime, datasets, hardware, and a separate safety evaluation lane. |
| 14 | Motif-3-Beta | model_candidate | https://huggingface.co/Motif-Technologies/Motif-3-Beta | Not shortlisted; source lists 315B parameters and no practical approved local artifact path. |
| 15 | Inkling-GGUF | model_candidate | https://huggingface.co/unsloth/inkling-GGUF | Not shortlisted; source lists a roughly 947B conversion with impractical artifact and memory burden. |
| 16 | MOSS-Transcribe-Diarize | model_candidate | https://huggingface.co/OpenMOSS-Team/MOSS-Transcribe-Diarize | Not shortlisted; speech and diarization are outside v0 scope and require separate privacy fixtures. |
| 17 | MiniCPM5 Claude Opus derivative | model_candidate | https://huggingface.co/GnLOLot/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-GGUF | Not shortlisted; derivative overlaps the previously reviewed MiniCPM5 family. |
| 18 | Hy3-GGUF | model_candidate | https://huggingface.co/AngelSlim/Hy3-GGUF | Not shortlisted; source lists about 295B parameters and no compelling local benchmark role. |
| 19 | Kimi-K2.7-Code | model_candidate | https://huggingface.co/moonshotai/Kimi-K2.7-Code | Not shortlisted; source lists roughly 1.1T parameters and no practical reviewed local artifact. |
| 20 | MiniCPM-RobotTrack | model_candidate | https://huggingface.co/openbmb/MiniCPM-RobotTrack | Not shortlisted; robotics tracking needs custom runtime, video fixtures, privacy review, and a separate benchmark lane. |
| 21 | OpenTelemetry Semantic Conventions | project_opportunity | https://github.com/open-telemetry/semantic-conventions | Shortlisted; a current standard offers a concrete trace-privacy and evidence vocabulary for AI Lab OS. |
| 22 | ToolHive | project_opportunity | https://github.com/stacklok/toolhive | Shortlisted; its July 20 release and registry/runtime separation make a useful static comparison for the reviewed Growth policy boundary. |
| 23 | Langfuse | project_opportunity | https://github.com/langfuse/langfuse | Shortlisted; mature trace and evaluation UX is a useful product reference despite a heavy self-hosted stack and telemetry concerns. |
| 24 | QGroundControl | project_opportunity | https://github.com/mavlink/qgroundcontrol | Shortlisted; an offline flight-review storyboard offers a clear drone portfolio artifact without flight or vehicle control. |
| 25 | Reachy Mini | project_opportunity | https://github.com/pollen-robotics/reachy_mini | Shortlisted; a priced desktop robot can become a strong local-first portfolio investment after purchase, privacy, and physical-safety review. |
| 26 | Model Context Protocol Inspector | project_opportunity | https://github.com/modelcontextprotocol/inspector | Not shortlisted; useful official reference but direct use connects to and exercises servers and overlaps yesterday's scanner review. |
| 27 | Microsoft MCP Gateway | project_opportunity | https://github.com/microsoft/mcp-gateway | Not shortlisted; Kubernetes, container registry, authorization, telemetry, and Azure paths are too broad for the current local-first MVP. |
| 28 | Opik | project_opportunity | https://github.com/comet-ml/opik | Not shortlisted; broad tracing, provider, optimizer, guardrail, and model-judge surface is heavier than the selected standards review. |
| 29 | Arize Phoenix | project_opportunity | https://github.com/Arize-ai/phoenix | Not repeated; previously reviewed and no material release, license, maintenance, price, or risk change was established. |
| 30 | Ragas | project_opportunity | https://github.com/vibrantlabsai/ragas | Not shortlisted; default provider and model-judge paths plus framework overlap reduce immediate value. |
| 31 | Open RAG Eval | project_opportunity | https://github.com/vectara/open-rag-eval | Not shortlisted; default model-judge key and corpus query-generation paths conflict with this metadata-only lane. |
| 32 | MAVSDK | project_opportunity | https://github.com/mavlink/MAVSDK | Not shortlisted; current and relevant, but its live vehicle-control API has a higher authority boundary than the QGroundControl storyboard. |
| 33 | Open-RMF | project_opportunity | https://github.com/open-rmf/rmf | Not shortlisted; multi-fleet Robot Operating System 2 dependencies and Ubuntu-first setup are too broad for this Mac-local MVP. |
| 34 | Aerostack2 | project_opportunity | https://github.com/aerostack2/aerostack2 | Not shortlisted; autonomous multi-drone and Robot Operating System 2 scope requires simulation and control gates beyond this report. |
| 35 | RViz | project_opportunity | https://github.com/ros2/rviz | Not shortlisted; useful Robot Operating System 2 viewer but less focused than the selected offline flight-review artifact. |

## Supplemental Source Notes

| Project | Public metadata observed | Relevance and caution |
| --- | --- | --- |
| OpenTelemetry Semantic Conventions | Apache-2.0; about 582 stars and 361 forks; v1.41.1 shown for 2026-05-11. | Generative AI conventions cover retrieval, tools, evaluation, streaming, and privacy-sensitive content. Many fields remain evolving and content capture can expose prompts or tool data. |
| ToolHive | Apache-2.0; about 2,000 stars and 254 forks; v0.40.1 shown for 2026-07-20. | Separates gateway, registry, runtime, and portal concepts. Upstream can install, build, run, proxy, authenticate, and observe servers; none of those actions are approved here. |
| Langfuse | MIT except enterprise folders; about 29,100 stars and 3,000 forks; v3.185.0 shown for 2026-06-12. | Self-hosting uses web and worker containers plus PostgreSQL, ClickHouse, Redis or Valkey, and object storage. Open-source telemetry is enabled unless disabled and sends aggregated deployment information. |
| QGroundControl | Apache-2.0 and GPL-3.0 files; about 4,800 stars and 4,900 forks; v5.0.8 shown for 2025-10-09. | Supports mission planning, vehicle setup, telemetry, video, and control. The proposed AI Lab artifact is an offline synthetic review design only. |
| Reachy Mini | Apache-2.0 software and separate non-commercial hardware terms; about 1,200 stars and 237 forks; v1.7.3 shown for 2026-05-13. | Official pages show a Lite kit using external compute and a wireless kit with onboard compute. Camera, microphones, motors, app installation, and model integrations require separate review. |

Adoption figures are approximate source-page observations and are not scores,
trust signals, registry decisions, or installation authority.

## Highest-Signal Items

### project_opportunity: OpenTelemetry GenAI trace privacy map

| Field | Value |
| --- | --- |
| `project_id` | `20260722-opentelemetry-genai-privacy-map` |
| `project_name` | OpenTelemetry GenAI trace privacy map |
| `source_url` | https://github.com/open-telemetry/semantic-conventions |
| `item_type` | `project_opportunity` |
| `priority_score` | 5 |
| `priority_rationale` | The current standard directly addresses retrieval, tools, evaluation events, streaming, and sensitive-content capture, which maps to AI Lab's evidence and privacy rules without requiring a new runtime. |
| `plain_language_summary` | OpenTelemetry Semantic Conventions provide shared names for recording what software did, how long it took, and what failed. Its generative AI section proposes consistent fields for model requests, retrieval, tools, agents, and evaluations. |
| `problem_it_solves` | Traces become difficult to compare or protect when every application records different field names or mixes safe operational facts with private prompts and tool data. |
| `who_it_is_for` | Developers, observability teams, security reviewers, and product teams designing repeatable AI evidence. |
| `common_use_cases` | Naming model and retrieval operations; recording latency and token counts; tracing tool calls; representing evaluation events; documenting which content fields are disabled. |
| `how_it_works_in_practice` | An application emits structured events using agreed field names. A trace viewer can then group related operations, compare timings, and apply privacy rules consistently. |
| `ai_lab_use_case` | Create a static map from current AI Lab benchmark and RAG evidence to 20 standard fields, with allow, redact, local-only, and prohibit labels. No telemetry would be emitted. |
| `limitations` | The generative AI conventions are still evolving, consistent names do not guarantee safe collection, and prompt, tool, exception, or file fields can contain private content. |
| `why_interesting` | It could give the benchmark, RAG harness, and dashboard a shared evidence vocabulary while making privacy defaults explicit. |
| `business_tie_in` | A trace privacy map is a credible governance and observability artifact for private-AI client work. |
| `learning_value` | High: distributed traces, evidence schemas, sensitive-content controls, retrieval spans, tool-call boundaries, and evaluation provenance. |
| `local_fit` | High for a dependency-free documentation exercise; implementation would require a separate architecture and logging review. |
| `risk_notes` | Standard fields may capture prompts, tool definitions, tool arguments, results, files, exception messages, server addresses, or identifiers. The standard is not a privacy policy. |
| `recommended_next_step` | `ready_for_review`: approve a static 20-field privacy and evidence crosswalk only. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-22 |
| `cost_scope` | Documentation-only field map, four privacy dispositions, three synthetic traces, and a static dashboard evidence card on confirmed lab compute. |
| `incremental_cost` | $0 project-specific cash using confirmed lab compute. |
| `from_scratch_cost` | $0-$25 when a general-purpose computer and text editor are available. |
| `portfolio_build_cost` | $0-$100 for polished diagrams, synthetic traces, and a narrated governance walkthrough. |
| `diy_effort_hours` | 8-14 hours. |
| `recurring_monthly_cost` | $0 for the defined static local scope. |
| `cost_confidence` | High for cash; Medium for effort because field-level policy choices need owner review. |
| `cost_assumptions` | Reuses the confirmed Mac and existing specifications; all trace examples are synthetic and contain no prompts or private paths. |
| `cost_exclusions` | Instrumentation libraries, telemetry collectors, servers, data export, implementation, private traces, dependencies, hosted observability, and paid design tools. |
| `cost_source_urls` | https://github.com/open-telemetry/semantic-conventions and https://github.com/open-telemetry/semantic-conventions/releases |
| `source_last_checked` | 2026-07-22 |
| `price_valid_until` | 2026-08-21 |
| `refresh_reason` | Refresh if generative AI field stability, sensitive-content guidance, evaluation events, retrieval spans, tool-call fields, license, or release status changes. |
| `first_seen` | 2026-07-22 |
| `last_seen` | 2026-07-22 |
| `change_status` | `new` |
| `change_summary` | First radar appearance of the dedicated semantic-conventions project as a trace-privacy mapping opportunity. |
| `one_week_deliverable` | A 20-field crosswalk with allow, redact, local-only, and prohibit dispositions plus three synthetic trace examples. |
| `success_criteria` | Every mapped field has a purpose, source, privacy disposition, retention note, and explicit rule preventing prompts, retrieved chunks, secrets, or private paths from entering default logs. |
| `demo_artifact` | Markdown field map and static dashboard evidence-card mockup. |
| `prerequisites` | User approval for a documentation-only review and selection of three synthetic workflow shapes. |
| `first_three_tasks` | 1. Inventory current benchmark and RAG evidence fields. 2. Map 20 standard fields and four privacy dispositions. 3. Draft three synthetic traces and the static evidence card. |
| `blockers` | Retention expectations, field ownership, and whether a later implementation needs an architecture decision record require confirmation. |
| `stop_conditions` | Stop if progress requires adding instrumentation, collecting a real trace, logging prompts or chunks, exporting telemetry, adding a dependency, or changing runtime behavior. |
| `safety_notes` | Static synthetic documentation only; no telemetry, prompt, chunk, tool result, private path, collector, exporter, server, package, or execution is approved. |

### project_opportunity: ToolHive MCP trust-policy crosswalk

| Field | Value |
| --- | --- |
| `project_id` | `20260722-toolhive-mcp-trust-crosswalk` |
| `project_name` | ToolHive MCP trust-policy crosswalk |
| `source_url` | https://github.com/stacklok/toolhive |
| `item_type` | `project_opportunity` |
| `priority_score` | 5 |
| `priority_rationale` | ToolHive's separation of registry, runtime, gateway, and portal concepts is directly relevant to the repository's newly explicit Growth installation authority, while its current release makes the comparison timely. |
| `plain_language_summary` | ToolHive is a platform for cataloging, approving, running, and controlling Model Context Protocol servers. These servers let AI assistants use external tools, so ToolHive adds registries, isolation, permissions, gateways, and audit records around them. |
| `problem_it_solves` | Teams need a way to distinguish finding a tool from trusting it, and to control what an approved tool can access or do after deployment. |
| `who_it_is_for` | AI platform teams, security engineers, administrators, and developers managing many tool integrations. |
| `common_use_cases` | Curating a server catalog; checking provenance; assigning permissions; isolating servers; auditing access; exposing approved tools through a gateway. |
| `how_it_works_in_practice` | The upstream platform can discover catalog entries, verify metadata, install or launch servers, proxy connections, enforce policies, store secrets, and export operational records. |
| `ai_lab_use_case` | Compare ToolHive's four layers with AI Lab's discovery inbox, reviewed Growth policy, official-host command allowlist, rollback evidence, and no-install radar boundary. No ToolHive component or catalog entry would run. |
| `limitations` | A platform does not make catalog entries trustworthy by itself. Upstream paths include containers, package managers, remote servers, credentials, cloud interfaces, Kubernetes, and one-click installation. |
| `why_interesting` | It provides a concrete external architecture for testing whether AI Lab's discovery, approval, execution, and rollback boundaries are complete. |
| `business_tie_in` | A clear tool-governance architecture is useful for client automation intake and enterprise AI controls. |
| `learning_value` | High: supply-chain provenance, policy separation, runtime isolation, secrets, auditability, rollback, and gateway authority. |
| `local_fit` | High for a static policy comparison; direct use conflicts with radar authority and needs a separate reviewed Growth decision. |
| `risk_notes` | Upstream can build from package managers, run containers, proxy remote servers, manage secrets, install servers, connect AI clients, and use Kubernetes or cloud interfaces. Catalog presence and popularity do not grant trust. |
| `recommended_next_step` | `ready_for_review`: approve a static four-layer trust-policy crosswalk only; no Growth or installation authority is granted. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-22 |
| `cost_scope` | Documentation-only architecture comparison, authority matrix, rollback checklist, and synthetic server-review record on confirmed lab compute. |
| `incremental_cost` | $0 project-specific cash using confirmed lab compute. |
| `from_scratch_cost` | $0-$25 when a general-purpose computer and text editor are available. |
| `portfolio_build_cost` | $0-$100 for polished diagrams, synthetic policy records, and a narrated governance walkthrough. |
| `diy_effort_hours` | 10-18 hours. |
| `recurring_monthly_cost` | $0 for the defined static local scope. |
| `cost_confidence` | High for cash; Medium for effort because the comparison spans radar and Growth ownership boundaries. |
| `cost_assumptions` | Reuses confirmed lab compute and public metadata; all servers, manifests, commands, and rollback records are synthetic. |
| `cost_exclusions` | ToolHive, containers, packages, registries, servers, plugins, skills, connectors, credentials, gateways, Kubernetes, cloud services, installation, execution, and paid support. |
| `cost_source_urls` | https://github.com/stacklok/toolhive and https://github.com/stacklok/toolhive/releases |
| `source_last_checked` | 2026-07-22 |
| `price_valid_until` | 2026-08-21 |
| `refresh_reason` | Refresh if registry provenance, skill schema, package behavior, gateway policy, rollback, telemetry, license, release, or Growth authority rules materially change. |
| `first_seen` | 2026-07-22 |
| `last_seen` | 2026-07-22 |
| `change_status` | `new` |
| `change_summary` | First radar appearance; v0.40.1 dated 2026-07-20 exposes current registry, skill-schema, authorization, audit, and runtime concepts relevant to the local policy boundary. |
| `one_week_deliverable` | Four-layer architecture crosswalk, authority matrix, immutable-source checklist, rollback evidence checklist, and one synthetic server-review record. |
| `success_criteria` | Reviewers can distinguish discovery from approval, policy from inventory, official-host execution from forbidden fallbacks, and qualification evidence from installation authority. |
| `demo_artifact` | Markdown policy map and static approval-flow diagram using synthetic entries. |
| `prerequisites` | User approval for documentation only and confirmation that Growth policy remains the sole installation authority. |
| `first_three_tasks` | 1. Map registry, runtime, gateway, and portal concepts. 2. Compare each concept with radar and Growth authority rules. 3. Draft synthetic approval and rollback evidence records. |
| `blockers` | Ownership between radar and Growth documentation and the future location of the crosswalk need confirmation. |
| `stop_conditions` | Stop if progress requires installing ToolHive, reading host inventory, adding or removing a skill, plugin, server, or connector, running a package manager, starting a container, using credentials, or changing Growth policy. |
| `safety_notes` | Static public-metadata review only; radar grants no installation, removal, enablement, disablement, inventory, server, plugin, skill, connector, package, container, credential, gateway, or execution authority. |

### project_opportunity: Langfuse local observability architecture review

| Field | Value |
| --- | --- |
| `project_id` | `20260722-langfuse-local-observability-review` |
| `project_name` | Langfuse local observability architecture review |
| `source_url` | https://github.com/langfuse/langfuse |
| `item_type` | `project_opportunity` |
| `priority_score` | 3 |
| `priority_rationale` | Langfuse is a strong product reference for traces, datasets, evaluations, and prompts, but its storage stack, credentials, telemetry, retention, and enterprise boundaries are much broader than AI Lab's dependency-light dashboard. |
| `plain_language_summary` | Langfuse is a workspace for recording and reviewing what AI applications did. It organizes traces, prompts, datasets, quality checks, costs, and user feedback so teams can compare changes over time. |
| `problem_it_solves` | AI debugging and evaluation evidence becomes scattered when prompts, retrieved context, model calls, scores, and feedback live in different systems. |
| `who_it_is_for` | AI product teams, developers, quality reviewers, and operations teams managing production or experimental AI applications. |
| `common_use_cases` | Inspecting traces; comparing prompt versions; managing evaluation datasets; reviewing scores and feedback; monitoring costs and failures. |
| `how_it_works_in_practice` | Applications send structured events to a web and worker service. The self-hosted platform stores operational records across PostgreSQL, ClickHouse, Redis or Valkey, and object storage for review in a dashboard. |
| `ai_lab_use_case` | Produce a static architecture and feature-gap comparison, then sketch two smaller dashboard concepts that preserve local-only evidence and confirmed-score rules. No Langfuse service would run. |
| `limitations` | The self-hosted stack is operationally heavy, some features require model or provider connections, telemetry is enabled by default for open-source deployments, and data retention features vary by edition. |
| `why_interesting` | Its mature evidence workflow can reveal which small dashboard improvements would create the most value without adopting the full platform. |
| `business_tie_in` | Trace review and experiment evidence are useful for client RAG acceptance tests, incident reviews, and private-AI operations. |
| `learning_value` | High: event ingestion, trace UX, storage boundaries, retention, telemetry, data masking, and open-core licensing. |
| `local_fit` | Medium for direct use because of the multi-service stack; high as a static product and architecture reference. |
| `risk_notes` | Self-hosting uses multiple databases, object storage, credentials, migrations, containers, and optional external model APIs. Open-source telemetry sends aggregated usage and user-domain information unless disabled. Raw traces may contain prompts and private content. |
| `recommended_next_step` | `needs_more_info`: complete a static telemetry, retention, licensing, and minimum-stack review before approving even a dashboard concept. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-22 |
| `cost_scope` | Public-metadata architecture and feature comparison plus two static AI Lab dashboard concepts on confirmed lab compute. |
| `incremental_cost` | $0 project-specific cash using confirmed lab compute. |
| `from_scratch_cost` | $0-$25 when a general-purpose computer and design or presentation tool are available. |
| `portfolio_build_cost` | $0-$125 for polished architecture diagrams, two screen concepts, and a narrated product review. |
| `diy_effort_hours` | 12-20 hours. |
| `recurring_monthly_cost` | $0 for the defined public-metadata comparison. |
| `cost_confidence` | High for cash; Medium for effort because edition, telemetry, and storage boundaries are broad. |
| `cost_assumptions` | Reuses confirmed lab compute and public documentation; no service, database, trace, prompt, user record, or provider is used. |
| `cost_exclusions` | Containers, PostgreSQL, ClickHouse, Redis or Valkey, object storage, API keys, model providers, hosted service, private traces, installation, migration, implementation, and paid features. |
| `cost_source_urls` | https://github.com/langfuse/langfuse and https://langfuse.com/self-hosting and https://langfuse.com/self-hosting/security/telemetry |
| `source_last_checked` | 2026-07-22 |
| `price_valid_until` | 2026-08-21 |
| `refresh_reason` | Refresh if license, edition boundaries, telemetry defaults, retention, minimum infrastructure, release status, or self-hosting architecture materially changes. |
| `first_seen` | 2026-07-22 |
| `last_seen` | 2026-07-22 |
| `change_status` | `new` |
| `change_summary` | First radar appearance of Langfuse as a product and architecture reference, with current self-hosting and telemetry metadata. |
| `one_week_deliverable` | Architecture and feature-gap matrix, telemetry and retention review, and two static dashboard concepts. |
| `success_criteria` | Reviewers can identify the minimum useful features, excluded infrastructure, privacy differences, confirmed-score conflicts, and whether either screen concept belongs in the roadmap. |
| `demo_artifact` | Markdown architecture review and two static dashboard mockups. |
| `prerequisites` | User confirmation of the two AI Lab workflows to compare and approval for public-metadata design work only. |
| `first_three_tasks` | 1. Map Langfuse services, storage, telemetry, and edition boundaries. 2. Compare trace, dataset, prompt, and score workflows with AI Lab OS. 3. Draft two smaller local-first screen concepts. |
| `blockers` | Preferred dashboard workflows, retention requirements, portfolio budget, and maximum DIY hours are unconfirmed. |
| `stop_conditions` | Stop if progress requires running containers, creating credentials, connecting a provider, ingesting a trace, storing a prompt, enabling telemetry, adding dependencies, or changing dashboard code. |
| `safety_notes` | Static public-metadata design only; no service, database, container, credential, model, provider, telemetry, trace, prompt, private data, installation, migration, or execution is approved. |

### project_opportunity: QGroundControl offline flight-review storyboard

| Field | Value |
| --- | --- |
| `project_id` | `20260722-qgroundcontrol-offline-review` |
| `project_name` | QGroundControl offline flight-review storyboard |
| `source_url` | https://github.com/mavlink/qgroundcontrol |
| `item_type` | `project_opportunity` |
| `priority_score` | 3 |
| `priority_rationale` | QGroundControl is a widely adopted drone operations reference and can inspire a strong offline incident-review artifact, but its latest stable release is from 2025 and the full product has flight-control authority. |
| `plain_language_summary` | QGroundControl is an application for planning drone missions, configuring vehicles, watching live telemetry, viewing maps and video, and reviewing flight information. |
| `problem_it_solves` | Drone operations are difficult to understand when route plans, warnings, positions, battery readings, and operator actions are spread across separate screens or logs. |
| `who_it_is_for` | Drone pilots, field teams, developers, educators, and reviewers investigating mission or vehicle behavior. |
| `common_use_cases` | Planning routes; configuring a vehicle; monitoring battery and position; viewing camera feeds; reviewing telemetry and flight logs. |
| `how_it_works_in_practice` | The full application connects to a compatible vehicle or recording and presents maps, instruments, mission steps, parameters, alerts, and media in one control interface. |
| `ai_lab_use_case` | Create a static offline storyboard for one synthetic survey flight, covering preflight evidence, timeline, map, alert, battery, and after-action review. No application, drone, simulator, or log would run. |
| `limitations` | A storyboard cannot validate aircraft behavior. Real use involves safety-critical control, radio links, maps, logs, video, vehicle configuration, and platform-specific binaries. |
| `why_interesting` | It creates an understandable bridge from telemetry data to a resume-grade field-operations review workflow. |
| `business_tie_in` | After-action review concepts are relevant to inspection, mapping, public safety, construction, and field-service demonstrations. |
| `learning_value` | High: mission states, telemetry, human factors, alerts, provenance, uncertainty, and separation of review from control authority. |
| `local_fit` | High for a static synthetic artifact; direct macOS use and any simulator or vehicle path need separate review. |
| `risk_notes` | The upstream product can plan and control missions, tune parameters, connect vehicles, receive video, and access precise location logs. The current stable release date is 2025-10-09. |
| `recommended_next_step` | `ready_for_review`: approve a synthetic offline after-action storyboard only, with no flight, control, simulation, radio, map service, or log execution. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-22 |
| `cost_scope` | Static six-screen synthetic flight-review storyboard and evidence checklist on confirmed lab compute; no drone hardware required. |
| `incremental_cost` | $0 project-specific cash using confirmed lab compute. |
| `from_scratch_cost` | $0-$25 when a general-purpose computer and design or presentation tool are available. |
| `portfolio_build_cost` | $0-$125 for polished synthetic maps, telemetry charts, alerts, and a narrated after-action walkthrough. |
| `diy_effort_hours` | 10-18 hours. |
| `recurring_monthly_cost` | $0 for the defined offline static scope. |
| `cost_confidence` | High for cash; Medium for effort because the scenario and presentation depth need confirmation. |
| `cost_assumptions` | Reuses confirmed lab compute and wholly synthetic route, map, vehicle, and telemetry data. |
| `cost_exclusions` | QGroundControl binary, simulator, maps, drone, controller, radio, batteries, camera, real logs, flight, travel, insurance, certification, installation, and paid design assets. |
| `cost_source_urls` | https://github.com/mavlink/qgroundcontrol and https://github.com/mavlink/qgroundcontrol/releases |
| `source_last_checked` | 2026-07-22 |
| `price_valid_until` | 2026-08-21 |
| `refresh_reason` | Refresh if stable release, platform support, licensing, log handling, map services, telemetry, vehicle-control behavior, or maintenance status materially changes. |
| `first_seen` | 2026-07-22 |
| `last_seen` | 2026-07-22 |
| `change_status` | `new` |
| `change_summary` | First radar appearance of QGroundControl, narrowed to a static offline flight-review design because direct use has vehicle-control authority. |
| `one_week_deliverable` | Six-screen after-action storyboard with mission summary, map, timeline, battery, alert, evidence, and uncertainty views. |
| `success_criteria` | A non-technical reviewer can explain the planned route, observed synthetic event, evidence, operator decision, and unresolved uncertainty without implying a real flight occurred. |
| `demo_artifact` | Click-through static mockup or slide sequence with a narrated review. |
| `prerequisites` | User approval for static design and selection of one synthetic survey scenario. |
| `first_three_tasks` | 1. Define the synthetic mission and incident question. 2. Draft route, timeline, battery, alert, and evidence states. 3. Add uncertainty, provenance, and no-control labels. |
| `blockers` | Target industry, map style, presentation format, maximum DIY hours, and whether the artifact belongs in portfolio docs need confirmation. |
| `stop_conditions` | Stop if progress requires installing QGroundControl, downloading maps or logs, running a simulator, connecting a vehicle, using radio, planning a real mission, handling precise locations, or flying. |
| `safety_notes` | Static synthetic review only; no application, map service, log, simulator, drone, controller, radio, video, telemetry, mission, flight, or control activity is approved. |

### project_opportunity: Reachy Mini local interaction portfolio build

| Field | Value |
| --- | --- |
| `project_id` | `20260722-reachy-mini-local-portfolio` |
| `project_name` | Reachy Mini local interaction portfolio build |
| `source_url` | https://github.com/pollen-robotics/reachy_mini |
| `item_type` | `project_opportunity` |
| `priority_score` | 4 |
| `priority_rationale` | Reachy Mini is an unusually understandable open desktop robot with a Mac-powered Lite option and visible current pricing, but hardware purchase, camera and microphone privacy, physical motion, app installation, and model paths require separate gates. |
| `plain_language_summary` | Reachy Mini is a small expressive desktop robot with moving head parts, a camera, microphones, and a speaker. The Lite version uses an external Mac or Linux computer, while the wireless version includes onboard compute. |
| `problem_it_solves` | Software-only AI demos do not show how people understand motion, attention, timing, sound, and physical presence during an interaction. |
| `who_it_is_for` | Robotics learners, educators, human-computer interaction researchers, AI demo builders, and portfolio developers. |
| `common_use_cases` | Learning robot motion; prototyping expressive interfaces; testing local vision or audio concepts; demonstrating human-robot interaction; building educational apps. |
| `how_it_works_in_practice` | The full kit is assembled, connected to local compute, and controlled through software that can move motors and access camera, microphone, speaker, and optional AI applications. |
| `ai_lab_use_case` | First produce a no-purchase safety and interaction design for a local, typed-command, motion-only demo. If separately approved later, the Lite kit would reuse the confirmed Mac and keep camera, microphones, app store, and model integrations disabled for the first acceptance test. |
| `limitations` | It has no arms or locomotion, is sold as a kit, requires assembly, and introduces moving hardware plus camera and microphone privacy. Apps and AI integrations can add downloads, credentials, cloud calls, and broader authority. |
| `why_interesting` | It could become a distinctive physical portfolio project while still supporting a staged, local-first acceptance plan. |
| `business_tie_in` | Expressive robot demos can support education, retail, reception, accessibility, exhibit, and human-interface concept work. |
| `learning_value` | High: physical safety, motion design, local device control, privacy, human factors, staged acceptance, and hardware-software boundaries. |
| `local_fit` | The Lite version can reuse confirmed Mac compute, but no owned unit is confirmed and all installation, device, model, and media paths remain unreviewed. |
| `risk_notes` | Motors can move unexpectedly; camera and microphones can collect personal data; upstream includes one-click apps, Hugging Face integrations, model downloads, notebooks, and agent prompts. Hardware terms differ from the Apache-2.0 software license. |
| `recommended_next_step` | `needs_more_info`: confirm budget, regional price, lead time, workspace, privacy policy, and physical acceptance limits before any purchase or implementation decision. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-22 |
| `cost_scope` | Planning week is $0; later smallest physical MVP uses a Reachy Mini Lite kit, confirmed Mac compute, motion-only typed commands, and basic workspace protection after separate approvals. |
| `incremental_cost` | $0 for the planning week; $399-$499 for a later kit based on current official US pricing, before shipping and tax. |
| `from_scratch_cost` | $425-$575 for kit plus basic workspace protection and cable management; shipping, tax, and regional import costs remain unresolved. |
| `portfolio_build_cost` | $475-$700 for kit, protected demo surface, transport or storage, simple presentation materials, and contingency. |
| `diy_effort_hours` | 16-30 hours including design, source and license review, source-declared 2-3 hour assembly, safety acceptance, and portfolio documentation. |
| `recurring_monthly_cost` | $0 for a local motion-only demo; electricity and optional services are excluded. |
| `cost_confidence` | Medium because official regional pages show different currencies or prices and shipping, tax, lead time, and owned accessories are unconfirmed. |
| `cost_assumptions` | Uses the Lite kit with the confirmed Mac, a stable indoor desk, typed local commands, and no camera, microphone, model, app-store, or cloud feature in the first physical acceptance. |
| `cost_exclusions` | Shipping, tax, duties, replacement parts, tools already owned, models, apps, subscriptions, cloud services, camera or audio use, insurance, installation, and professional safety certification. |
| `cost_source_urls` | https://github.com/pollen-robotics/reachy_mini and https://reachy-mini.ai/ and https://store.pollen-robotics.com/ |
| `source_last_checked` | 2026-07-22 |
| `price_valid_until` | 2026-08-05 |
| `refresh_reason` | Refresh within 14 days because regional pricing, currency, stock, shipping, lead time, kit contents, hardware terms, and compatibility can change. |
| `first_seen` | 2026-07-22 |
| `last_seen` | 2026-07-22 |
| `change_status` | `new` |
| `change_summary` | First radar appearance with official SDK metadata, current regional price pages, a Mac-powered Lite path, and explicit app, media, motion, and license risks. |
| `one_week_deliverable` | No-purchase decision packet with interaction storyboard, workspace plan, privacy states, motion limits, acceptance checklist, refreshed landed-cost worksheet, and go or no-go recommendation. |
| `success_criteria` | The packet identifies exact kit and regional price, workspace and supervision needs, motion limits, camera and microphone defaults, rollback or power-off steps, excluded app and model paths, and a budget decision. |
| `demo_artifact` | Static interaction storyboard, tabletop layout, motion-safety checklist, and priced decision sheet; no physical robot is required. |
| `prerequisites` | Confirm portfolio budget, maximum DIY hours, region, shipping destination category without storing an address, available tools, tabletop space, and comfort with a camera and microphone device. |
| `first_three_tasks` | 1. Refresh official regional kit price, contents, terms, and lead time without entering a cart. 2. Draft motion-only interaction and physical acceptance limits. 3. Complete privacy, workspace, cost, and go or no-go review. |
| `blockers` | Portfolio budget, maximum DIY hours, owned tools, region, shipping and tax, workspace, supervision, camera and microphone policy, and exact kit terms are unconfirmed. |
| `stop_conditions` | Stop before entering a cart, submitting personal data, purchasing, installing software or apps, enabling a skill or connector, downloading a model, connecting hardware, energizing motors, using camera or microphones, or accepting unresolved terms. |
| `safety_notes` | Planning only; no cart, personal data, purchase, shipment, assembly, power, motion, camera, microphone, app, skill, plugin, connector, model, installation, download, cloud call, credential, or device control is approved. |

## Reviewer Notes

- No model candidate is `ready_for_eval`; no benchmark task was created.
- All five projects are candidate-only planning records. ToolHive discovery and
  review do not grant Growth installation or inventory authority.
- The confirmed lab host supports $0 design MVPs. Edge and robotics inventory,
  maximum DIY hours, and portfolio budget remain unconfirmed.

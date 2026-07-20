# AI Lab Radar Source Packet

Packet title: Daily External Radar Metadata Scan
Packet date: 2026-07-18
Prepared by: Codex automation
Approved for radar review: no
Safe to commit: no

## Scope

Daily External Radar ran because no new user-approved Local Radar source packet
was found under `automations/ai-lab-radar/inputs`.

This packet is public metadata only. It does not approve registry entry,
downloads, installs, model execution, repository execution, benchmark scoring,
dashboard import, or final decisions.

Source access date: 2026-07-18.

## Reviewed Source Set

The scan reviewed these public metadata items and de-duped obvious matches
against `data/model_registry/candidates.csv`,
`data/project_registry/github_repos.csv`, and prior radar reports.

| # | Item | Type | Source URL | Scan note |
| --- | --- | --- | --- | --- |
| 1 | Qwen3-Coder-Next-GGUF | model_candidate | https://huggingface.co/unsloth/Qwen3-Coder-Next-GGUF | New high-end coding-agent GGUF candidate; related to existing Qwen lane but not the same registry row. |
| 2 | Qwopus3.6-27B-Coder-MTP-4bit.mlx | model_candidate | https://huggingface.co/jedisct1/Qwopus3.6-27B-Coder-MTP-4bit.mlx | MLX coding-agent artifact with local validation claims and tool-call template notes. |
| 3 | Phi-4-Reasoning-Vision-15B | model_candidate | https://huggingface.co/microsoft/Phi-4-reasoning-vision-15B | Official multimodal reasoning model; text-first harness scope remains a blocker. |
| 4 | Qwen/Qwen3-Coder-30B-A3B-Instruct | model_candidate | https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct | Already covered by local Qwen registry lineage; de-duped. |
| 5 | DeepSeek-R1-0528-Qwen3-8B | model_candidate | https://huggingface.co/deepseek-ai/DeepSeek-R1-0528-Qwen3-8B | Already represented in model registry; de-duped. |
| 6 | Qwen3-8B-Abliterated-GGUF | model_candidate | https://huggingface.co/bartowski/mlabonne_Qwen3-8B-abliterated-GGUF | Already represented in model registry; de-duped. |
| 7 | Dolphin3.0-Llama3.1-8B-GGUF | model_candidate | https://huggingface.co/dphn/Dolphin3.0-Llama3.1-8B-GGUF | Already represented in model registry; de-duped. |
| 8 | Future AGI | project_opportunity | https://github.com/future-agi/future-agi | Self-hostable eval/observability platform for agents; relevant to draft-vs-confirmed scoring. |
| 9 | Future AGI self-hosting docs | project_opportunity | https://docs.futureagi.com/docs/self-hosting/ | Self-hosting metadata says traces, datasets, evals, and model calls stay inside the user's network. |
| 10 | mcp-agent | project_opportunity | https://github.com/lastmile-ai/mcp-agent | MCP workflow framework; relevant to agent/eval lanes without entering RAG runtime v0. |
| 11 | Microsoft Agent Framework | project_opportunity | https://learn.microsoft.com/en-us/agent-framework/overview/ | Successor path for AutoGen/Semantic Kernel; useful reference, but cloud/provider assumptions need review. |
| 12 | Mastra | project_opportunity | https://github.com/mastra-ai/mastra | TypeScript agent framework with evals/observability; product reference, heavier than current stack. |
| 13 | Claude Context Local | project_opportunity | https://github.com/FarhanAliRaza/claude-context-local | Local semantic code search MCP; stronger local-first posture than cloud embedding defaults. |
| 14 | Neuledge Context | project_opportunity | https://github.com/neuledge/context | Local-first docs MCP with package registry; package-fetch behavior requires approval review. |
| 15 | dltHub AI Workbench | project_opportunity | https://github.com/dlt-hub/dlthub-ai-workbench | Agent workflow/toolkit pattern for data pipelines; useful business automation reference. |
| 16 | Raspberry Pi AI Camera docs | project_opportunity | https://www.raspberrypi.com/documentation/accessories/ai-camera.html | Official edge AI camera docs for IMX500; relevant to local field-system prototypes. |
| 17 | Raspberry Pi IMX500 model zoo | project_opportunity | https://github.com/raspberrypi/imx500-models | Official model zoo metadata for AI Camera tasks. |
| 18 | rtl_433 | project_opportunity | https://github.com/merbanan/rtl_433 | Passive ISM-band receiver metadata; useful SDR learning lane with legal/receive-only guardrails. |
| 19 | WildBridge | project_opportunity | https://github.com/WildDrone/WildBridge | DJI telemetry/control bridge; useful for drone telemetry learning with safety constraints. |
| 20 | RosettaDrone | project_opportunity | https://github.com/RosettaDrone/rosettadrone | MAVLink/H.264 bridge for DJI drones; useful reference but flight-control risk is high. |
| 21 | Raspberry Pi topic index | project_opportunity | https://github.com/topics/raspberry-pi | Broad edge-hardware discovery context only. |
| 22 | Embedded vision topic index | project_opportunity | https://github.com/topics/embedded-vision | Broad embedded-vision discovery context only. |
| 23 | GPS-denied topic index | project_opportunity | https://github.com/topics/gps-denied | Broad drone/robotics discovery context only; avoid operational claims. |
| 24 | evals topic index | project_opportunity | https://github.com/topics/evals | Broad eval-framework discovery context only. |

### Same-Day Follow-Up Source Set

The scheduled follow-up reviewed 27 additional public metadata items. It found
five worthwhile items not present in the morning packet, existing registries,
or prior radar reports. The remaining items were older, duplicate, lower-fit,
or carried a higher review burden than the reported shortlist.

| # | Item | Type | Source URL | Scan note |
| --- | --- | --- | --- | --- |
| 25 | Bonsai-27B-gguf | model_candidate | https://huggingface.co/prism-ml/Bonsai-27B-gguf | New compact 1-bit derivative with Metal claims; custom runtime forks are a major review gate. |
| 26 | SmolLM3-3B-GGUF | model_candidate | https://huggingface.co/ggml-org/SmolLM3-3B-GGUF | Official ggml-org GGUF with explicit Q4/Q8/F16 sizes and local runtime metadata. |
| 27 | Llama-3b-Code-Reasoning-GGUF | model_candidate | https://huggingface.co/mradermacher/Llama-3b-Code-Reasoning-GGUF | Mirror/quantization source and model provenance are less clear than SmolLM3; not shortlisted. |
| 28 | gemma-4-12b-coder MLX | model_candidate | https://huggingface.co/mlx-community/gemma-4-12b-coder-fable5-composer2.5-4bit | Model-card history and source-chain changes increase review burden; not shortlisted. |
| 29 | Mallow-A1-GGUF | model_candidate | https://huggingface.co/Maazwaheed/Mallow-A1-gguf | Small artifact metadata visible, but source/model purpose is weaker than shortlisted candidates. |
| 30 | Qwopus3.6 evaluation report | model_candidate | https://huggingface.co/spaces/Jackrong/qwopus36-eval | Supporting metadata for an item already reported this morning; de-duped. |
| 31 | Dagu | project_opportunity | https://github.com/dagucloud/dagu | Local-first file-backed workflow engine with recent release and explicit approval/retry concepts. |
| 32 | AiderDesk | project_opportunity | https://github.com/hotovo/aider-desk | Local-first coding workflow UI with worktrees and tool approval gates; recent release. |
| 33 | LocalAI | project_opportunity | https://github.com/mudler/LocalAI | Broad local inference control tower with Apple Silicon paths, but automatic model/backend features raise scope risk. |
| 34 | ToolJet | project_opportunity | https://github.com/ToolJet/ToolJet | Mature internal-tools platform; heavier stack and weaker direct lab fit than the shortlist. |
| 35 | Accomplish | project_opportunity | https://github.com/accomplish-ai/accomplish | Local-first desktop agent, but provider SDK/keychain and autonomous browser scope increase risk. |
| 36 | Routa | project_opportunity | https://github.com/phodal/routa | Multi-agent coordination reference; overlaps the v0 agent boundary and was not shortlisted. |
| 37 | OpenClaw Dashboard | project_opportunity | https://github.com/ChristianAlmurr/openclaw-dashboard | Local dashboard reference tied to an external agent stack; lower direct fit. |
| 38 | Skales | project_opportunity | https://github.com/skalesapp/skales | Desktop-agent reference with many provider paths and broad execution scope. |
| 39 | Raspberry Pi AI archive | project_opportunity | https://www.raspberrypi.com/news/category/raspberry-pi-products/raspberry-pi-ai/ | Official edge-AI discovery context; morning camera project already covers the strongest lane. |
| 40 | Raspberry Pi AI Camera launch | project_opportunity | https://www.raspberrypi.com/news/raspberry-pi-ai-camera-on-sale-now/ | Existing morning camera pricing/capability source; de-duped. |
| 41 | Raspberry Pi camera documentation | project_opportunity | https://www.raspberrypi.com/documentation/accessories/camera.html | Supporting camera metadata; no separate project delta. |
| 42 | Raspberry Pi camera software | project_opportunity | https://www.raspberrypi.com/documentation/computers/camera_software.html | Supporting software metadata; install/run guidance was not used. |
| 43 | Raspberry Pi Smart Display Module | project_opportunity | https://www.raspberrypi.com/news/raspberry-pi-smart-display-module-coming-soon/ | Edge-signage concept remains pre-release and lacks current pricing. |
| 44 | PX4-Autopilot | project_opportunity | https://github.com/PX4/PX4-Autopilot | Stable robotics reference; no material change since the morning drone scan. |
| 45 | PX4 ROS 2 messages | project_opportunity | https://github.com/PX4/px4_msgs | Useful compatibility reference, but not a standalone project opportunity today. |
| 46 | PX4 repository index | project_opportunity | https://github.com/orgs/PX4/repositories | Broad organization metadata only. |
| 47 | Raspberry Pi AI Magazine overview | project_opportunity | https://magazine.raspberrypi.com/articles/putting-ai-to-use | Editorial context; no stronger metadata than official product/docs sources. |
| 48 | Raspberry Pi AI Camera product brief | project_opportunity | https://datasheets.raspberrypi.com/camera/ai-camera-product-brief.pdf | Existing camera project support only. |
| 49 | Hugging Face GGUF documentation | model_candidate | https://huggingface.co/docs/hub/main/gguf | Format reference, not a candidate. |
| 50 | Experiential Plasticity paper artifact | model_candidate | https://huggingface.co/continuum-ai/experiential-plasticity-paper | Research context lacks a directly approved local artifact path. |
| 51 | NIST GAI response artifact | project_opportunity | https://huggingface.co/datasets/huggingface/policy-docs | General policy/security context, not a project opportunity. |

### Supplemental Cost Sources

These public pages were reviewed after the discovery scan to price concrete,
safe local MVPs. Prices are observations as of 2026-07-18, not purchase
recommendations or checkout approval.

| Project | Cost source | Pricing or sizing evidence |
| --- | --- | --- |
| Future AGI | https://docs.futureagi.com/docs/self-hosting/requirements/ | Official single-user trial minimum: 4 CPU cores, 8 GB RAM, and 20 GB disk. |
| Future AGI / mcp-agent | https://store.minisforum.com/en-ph/products/minisforum-un100p | Official-store observation: 16 GB RAM / 512 GB SSD mini PC at $219. |
| mcp-agent | https://github.com/lastmile-ai/mcp-agent | Apache-2.0 software; local-only prototype can reuse existing lab compute and model runtime. |
| rtl_433 | https://www.rtl-sdr.com/rtl-sdr-blog-v4-dongle-initial-release/ | Vendor observation: $29.95 dongle-only or $39.95 with antenna set. |
| Raspberry Pi AI Camera | https://www.raspberrypi.com/products/ai-camera/ | Official AI Camera MSRP: $70. |
| Raspberry Pi host | https://www.raspberrypi.com/news/more-memory-driven-price-rises/ | Official 2026 Raspberry Pi memory-tier pricing context. |
| WildBridge | https://github.com/WildDrone/WildBridge | Official project prerequisites and supported DJI/Android hardware classes. |
| WildBridge drone | https://store.dji.com/product/dji-mini-4-pro | Official-store observation: DJI Mini 4 Pro with standard controller at $759. |
| WildBridge Android host | https://store.google.com/config/pixel_9a?hl=en-US | Official-store observation: unlocked Pixel 9a 128 GB at $499. |
| Dagu | https://github.com/dagucloud/dagu | GPL-3.0 software with local single-server metadata; existing-lab design review has no software purchase price. |
| AiderDesk | https://github.com/hotovo/aider-desk | Apache-2.0 software; existing-lab design review has no software purchase price. |
| LocalAI | https://github.com/mudler/LocalAI | MIT software; existing-lab architecture review has no software purchase price. |

## Highest-Signal Items

### model_candidate: Qwen3-Coder-Next-GGUF

| Field | Value |
| --- | --- |
| `candidate_id` | `20260718-qwen3-coder-next-gguf` |
| `model_name` | Qwen3-Coder-Next-GGUF |
| `model_family` | Qwen |
| `provider_or_org` | Unsloth / Qwen metadata |
| `params_b` | 80 total, 3 activated claimed by source metadata |
| `format_or_runtime` | GGUF; local runtimes such as llama.cpp/LM Studio/Ollama require separate review |
| `claimed_context_window` | 262,144 native context claimed in source metadata |
| `license` | unknown in this scan; needs review |
| `source_url` | https://huggingface.co/unsloth/Qwen3-Coder-Next-GGUF |
| `public_adoption_signal` | Hugging Face page visible; adoption counts not captured in this scan |
| `discovered_at` | 2026-07-18 |
| `why_interesting` | Coding-agent-focused open-weight GGUF candidate that may better match repository-scale agent tasks than the current Qwen3-Coder local row. |
| `local_fit` | Strong theoretical fit for 256 GB unified memory if a specific artifact and runtime path are later approved. |
| `estimated_artifact_size` | unknown until an exact quantization file is selected; the source page exposes multiple GGUF variants. |
| `estimated_disk_requirement` | unknown until artifact selection; reserve artifact size plus runtime/cache overhead only after review. |
| `expected_memory_range` | unknown until quantization, context target, and runtime are selected. |
| `compatible_local_runtimes` | GGUF suggests llama.cpp, LM Studio, or Ollama paths, but compatibility is unverified in this metadata scan. |
| `benchmark_gap` | Exact artifact, license, hash, prompt template, context target, and approved local runner are missing before `evals/local-llm-benchmark/SPEC.md` can be used. |
| `risk_notes` | Large artifact; license, quantization source, checksums, prompt template, and exact runtime behavior are unreviewed. |
| `security_review_status` | `needs_review` |
| `download_approval` | `not_approved` |
| `license_review_status` | `needs_review` |
| `provenance_status` | `source_metadata_only` |
| `security_notes` | Metadata only. Do not download, install, run, or create local model IDs until a specific artifact/source/license/hash review is approved. |
| `isolation_notes` | If later approved, prefer an existing local runtime path that loads GGUF without executing upstream code. |
| `recommended_next_step` | `needs_more_info` |
| `proposed_eval` | After approval only: compare against the existing Qwen3-Coder raw-response lineage using `evals/local-llm-benchmark/SPEC.md` and `skills/local-llm-eval`. |
| `source_last_checked` | 2026-07-18 |
| `first_seen` | 2026-07-18 |
| `last_seen` | 2026-07-18 |
| `change_status` | `new` |
| `change_summary` | First radar appearance of this specific GGUF candidate. |

### model_candidate: Qwopus3.6-27B-Coder-MTP-4bit.mlx

| Field | Value |
| --- | --- |
| `candidate_id` | `20260718-qwopus36-27b-coder-mtp-mlx-4bit` |
| `model_name` | Qwopus3.6-27B-Coder-MTP-4bit.mlx |
| `model_family` | Qwen-derived / Qwopus |
| `provider_or_org` | jedisct1 packaging from Jackrong source metadata |
| `params_b` | source page displays mixed 27B naming and 5B params metadata; needs review |
| `format_or_runtime` | MLX 4-bit |
| `claimed_context_window` | unknown |
| `license` | unknown in this scan |
| `source_url` | https://huggingface.co/jedisct1/Qwopus3.6-27B-Coder-MTP-4bit.mlx |
| `public_adoption_signal` | Source page showed 463 downloads last month during scan. |
| `discovered_at` | 2026-07-18 |
| `why_interesting` | MLX coding-agent artifact with source claims about static artifact checks and tool-call smoke gates. |
| `local_fit` | Potential Apple Silicon fit because the artifact is MLX and source page lists 17 GB size metadata. |
| `estimated_artifact_size` | 17 GB, source-declared on the model page. |
| `estimated_disk_requirement` | Approximately 25 GB inferred planning allowance for the 17 GB artifact plus runtime/cache overhead. |
| `expected_memory_range` | unknown until the MLX runtime, context target, and MTP behavior are reviewed. |
| `compatible_local_runtimes` | MLX/MLX-LM is the expected path; exact command and template compatibility are unverified. |
| `benchmark_gap` | Publisher chain, license, file hashes, template patch, exact local command, and benchmark comparability review are missing. |
| `risk_notes` | Not an upstream official artifact; patched template and packaging chain need review before trust. |
| `security_review_status` | `needs_review` |
| `download_approval` | `not_approved` |
| `license_review_status` | `unknown` |
| `provenance_status` | `source_metadata_only` |
| `security_notes` | Metadata only. Confirm publisher chain, license, exact files, hashes, and whether custom template changes create benchmark comparability risk. |
| `isolation_notes` | If later approved, use MLX/MLX-LM only through a reviewed local command path and preserve raw evidence locally. |
| `recommended_next_step` | `watchlist` |
| `proposed_eval` | Approve source/security review first; only then consider local coding-agent prompt comparison. |
| `source_last_checked` | 2026-07-18 |
| `first_seen` | 2026-07-18 |
| `last_seen` | 2026-07-18 |
| `change_status` | `new` |
| `change_summary` | First radar appearance of this specific MLX artifact. |

### model_candidate: Phi-4-Reasoning-Vision-15B

| Field | Value |
| --- | --- |
| `candidate_id` | `20260718-phi4-reasoning-vision-15b` |
| `model_name` | Phi-4-Reasoning-Vision-15B |
| `model_family` | Phi |
| `provider_or_org` | Microsoft |
| `params_b` | 15 |
| `format_or_runtime` | Official Hugging Face model metadata; local GGUF/MLX path not selected |
| `claimed_context_window` | 16,384 tokens |
| `license` | MIT claimed on model card |
| `source_url` | https://huggingface.co/microsoft/Phi-4-reasoning-vision-15B |
| `public_adoption_signal` | Official Microsoft model card with release metadata; adoption count not captured in this scan. |
| `source_date` | 2026-03-04 |
| `discovered_at` | 2026-07-18 |
| `why_interesting` | Compact official multimodal reasoning model that could seed a future text-plus-vision evaluation lane. |
| `local_fit` | Good size for 256 GB memory, but the current benchmark is text-first and no reviewed local artifact path exists. |
| `estimated_artifact_size` | unknown; no exact local GGUF or MLX artifact was selected. |
| `estimated_disk_requirement` | unknown until a local artifact and runtime are selected. |
| `expected_memory_range` | unknown until precision, image/context workload, and local runtime are selected. |
| `compatible_local_runtimes` | Official Safetensors/Transformers metadata is visible; a dependency-light local MLX, GGUF, LM Studio, Ollama, or llama.cpp path is unverified. |
| `benchmark_gap` | The lab lacks a reviewed local artifact and a vision-specific benchmark lane with image fixtures and scoring rules. |
| `risk_notes` | Vision model scope, artifact format, runtime path, and benchmark methodology need separate review. |
| `security_review_status` | `needs_review` |
| `download_approval` | `not_approved` |
| `license_review_status` | `needs_review` |
| `provenance_status` | `source_metadata_only` |
| `security_notes` | Official source metadata only. Do not treat MIT claim or Microsoft source as local execution approval. |
| `isolation_notes` | Keep on watchlist until a retrieval/vision-specific eval lane exists. |
| `recommended_next_step` | `watchlist` |
| `proposed_eval` | Define a multimodal/vision benchmark lane before any local artifact approval. |
| `source_last_checked` | 2026-07-18 |
| `first_seen` | 2026-07-18 |
| `last_seen` | 2026-07-18 |
| `change_status` | `new` |
| `change_summary` | First radar appearance of this official multimodal model candidate. |

### project_opportunity: Future AGI

| Field | Value |
| --- | --- |
| `project_id` | `20260718-future-agi` |
| `project_name` | Future AGI |
| `source_url` | https://github.com/future-agi/future-agi |
| `item_type` | `project_opportunity` |
| `priority_score` | 4 |
| `priority_rationale` | Strong fit for AI Lab OS confirmed-score and observability gaps, but it is a full platform with cloud/gateway concepts that require boundary review. |
| `plain_language_summary` | Future AGI is a control center for checking how AI applications behave. It collects evidence about answers and workflows so people can see what went wrong and whether a change actually helped. |
| `problem_it_solves` | AI systems can fail in inconsistent ways, and teams often lack one place to trace failures, compare changes, and review quality checks. |
| `who_it_is_for` | Teams building AI assistants, automated workflows, or customer-facing AI features that need repeatable quality and safety review. |
| `common_use_cases` | Reviewing answer quality; tracing failed AI tasks; comparing prompt or model changes; monitoring safety checks; organizing test datasets. |
| `how_it_works_in_practice` | An AI application sends test or interaction records to the platform. Automated checks organize the evidence, a dashboard shows patterns and failures, and people review the results before accepting changes. |
| `ai_lab_use_case` | AI Lab would create a static comparison showing how Future AGI's review ideas map to the lab's draft-versus-confirmed score workflow, using mock records only. |
| `limitations` | It is a broad platform rather than a small library. Gateway, cloud, agent, and container features exceed the current lab scope, so the proposed work studies the review pattern without running the platform. |
| `public_adoption_signal` | GitHub org page showed 1.4k stars, Apache-2.0 license, and update activity on 2026-07-18. |
| `why_interesting` | The repo frames a single feedback loop for evaluations, tracing, simulations, guardrails, gateway, and optimization. |
| `business_tie_in` | Could inspire a client-facing "AI reliability workbench" or internal eval review workflow. |
| `learning_value` | Good reference for separating traces, evaluator records, guardrails, and score review. |
| `local_fit` | Self-hosting docs claim datasets, traces, evals, and model calls can stay inside the user's network. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-18 |
| `cost_scope` | Single-user local evaluation/observability stack using a local model endpoint and no paid cloud providers. |
| `incremental_cost` | $0-$25 cash on the existing Mac Studio; software is Apache-2.0 and the upper allowance covers incidental local storage or cabling. |
| `from_scratch_cost` | $220-$350 for a dedicated 16 GB / 512 GB x86 mini PC meeting the published 4-core / 8 GB / 20 GB minimum, plus tax or shipping allowance. |
| `portfolio_build_cost` | $300-$700 for a stronger dedicated host, backup storage, and basic power protection. |
| `diy_effort_hours` | 16-32 hours for boundary review, local configuration, one eval workflow, and a sanitized demo. |
| `recurring_monthly_cost` | $2-$6 for an always-on low-power host at an assumed $0.20-$0.40/kWh; $0 provider spend in the local-only scope. |
| `cost_confidence` | Medium. Official sizing and software license are explicit; dedicated-host and electricity totals are planning ranges. |
| `cost_assumptions` | Reuses the existing local model runtime; disables or reviews telemetry; no cloud model provider or paid support. |
| `cost_exclusions` | Model inference hardware already owned by the lab, commercial support, cloud APIs, labor valuation, and production redundancy. |
| `cost_source_urls` | https://docs.futureagi.com/docs/self-hosting/requirements/ ; https://github.com/future-agi/future-agi ; https://store.minisforum.com/en-ph/products/minisforum-un100p |
| `source_last_checked` | 2026-07-18 |
| `price_valid_until` | 2026-08-17 |
| `refresh_reason` | Initial discovery and baseline cost estimate; refresh after 30 days or a material release, license, maintenance, price, or risk change. |
| `first_seen` | 2026-07-18 |
| `last_seen` | 2026-07-18 |
| `change_status` | `new` |
| `change_summary` | First radar appearance with self-host sizing and a dedicated-host cost baseline. |
| `risk_notes` | Full-stack Docker platform, gateway behavior, SDKs, and possible cloud path are out of scope for direct dependency adoption. |
| `recommended_next_step` | `needs_more_info`: review docs for draft-score vs confirmed-score workflow patterns only. |
| `one_week_deliverable` | A no-install architecture comparison mapping Future AGI concepts to AI Lab OS draft/confirmed score review boundaries. |
| `success_criteria` | The brief identifies reusable concepts, rejected dependencies, data-flow boundaries, and one approval-sized follow-up task. |
| `demo_artifact` | Sanitized architecture comparison and mock evaluator-review flow in Markdown. |
| `prerequisites` | Approve a documentation-only review; confirm no platform installation, repository execution, or cloud-provider setup. |
| `first_three_tasks` | 1. Map public components to current AI Lab OS concepts. 2. Document local-first and confirmed-score gaps. 3. Draft the sanitized comparison and approval task. |
| `blockers` | Telemetry behavior, privileged container needs, x86/Rosetta assumptions, and the v0 agent boundary are unresolved. |
| `stop_conditions` | Stop if useful learning requires platform execution, credentials, privileged services, or direct adoption into the v0 runtime. |
| `safety_notes` | Metadata/design review only; no SDK, gateway, model-provider, telemetry, credential, or container execution is approved. |

### project_opportunity: mcp-agent

| Field | Value |
| --- | --- |
| `project_id` | `20260718-mcp-agent` |
| `project_name` | mcp-agent |
| `source_url` | https://github.com/lastmile-ai/mcp-agent |
| `item_type` | `project_opportunity` |
| `priority_score` | 4 |
| `priority_rationale` | Strong MCP workflow learning value, but AI Lab OS v0 forbids adding agent orchestration to the RAG runtime. |
| `plain_language_summary` | mcp-agent is a framework for building AI assistants that carry out several tool-based steps instead of answering a single question. MCP means Model Context Protocol, a standard way for an assistant to interact with approved tools. |
| `problem_it_solves` | Multi-step AI workflows become difficult to organize when they must remember progress, call several tools, pause for a person, and recover from failures. |
| `who_it_is_for` | Developers designing tool-using assistants, internal automations, and human-approved AI workflows. |
| `common_use_cases` | Research workflows; document processing; multi-step business tasks; tool coordination; workflows that pause for human approval. |
| `how_it_works_in_practice` | A developer defines a sequence of steps and allowed tools. The framework keeps track of progress, asks for human input where required, and resumes the workflow with the stored state. |
| `ai_lab_use_case` | AI Lab would write a no-install operating procedure for one fictional tool workflow and show its approvals and audit events with deterministic mock data. |
| `limitations` | It is not an AI model and does not make tools safe by itself. Real use requires tool/provider setup and agent execution, which remains outside the v0 RAG runtime. |
| `public_adoption_signal` | Public GitHub repo and discussions visible; star count not captured in this scan. |
| `why_interesting` | Provides MCP-centered workflow patterns, persistent state, and human input mechanics as a reference for future automation design. |
| `business_tie_in` | Useful for designing auditable client automations that coordinate tools without hiding provider assumptions. |
| `learning_value` | Good way to study MCP agent workflow structure without importing it. |
| `local_fit` | Can inform repo-local skills and automation SOPs while leaving runtime dependencies unchanged. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-18 |
| `cost_scope` | Separate local-only MCP workflow demo using deterministic fixtures or an existing local model runtime; no cloud provider and no RAG-runtime integration. |
| `incremental_cost` | $0-$25 cash on existing lab hardware; Apache-2.0 software has no purchase price. |
| `from_scratch_cost` | $220-$350 for a dedicated 16 GB / 512 GB mini PC if an isolated always-on demo host is desired. |
| `portfolio_build_cost` | $250-$500 for the dedicated host plus backup storage, basic power protection, and presentation accessories. |
| `diy_effort_hours` | 12-24 hours for one constrained workflow, audit logging, safety boundaries, tests, and demo documentation. |
| `recurring_monthly_cost` | $0 when run occasionally on the existing Mac; approximately $2-$6 for an always-on low-power host. |
| `cost_confidence` | Medium. Software/license cost is explicit; host and effort ranges depend on the selected workflow. |
| `cost_assumptions` | Uses an existing local runtime or deterministic provider and local MCP servers only. |
| `cost_exclusions` | Cloud inference, managed deployment, credentialed third-party connectors, labor valuation, and production support. |
| `cost_source_urls` | https://github.com/lastmile-ai/mcp-agent ; https://store.minisforum.com/en-ph/products/minisforum-un100p |
| `source_last_checked` | 2026-07-18 |
| `price_valid_until` | 2026-08-17 |
| `refresh_reason` | Initial discovery and local-only demo baseline; refresh after 30 days or a material release, license, maintenance, price, or risk change. |
| `first_seen` | 2026-07-18 |
| `last_seen` | 2026-07-18 |
| `change_status` | `new` |
| `change_summary` | First radar appearance with a constrained local-only workflow estimate. |
| `risk_notes` | Framework adoption could violate the no-agent-orchestration v0 runtime boundary if pulled into `src/local_ai_lab`. |
| `recommended_next_step` | `watchlist`: read architecture docs only; no dependency or runtime integration. |
| `one_week_deliverable` | A no-install MCP workflow SOP using deterministic mock steps and explicit human approval points. |
| `success_criteria` | The SOP defines one bounded workflow, audit events, failure handling, credential boundaries, and a post-v0 decision point. |
| `demo_artifact` | Sanitized sequence diagram and deterministic mock event transcript. |
| `prerequisites` | Approve a design-only review and keep all agent framework code outside `src/local_ai_lab`. |
| `first_three_tasks` | 1. Select one non-credentialed mock workflow. 2. Map state, approvals, and audit events. 3. Draft the SOP and mock transcript. |
| `blockers` | AI Lab OS v0 excludes agent orchestration; provider credentials and third-party connectors remain out of scope. |
| `stop_conditions` | Stop if the deliverable requires framework installation, cloud inference, credentials, or a v0 runtime dependency. |
| `safety_notes` | Design reference only; no framework import, tool execution, cloud call, secret, or MCP server installation is approved. |

### project_opportunity: Raspberry Pi AI Camera + IMX500 Model Zoo

| Field | Value |
| --- | --- |
| `project_id` | `20260718-raspberry-pi-ai-camera-imx500` |
| `project_name` | Raspberry Pi AI Camera + IMX500 Model Zoo |
| `source_url` | https://www.raspberrypi.com/documentation/accessories/ai-camera.html |
| `supporting_source_url` | https://github.com/raspberrypi/imx500-models |
| `item_type` | `project_opportunity` |
| `priority_score` | 5 |
| `priority_rationale` | Strong edge-hardware and portfolio fit, clear official docs, and a contained learning path if treated as metadata and design planning first. |
| `plain_language_summary` | The Raspberry Pi AI Camera is a camera with a small AI chip built into it. It can recognize objects, poses, or other visual patterns before sending compact results to a Raspberry Pi computer. |
| `problem_it_solves` | Ordinary camera projects often need a powerful computer or cloud service to analyze every image, which adds cost, delay, power use, and privacy concerns. |
| `who_it_is_for` | Hobbyists, students, educators, makers, and small teams building private low-power camera or field-sensor projects. |
| `common_use_cases` | Wildlife monitoring; counting approved objects; workshop or equipment status; offline field logging; educational computer-vision demonstrations. |
| `how_it_works_in_practice` | The camera captures an image, its Sony IMX500 chip runs a selected visual model, and the Raspberry Pi receives results such as labels or locations. The Pi can then save events or show them on a local dashboard. |
| `ai_lab_use_case` | AI Lab would plan one stock-model camera demo that writes privacy-safe event records to a small local dashboard, starting with synthetic events and a reviewed bill of materials. |
| `limitations` | Accuracy depends on lighting, camera placement, and the selected model. Model licenses and privacy must be reviewed, and the proposed demo excludes facial recognition, covert monitoring, and custom model training. |
| `public_adoption_signal` | Official Raspberry Pi documentation and official GitHub model zoo visible. |
| `why_interesting` | Enables local field-system prototypes around low-latency object detection, pose, and sensor workflows. |
| `business_tie_in` | Resume-grade demos: local wildlife monitor, workshop safety camera, inventory counter, or offline field logger. |
| `learning_value` | Teaches edge inference constraints, camera pipelines, sensor logging, and local dashboard ingestion. |
| `local_fit` | Good fit as an external hardware lane feeding AI Lab OS reports without touching model scores. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-18 |
| `cost_scope` | One stock-model AI Camera pipeline with local event logging and a small portfolio dashboard; no custom model training or cloud service. |
| `incremental_cost` | $80-$100 delivered when reusing a compatible Raspberry Pi, power supply, and storage. |
| `from_scratch_cost` | $155-$180 delivered for a minimum headless prototype using a Raspberry Pi 5 1GB, AI Camera, power supply, and microSD storage. |
| `portfolio_build_cost` | $195-$225 delivered for a Raspberry Pi 5 2GB build with cooling and basic case or camera mounting. |
| `diy_effort_hours` | 8-16 hours for assembly, one stock-model pipeline, event logging, and a small portfolio dashboard. |
| `recurring_monthly_cost` | $1-$3 for local power under an intermittent-to-always-on duty-cycle assumption; no cloud service is required. |
| `cost_confidence` | Medium. Camera, Pi, power-supply, and cooler prices are sourced; storage, enclosure, tax, and shipping are allowances. |
| `cost_assumptions` | Headless setup; existing keyboard/display not required; IMX500 inference runs on the camera, so no separate AI HAT is included. |
| `cost_exclusions` | Weatherproof enclosure, battery/UPS, custom fabrication, replacement parts, labor, tax by jurisdiction, and expedited shipping. |
| `cost_source_urls` | https://www.raspberrypi.com/products/ai-camera/ ; https://www.raspberrypi.com/news/more-memory-driven-price-rises/ ; https://www.pishop.us/product/raspberry-pi-5-2gb/ ; https://www.pishop.us/product/raspberry-pi-27w-usb-c-power-supply-black-us/ ; https://www.pishop.us/product/raspberry-pi-active-cooler/ |
| `source_last_checked` | 2026-07-18 |
| `price_valid_until` | 2026-08-17 |
| `refresh_reason` | Initial discovery and hardware BOM baseline; refresh after 30 days, inventory confirmation, or a material model-license, price, or compatibility change. |
| `first_seen` | 2026-07-18 |
| `last_seen` | 2026-07-18 |
| `change_status` | `new` |
| `change_summary` | First radar appearance with official camera metadata and three hardware cost scenarios. |
| `risk_notes` | Hardware/software setup is outside radar; no packages, models, or scripts are approved by this packet. |
| `recommended_next_step` | `ready_for_review`: draft a no-install project brief and dashboard schema for edge event logs. |
| `one_week_deliverable` | A no-install project brief, reviewed BOM, edge-event schema, and mock dashboard dataset for one stock-model use case. |
| `success_criteria` | The brief selects one use case and model license, distinguishes owned versus required hardware, and defines observable demo acceptance criteria. |
| `demo_artifact` | Sanitized mock event log plus a dashboard wireframe or static report using synthetic events. |
| `prerequisites` | Confirm owned Raspberry Pi/camera accessories, approve the project lane, and review the exact model-zoo license. |
| `first_three_tasks` | 1. Confirm inventory and select one stock-model use case. 2. Review the model license and define the event schema. 3. Draft the BOM, mock data, and demo acceptance brief. |
| `blockers` | Raspberry Pi inventory, deployment environment, privacy expectations, and exact model selection are unconfirmed. |
| `stop_conditions` | Stop if the selected model license is incompatible, required cash exceeds the approved tier, or the use case implies biometric surveillance. |
| `safety_notes` | No camera deployment, package/model download, facial recognition, biometric identification, covert monitoring, or purchase is approved. |

### project_opportunity: rtl_433

| Field | Value |
| --- | --- |
| `project_id` | `20260718-rtl-433` |
| `project_name` | rtl_433 |
| `source_url` | https://github.com/merbanan/rtl_433 |
| `item_type` | `project_opportunity` |
| `priority_score` | 4 |
| `priority_rationale` | Strong passive SDR learning fit with local sensor/dashboard tie-in, but legal/receive-only boundaries must be explicit. |
| `plain_language_summary` | rtl_433 turns radio messages from many common wireless sensors into readable event data. It listens through a software-defined radio receiver and does not need to transmit. |
| `problem_it_solves` | Weather stations and simple sensors often broadcast data in different radio formats, making it difficult to collect their readings in one local dashboard. |
| `who_it_is_for` | Radio hobbyists, students, facilities teams, and researchers studying approved unencrypted sensor broadcasts. |
| `common_use_cases` | Local weather readings; outdoor temperature sensors; approved equipment telemetry; home-lab environmental dashboards; radio-learning exercises. |
| `how_it_works_in_practice` | A small radio receiver hears nearby approved sensor broadcasts. rtl_433 recognizes supported message formats and converts them into ordinary event fields that another local tool can store or display. |
| `ai_lab_use_case` | AI Lab would first design a receive-only event format and dashboard using synthetic sensor messages, then separately review any live passive-reception proposal. |
| `limitations` | It does not transmit and cannot decode every device. Reception depends on frequency, antenna, location, and local law; protected communications, decryption, evasion, and private-activity monitoring are excluded. |
| `public_adoption_signal` | Official GitHub repo visible; adoption count not captured in this scan. |
| `why_interesting` | Generic receiver metadata for common ISM bands supports passive environmental and sensor logging projects. |
| `business_tie_in` | Could support local facilities monitoring, home-lab telemetry, or field data dashboards. |
| `learning_value` | Teaches SDR basics, signal metadata, decoders, and evidence logging. |
| `local_fit` | Strong local-first lane if limited to legal passive reception and sanitized sensor event summaries. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-18 |
| `cost_scope` | Legal passive receive-only sensor dashboard using one RTL-SDR receiver and antenna; no transmission or protected-communications targeting. |
| `incremental_cost` | $40-$80 using the existing Mac Studio, including a $39.95 receiver/antenna baseline plus tax, shipping, or a USB extension allowance. |
| `from_scratch_cost` | $125-$180 using a low-memory Raspberry Pi host, power supply, microSD storage, case, and the receiver/antenna set. |
| `portfolio_build_cost` | $175-$300 with a better antenna, enclosure, one test sensor, and mounting or cable-management allowance. |
| `diy_effort_hours` | 10-20 hours for receive-only scoping, sanitized event parsing, dashboard ingestion, tests, and legal/safety notes. |
| `recurring_monthly_cost` | $1-$3 for local power; no subscription is required in the scoped passive build. |
| `cost_confidence` | Medium. Receiver pricing is explicit; host, antenna upgrade, sensor, tax, and shipping are allowances. |
| `cost_assumptions` | Uses public unencrypted sensor broadcasts that are legal to receive in the deployment jurisdiction. |
| `cost_exclusions` | Specialized antennas, filters, outdoor mast work, premium sensors, labor valuation, and any licensing or legal consultation. |
| `cost_source_urls` | https://www.rtl-sdr.com/rtl-sdr-blog-v4-dongle-initial-release/ ; https://www.raspberrypi.com/news/more-memory-driven-price-rises/ |
| `source_last_checked` | 2026-07-18 |
| `price_valid_until` | 2026-08-17 |
| `refresh_reason` | Initial discovery and receive-only hardware baseline; refresh after 30 days or a material price, maintenance, license, or legal-risk change. |
| `first_seen` | 2026-07-18 |
| `last_seen` | 2026-07-18 |
| `change_status` | `new` |
| `change_summary` | First radar appearance with a legal passive sensor-dashboard scope and receiver pricing. |
| `risk_notes` | Must avoid interception of protected communications, transmission, evasion, or offensive workflows. |
| `recommended_next_step` | `ready_for_review`: write a passive-only SDR learning brief with legal/safety boundaries. |
| `one_week_deliverable` | A passive-only SDR project brief, sanitized sensor event schema, mock dataset, and dashboard acceptance plan. |
| `success_criteria` | The brief limits scope to legal public sensor broadcasts, names the jurisdiction check, and defines a mock-data demo that requires no reception. |
| `demo_artifact` | Sanitized synthetic sensor-event file and static local dashboard/report mockup. |
| `prerequisites` | Confirm local law/policy, owned receiver inventory, allowed sensor class, and explicit receive-only scope. |
| `first_three_tasks` | 1. Define the allowed public sensor class and legal check. 2. Specify a sanitized event schema and mock records. 3. Draft the passive dashboard brief and stop conditions. |
| `blockers` | Jurisdiction, target sensor class, antenna needs, and SDR inventory are unconfirmed. |
| `stop_conditions` | Stop if scope includes transmission, protected communications, access controls, evasion, or identifiable private activity. |
| `safety_notes` | Passive, legal, educational receive-only planning; no interception, decryption, transmission, exploitation, or live collection is approved. |

### project_opportunity: WildBridge

| Field | Value |
| --- | --- |
| `project_id` | `20260718-wildbridge` |
| `project_name` | WildBridge |
| `source_url` | https://github.com/WildDrone/WildBridge |
| `item_type` | `project_opportunity` |
| `priority_score` | 3 |
| `priority_rationale` | Interesting drone telemetry/reference project, but control surfaces and safety constraints make it review-heavy. |
| `plain_language_summary` | WildBridge connects supported DJI drone systems to robotics software so telemetry, logs, and video can be viewed or processed by other tools. AI Lab is considering only passive recorded-data ideas, not drone control. |
| `problem_it_solves` | Drone data is often locked inside a controller or mobile application, which makes it hard for researchers to study flights with standard robotics tools. |
| `who_it_is_for` | Drone and robotics researchers, developers building ground-station tools, and teams reviewing flight data. |
| `common_use_cases` | Flight-log review; telemetry dashboards; robotics research; video/position correlation; simulated ground-station workflows. |
| `how_it_works_in_practice` | A supported Android device receives information from the drone/controller and translates it into messages that robotics software can understand. Other computers can then display, record, or analyze those messages. |
| `ai_lab_use_case` | AI Lab would use synthetic flight records to design a passive telemetry dashboard and data-import format with no live drone, controller, or video connection. |
| `limitations` | Hardware and controller compatibility are strict, and live flight introduces physical, legal, credential, and privacy risks. The proposed lab scope does not include command, control, autonomy, or live video. |
| `public_adoption_signal` | Public GitHub repo visible; supporting research metadata visible. |
| `why_interesting` | Bridges DJI UX context with telemetry, logs, discovery, and video publishing in the background. |
| `business_tie_in` | Portfolio concept: passive flight-log and telemetry review dashboard, not autonomous operation. |
| `learning_value` | Teaches ROS2/mobile ground-station architecture and telemetry/log design. |
| `local_fit` | Useful as a design reference for local telemetry import artifacts. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-18 |
| `cost_scope` | Safe first scope is a passive recorded-telemetry/dashboard prototype; connected-hardware pricing is included for planning but live flight/control remains unapproved. |
| `incremental_cost` | $0-$50 for a passive log/dashboard proof using existing lab hardware and sanitized sample telemetry. |
| `from_scratch_cost` | $1,300-$1,550 for a one-drone connected bench using the observed $759 DJI Mini 4 Pro package and a $499 Android phone, plus tax/cabling/network allowance. |
| `portfolio_build_cost` | $1,500-$2,100 for extra batteries, case, dedicated local networking, spares, and field presentation equipment. |
| `diy_effort_hours` | 24-60 hours for the passive dashboard and integration review; connected hardware would add approximately 20-40 hours. |
| `recurring_monthly_cost` | $2-$10 for charging, local storage, and occasional operation; insurance, permits, and paid field access are excluded. |
| `cost_confidence` | Low. Drone and phone prices are explicit, but the exact supported controller/app combination must be verified before any purchase. |
| `cost_assumptions` | Existing Mac Studio is the ground station; no autonomous operation; no cloud video service; one drone only. |
| `cost_exclusions` | Insurance, permits, travel, repairs, replacement aircraft, labor valuation, commercial operations, and multi-drone expansion. |
| `cost_source_urls` | https://github.com/WildDrone/WildBridge ; https://store.dji.com/product/dji-mini-4-pro ; https://store.google.com/config/pixel_9a?hl=en-US |
| `source_last_checked` | 2026-07-18 |
| `price_valid_until` | 2026-08-17 |
| `refresh_reason` | Initial passive-proof and connected-bench baseline; refresh after 30 days or a material controller, release, maintenance, price, legal, or safety change. |
| `first_seen` | 2026-07-18 |
| `last_seen` | 2026-07-18 |
| `change_status` | `new` |
| `change_summary` | First radar appearance with passive and connected-hardware scenarios separated. |
| `risk_notes` | Anything involving command/control, flight operation, or live video needs separate safety, legal, and hardware review. |
| `recommended_next_step` | `watchlist`: keep as reference for a passive flight-log parser/report lane only. |
| `one_week_deliverable` | A passive flight-log schema, sanitized fixture set, and telemetry dashboard brief with no live drone connection. |
| `success_criteria` | The brief parses only approved synthetic or sanitized records, documents data provenance, and excludes command/control and live video. |
| `demo_artifact` | Synthetic telemetry log and static local flight-summary dashboard/report mockup. |
| `prerequisites` | Approve passive log analysis, identify a sanitized data source, and confirm no flight or controller integration. |
| `first_three_tasks` | 1. Define a minimal passive telemetry schema. 2. Create synthetic flight records and privacy rules. 3. Draft the dashboard brief and connected-hardware review questions. |
| `blockers` | Sanitized sample telemetry, controller compatibility, legal requirements, and hardware inventory are unconfirmed. |
| `stop_conditions` | Stop if progress requires live flight, command/control, autonomous behavior, public video, credentials, or hardware purchase. |
| `safety_notes` | Passive synthetic/log review only; no flight, live connection, command/control, autonomous operation, video publishing, or purchase is approved. |

### model_candidate: SmolLM3-3B-GGUF

| Field | Value |
| --- | --- |
| `candidate_id` | `20260718-smollm3-3b-gguf` |
| `model_name` | SmolLM3-3B-GGUF |
| `model_family` | SmolLM3 |
| `provider_or_org` | ggml-org packaging from Hugging FaceTB source model |
| `params_b` | 3 |
| `format_or_runtime` | GGUF with Q4_K_M, Q8_0, and F16 metadata |
| `claimed_context_window` | 64K trained context and up to 128K with YaRN claimed by source metadata |
| `license` | Apache-2.0 shown on the model page |
| `source_url` | https://huggingface.co/ggml-org/SmolLM3-3B-GGUF |
| `public_adoption_signal` | Source page showed 8,056 downloads last month and 66 likes during the scan; context only. |
| `discovered_at` | 2026-07-18 |
| `why_interesting` | Small official GGUF with explicit artifact sizes and multiple familiar local runtime paths; useful for a fast baseline lane. |
| `local_fit` | Excellent theoretical fit for the existing Mac Studio and practical enough for a low-overhead baseline after approval. |
| `estimated_artifact_size` | 1.92 GB Q4_K_M, 3.28 GB Q8_0, or 6.16 GB F16, source-declared. |
| `estimated_disk_requirement` | Approximately 4-8 GB inferred for one selected artifact plus runtime/cache overhead. |
| `expected_memory_range` | Approximately 4-8 GB inferred for Q4 at moderate context; long-context memory remains unverified. |
| `compatible_local_runtimes` | Source page names llama.cpp, LM Studio, Ollama, ONNX, MLX, and MLC; exact approved local model ID is unverified. |
| `benchmark_gap` | Select and review an exact GGUF artifact/hash, verify the Jinja thinking template, confirm a local runner ID, and approve local execution before using `evals/local-llm-benchmark/SPEC.md`. |
| `risk_notes` | Model-card install/run examples were not followed; exact artifact hash, template behavior, and long-context memory need review. |
| `security_review_status` | `needs_review` |
| `download_approval` | `not_approved` |
| `license_review_status` | `needs_review` |
| `provenance_status` | `source_metadata_only` |
| `security_notes` | Metadata only. Prefer a reviewed GGUF path in an existing local runtime; do not run model-card scripts or one-line installers. |
| `isolation_notes` | If later approved, use the exact reviewed local artifact through llama.cpp, LM Studio, or Ollama and keep raw evidence local. |
| `recommended_next_step` | `needs_more_info` |
| `proposed_eval` | After exact artifact/security approval only: add a compact baseline run through `evals/local-llm-benchmark/SPEC.md` and `skills/local-llm-eval`. |
| `source_last_checked` | 2026-07-18 |
| `first_seen` | 2026-07-18 |
| `last_seen` | 2026-07-18 |
| `change_status` | `new` |
| `change_summary` | First radar appearance of the official ggml-org SmolLM3 GGUF packaging. |

### model_candidate: Bonsai-27B-gguf

| Field | Value |
| --- | --- |
| `candidate_id` | `20260718-bonsai-27b-gguf` |
| `model_name` | Bonsai-27B-gguf |
| `model_family` | Qwen3.6-derived Bonsai |
| `provider_or_org` | Prism ML |
| `params_b` | Approximately 27.3 claimed by source metadata |
| `format_or_runtime` | Custom 1-bit GGUF Q1_0_g128; custom llama.cpp/MLX forks referenced |
| `claimed_context_window` | 262K claimed by source metadata |
| `license` | Apache-2.0 shown on the model page |
| `source_url` | https://huggingface.co/prism-ml/Bonsai-27B-gguf |
| `public_adoption_signal` | Source page showed 426 likes during the scan; adoption is context only. |
| `discovered_at` | 2026-07-18 |
| `why_interesting` | Source claims a 3.9 GB deployed 27B-class derivative with Metal support, making it an unusually compact local reasoning candidate. |
| `local_fit` | Attractive Apple Silicon size on paper, but the required custom low-bit kernels conflict with the preferred stock-runtime path. |
| `estimated_artifact_size` | Approximately 3.9 GB deployed footprint, source-declared; optional vision projection is approximately 0.63 GB. |
| `estimated_disk_requirement` | Approximately 8-12 GB inferred for weights, optional projection, custom runtime, and working overhead. |
| `expected_memory_range` | Approximately 8-16 GB inferred for moderate context; source claims roughly 4.3 GB KV cache at full 262K context on selected layers, but local behavior is unverified. |
| `compatible_local_runtimes` | Source references custom llama.cpp Metal and MLX forks; compatibility with stock llama.cpp, LM Studio, or Ollama is not established. |
| `benchmark_gap` | Independent provenance/license review, exact files/hashes, custom-kernel code review, stock-runtime compatibility, and a comparable prompt template are missing. |
| `risk_notes` | Derivative source claims and custom runtime forks create elevated code-execution and benchmark-comparability risk. |
| `security_review_status` | `needs_review` |
| `download_approval` | `not_approved` |
| `license_review_status` | `needs_review` |
| `provenance_status` | `source_metadata_only` |
| `security_notes` | Metadata only. Do not use the referenced custom forks, kernels, scripts, or artifacts without a separate source/code/security review. |
| `isolation_notes` | Keep on metadata watchlist until a stock-runtime path or separately approved isolated custom-runtime review exists. |
| `recommended_next_step` | `needs_more_info` |
| `proposed_eval` | No benchmark task yet; first determine whether a reviewed stock-runtime artifact exists. |
| `source_last_checked` | 2026-07-18 |
| `first_seen` | 2026-07-18 |
| `last_seen` | 2026-07-18 |
| `change_status` | `new` |
| `change_summary` | First radar appearance of this compact 1-bit GGUF derivative and its custom-runtime claims. |

### project_opportunity: Dagu

| Field | Value |
| --- | --- |
| `project_id` | `20260718-dagu-workflow-engine` |
| `project_name` | Dagu |
| `source_url` | https://github.com/dagucloud/dagu |
| `item_type` | `project_opportunity` |
| `priority_score` | 4 |
| `priority_rationale` | Strong local-first workflow reliability reference with file-backed state, retries, approvals, and no required DBMS; script/container/SSH execution and GPL embedding terms need review. |
| `plain_language_summary` | Dagu is a scheduler and control panel for repeatable computer jobs. It is similar to a more visible and manageable version of cron, the traditional background job scheduler. |
| `problem_it_solves` | Important scripts and scheduled jobs can fail silently, overlap, or become difficult to understand when their steps, retries, and history are scattered. |
| `who_it_is_for` | Small engineering, operations, and data teams that run recurring jobs on local or self-hosted computers. |
| `common_use_cases` | Backups; data-processing pipelines; scheduled reports; health checks; sensor jobs; approved internal support tasks. |
| `how_it_works_in_practice` | A workflow file lists the jobs and their order. Dagu starts them on schedule, records what happened, retries allowed failures, and shows their status in a web interface. |
| `ai_lab_use_case` | AI Lab would compare Dagu's workflow states and recovery ideas with one existing automation, using a mock event transcript instead of installing or running Dagu. |
| `limitations` | Dagu can execute powerful commands, remote connections, and containers, so real deployment needs strong access controls. It is not an AI model, and GPL/commercial embedding terms need separate review. |
| `public_adoption_signal` | GitHub showed 3.6k stars, 292 forks, and v2.10.7 released 2026-07-12. |
| `why_interesting` | Offers a concrete comparison point for making scheduled local automations observable, retryable, and approval-aware. |
| `business_tie_in` | Could inspire a lightweight client operations console or governed internal automation product. |
| `learning_value` | Useful for studying file-backed workflow state, retry policies, concurrency, approval points, and local observability. |
| `local_fit` | Strong as a design reference; direct runtime adoption is not needed to improve AI Lab OS automation SOPs. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-18 |
| `cost_scope` | Documentation-only workflow-governance comparison plus a deterministic mock lifecycle; no Dagu installation or workflow execution. |
| `incremental_cost` | $0-$25 on the existing Mac Studio for local documentation and mock artifacts; software has no purchase price. |
| `from_scratch_cost` | $220-$350 planning range for a dedicated 16 GB / 512 GB mini PC if a later isolated functional prototype is approved. |
| `portfolio_build_cost` | $250-$500 for a dedicated host, backup storage, power protection, and presentation finish. |
| `diy_effort_hours` | 8-16 hours for architecture mapping, mock workflow state, failure scenarios, and a review brief. |
| `recurring_monthly_cost` | $0 on the existing Mac; approximately $2-$6 for an always-on low-power dedicated host. |
| `cost_confidence` | Medium. Software/license and existing-lab scope are explicit; dedicated-host and effort ranges are planning estimates. |
| `cost_assumptions` | Reuses existing lab compute for the design artifact; no scripts, containers, SSH, webhooks, managed service, or MCP execution. |
| `cost_exclusions` | Production operations, commercial embedding advice, cloud service, credentials, labor valuation, and workflow migration. |
| `cost_source_urls` | https://github.com/dagucloud/dagu ; https://store.minisforum.com/en-ph/products/minisforum-un100p |
| `source_last_checked` | 2026-07-18 |
| `price_valid_until` | 2026-08-17 |
| `refresh_reason` | Initial discovery after the 2026-07-12 release and baseline host pricing; refresh after 30 days or a material release, license, maintenance, price, or risk change. |
| `first_seen` | 2026-07-18 |
| `last_seen` | 2026-07-18 |
| `change_status` | `new` |
| `change_summary` | First radar appearance with recent release, local file-backed workflow metadata, and GPL embedding caveat. |
| `risk_notes` | Built-in execution covers scripts, SSH, containers, webhooks, and MCP controls; GPL/commercial embedding boundaries also need review. |
| `recommended_next_step` | `ready_for_review`: compare workflow-state and approval concepts to the current automation SOP without installing Dagu. |
| `one_week_deliverable` | A no-install workflow-governance comparison and deterministic mock lifecycle for one AI Lab OS automation. |
| `success_criteria` | The brief maps states, retries, concurrency, approvals, audit events, and failure recovery to current automation boundaries. |
| `demo_artifact` | Sanitized state diagram and mock JSONL/Markdown workflow event transcript. |
| `prerequisites` | Approve a documentation-only review and select one non-sensitive automation as the comparison case. |
| `first_three_tasks` | 1. Map Dagu public workflow concepts to the selected automation. 2. Define mock states, failures, retries, and approvals. 3. Draft the comparison and one scoped follow-up. |
| `blockers` | GPL embedding posture, executable-step breadth, MCP control surface, and managed/cloud boundaries are unresolved. |
| `stop_conditions` | Stop if progress requires installation, workflow execution, credentials, SSH, containers, webhooks, or runtime adoption. |
| `safety_notes` | Design review only; no installer, binary, workflow, script, container, SSH, webhook, MCP, credential, or managed service use is approved. |

### project_opportunity: AiderDesk

| Field | Value |
| --- | --- |
| `project_id` | `20260718-aiderdesk` |
| `project_name` | AiderDesk |
| `source_url` | https://github.com/hotovo/aider-desk |
| `item_type` | `project_opportunity` |
| `priority_score` | 4 |
| `priority_rationale` | Strong reference for worktree isolation, diff review, and tool approvals, but broad subagent/provider/extension behavior is outside the current runtime scope. |
| `plain_language_summary` | AiderDesk is a desktop workbench for organizing AI-assisted coding tasks. It keeps tasks in separate copies of a codebase and gives people review and approval controls before changes are merged. |
| `problem_it_solves` | AI coding work can mix unrelated tasks, lose context, or change files before a person has clearly reviewed what happened. |
| `who_it_is_for` | Software developers and engineering teams that use coding assistants but want stronger task isolation and human review. |
| `common_use_cases` | Running separate feature tasks; reviewing proposed code changes; comparing alternative approaches; managing several repositories; requiring approval before tool use. |
| `how_it_works_in_practice` | Each task gets an isolated Git worktree, which is a separate working copy of the code. An assistant proposes changes there, the user reviews the differences, and approved work can be merged back. |
| `ai_lab_use_case` | AI Lab would create a static wireflow showing task isolation, approvals, and review states using fictional repository data, without installing AiderDesk or connecting a model. |
| `limitations` | It is not a coding model. Real use still requires repository access, model providers, credentials, memory storage, and executable extensions, creating a much broader trust boundary than the proposed design study. |
| `public_adoption_signal` | GitHub showed 1.3k stars, 115 forks, Apache-2.0, and v0.74.0 released 2026-07-13. |
| `why_interesting` | Its task isolation, review gates, and context controls map directly to safe coding-agent workflow design. |
| `business_tie_in` | Could inform a portfolio-quality local engineering workbench or client-facing change-review workflow. |
| `learning_value` | Useful for studying worktree isolation, approval UX, task forking, diff review, and context curation. |
| `local_fit` | Good design reference for the dashboard/task loop, without adopting its Electron or agent runtime. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-18 |
| `cost_scope` | No-install UX/architecture teardown and static approval-flow prototype using existing repo artifacts. |
| `incremental_cost` | $0-$25 on existing lab hardware; Apache-2.0 software has no purchase price. |
| `from_scratch_cost` | $220-$350 planning range for a dedicated 16 GB / 512 GB demo host if a later isolated prototype is approved. |
| `portfolio_build_cost` | $250-$500 for dedicated host, backup storage, and polished presentation artifacts. |
| `diy_effort_hours` | 8-16 hours for workflow mapping, wireframes, threat review, and a sanitized static demo. |
| `recurring_monthly_cost` | $0 for a static existing-lab review; approximately $2-$6 for an always-on dedicated host. |
| `cost_confidence` | Medium. Software/license and design scope are explicit; host and effort ranges depend on a later prototype decision. |
| `cost_assumptions` | Uses only existing local repo metadata and mock tasks; no provider, repository attachment, extension, vector index, or agent execution. |
| `cost_exclusions` | Model/provider usage, credentials, hosted services, production support, labor valuation, and direct application adoption. |
| `cost_source_urls` | https://github.com/hotovo/aider-desk ; https://store.minisforum.com/en-ph/products/minisforum-un100p |
| `source_last_checked` | 2026-07-18 |
| `price_valid_until` | 2026-08-17 |
| `refresh_reason` | Initial discovery after the 2026-07-13 release and baseline host pricing; refresh after 30 days or a material release, license, maintenance, price, or risk change. |
| `first_seen` | 2026-07-18 |
| `last_seen` | 2026-07-18 |
| `change_status` | `new` |
| `change_summary` | First radar appearance with recent release and explicit worktree/tool-approval metadata. |
| `risk_notes` | Electron surface, multiple providers, vector memory, subagents, repository access, and extension code create a broad trust boundary. |
| `recommended_next_step` | `watchlist`: extract worktree and approval UX patterns only; no application adoption. |
| `one_week_deliverable` | A static coding-task approval-flow comparison covering worktree isolation, diff review, task forks, and context controls. |
| `success_criteria` | The artifact identifies three reusable UX patterns, rejected runtime assumptions, and one dashboard-sized follow-up. |
| `demo_artifact` | Sanitized wireflow and mock task/review transcript using fictional repository data. |
| `prerequisites` | Approve a design-only review and define the current AI Lab OS task/review flow being compared. |
| `first_three_tasks` | 1. Map public AiderDesk controls to current task states. 2. Threat-model provider, repository, memory, and extension boundaries. 3. Draft the wireflow and follow-up recommendation. |
| `blockers` | No approved need for a second coding-agent UI; provider, memory, extension, and repository-access boundaries remain broad. |
| `stop_conditions` | Stop if the work requires application installation, repository attachment, provider credentials, vector indexing, extension code, or agent execution. |
| `safety_notes` | Static design review only; no download, application launch, repository access, provider connection, secret, extension, tool call, or agent action is approved. |

### project_opportunity: LocalAI

| Field | Value |
| --- | --- |
| `project_id` | `20260718-localai-runtime-reference` |
| `project_name` | LocalAI |
| `source_url` | https://github.com/mudler/LocalAI |
| `item_type` | `project_opportunity` |
| `priority_score` | 3 |
| `priority_rationale` | Strong local runtime breadth and Apple Silicon metadata, but automatic model/backend management, agents, fine-tuning, distributed services, and API-key features exceed the lab's narrow provider harness. |
| `plain_language_summary` | LocalAI is a self-hosted server that gives many kinds of AI models one common local interface. It aims to provide a private alternative to sending every AI request to a cloud provider. |
| `problem_it_solves` | Different local models and runtimes often require different setup and interfaces, making it hard to manage text, image, speech, and retrieval tools consistently. |
| `who_it_is_for` | Developers and teams that want to operate several AI capabilities on their own computers or private infrastructure. |
| `common_use_cases` | Local chat; text generation; image or speech workflows; embeddings and reranking; routing requests across several local backends. |
| `how_it_works_in_practice` | LocalAI manages selected model backends and exposes a shared local application interface. Applications send requests to that interface, and LocalAI routes them to the appropriate local capability. |
| `ai_lab_use_case` | AI Lab would build a capability comparison and mock model-role/health dashboard showing which LocalAI ideas are useful for the existing Ollama and LM Studio provider harness. |
| `limitations` | The full platform can manage downloads, backends, agents, fine-tuning, authentication, and distributed services. Those features add supply-chain and operational complexity and are excluded from the proposed comparison. |
| `public_adoption_signal` | GitHub showed 47.6k stars, 4.3k forks, MIT license, and v4.7.1 released 2026-07-14. |
| `why_interesting` | Useful architecture reference for a local inference control plane spanning multiple model roles and runtimes. |
| `business_tie_in` | Could inform a private multi-model gateway or internal inference operations product, without importing the platform. |
| `learning_value` | Good comparison for backend modularity, model-role routing, quotas, health, and Apple Silicon support. |
| `local_fit` | Conceptually relevant, but much broader than the current dependency-light Ollama/LM Studio provider harness. |
| `cost_currency` | USD |
| `cost_as_of` | 2026-07-18 |
| `cost_scope` | Documentation-only capability-gap analysis against the existing provider harness; no LocalAI installation, backend, or model management. |
| `incremental_cost` | $0-$50 on the existing Mac Studio for architecture review and sanitized mock control-plane artifacts. |
| `from_scratch_cost` | $220-$500 planning range for a dedicated local host; actual model workloads could require substantially more hardware. |
| `portfolio_build_cost` | $500-$1,500 for stronger compute/storage, backup, and presentation finish, excluding model-specific accelerator needs. |
| `diy_effort_hours` | 16-40 hours for capability mapping, role boundaries, threat review, and a polished architecture demo. |
| `recurring_monthly_cost` | $0 for documentation-only review; approximately $2-$10 for a dedicated always-on host, excluding model-provider or storage growth. |
| `cost_confidence` | Low. Software/license are explicit, but hardware depends heavily on selected model roles, backends, context, and concurrency. |
| `cost_assumptions` | Reuses existing lab hardware for review; no model import, quantization, fine-tuning, agents, distributed mode, backend gallery, or public API exposure. |
| `cost_exclusions` | Model artifacts, accelerators, cloud/providers, credentials, production security, labor valuation, and distributed infrastructure. |
| `cost_source_urls` | https://github.com/mudler/LocalAI ; https://store.minisforum.com/en-ph/products/minisforum-un100p |
| `source_last_checked` | 2026-07-18 |
| `price_valid_until` | 2026-08-17 |
| `refresh_reason` | Initial discovery after the 2026-07-14 release and broad capability review; refresh after 30 days or a material release, license, maintenance, price, or risk change. |
| `first_seen` | 2026-07-18 |
| `last_seen` | 2026-07-18 |
| `change_status` | `new` |
| `change_summary` | First radar appearance with recent release, Apple Silicon support metadata, and explicit scope-risk notes. |
| `risk_notes` | Built-in model downloads, on-the-fly backends, agents, fine-tuning, APIs, keys, and distributed services conflict with current local-first/dependency-light boundaries if adopted directly. |
| `recommended_next_step` | `needs_more_info`: perform architecture comparison only; do not adopt or run the platform. |
| `one_week_deliverable` | A no-install capability-gap matrix between LocalAI and the current Ollama/LM Studio provider harness. |
| `success_criteria` | The matrix separates useful provider-control concepts from rejected model-management, agent, fine-tuning, auth, and distributed features. |
| `demo_artifact` | Sanitized architecture diagram and mock model-role/health dashboard data. |
| `prerequisites` | Approve a documentation-only comparison and define the provider-harness questions to answer. |
| `first_three_tasks` | 1. Inventory public LocalAI capabilities and current provider boundaries. 2. Classify useful, redundant, and prohibited features. 3. Draft the matrix, mock diagram, and one bounded follow-up. |
| `blockers` | Broad feature surface, backend supply chain, automatic downloads, API/auth behavior, telemetry posture, and production hardening are unresolved. |
| `stop_conditions` | Stop if progress requires platform installation, backend/model retrieval, fine-tuning, agents, API keys, public endpoints, or distributed services. |
| `safety_notes` | Architecture review only; no platform/backend/model download, quantization, fine-tuning, agent, API, key, public endpoint, or distributed execution is approved. |

## Reviewer Notes

- These items are not approved for registry entry.
- Model candidates must not be added to `data/model_registry/candidates.csv`
  until the user approves specific rows and security review scope.
- Project opportunities must not be added to
  `data/project_registry/github_repos.csv` until the user approves specific
  rows.
- No source claim here is a benchmark score, quality score, final label, or
  dashboard decision.

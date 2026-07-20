# AI Lab Radar Report

Date: 2026-07-18
Reviewer: Codex automation
Source packet: `automations/ai-lab-radar/inputs/2026-07-18-daily-external-radar.md`
Approved for radar review: no
Safe to commit: no
Dashboard: [Radar candidates](http://127.0.0.1:8765/radar) after starting the local dashboard.

## Summary

- Candidates reviewed: 5 model candidates and 8 project opportunities
- Ready for evaluation: 0
- Ready for project review: 3
- Watchlist: 5
- Skipped: 0
- Needs more information: 5
- Project cost estimates: 8 scoped estimates; 6 medium-confidence and 2
  low-confidence due to unresolved controller/model-workload compatibility

No new approved Local Radar packet was found, so this run used Daily External
Radar. The scan reviewed 24 discovery items plus supplemental official pricing
and sizing pages for the five reported projects. It did not edit model or
project registries. The local profile confirms the existing Mac Studio; edge,
radio, and drone inventory plus maximum DIY hours and portfolio budget remain
unconfirmed, so conditional existing-hardware prices are labeled accordingly.

A same-day scheduled follow-up reviewed 27 additional public metadata items and
added five previously unreported deltas: SmolLM3-3B-GGUF, Bonsai-27B-gguf,
Dagu, AiderDesk, and LocalAI. No existing item was repeated solely for
popularity or source re-access.

## Delta Summary

All thirteen reported items are new on 2026-07-18. Future daily reports will omit
them unless a price, release, license, maintenance, or risk change is material.

| Item | Type | Status | First seen | Last seen | Change summary |
| --- | --- | --- | --- | --- | --- |
| Qwen3-Coder-Next-GGUF | `model_candidate` | `new` | 2026-07-18 | 2026-07-18 | First appearance of this specific coding GGUF candidate. |
| Qwopus3.6-27B-Coder-MTP-4bit.mlx | `model_candidate` | `new` | 2026-07-18 | 2026-07-18 | First appearance of this specific MLX coding artifact. |
| Phi-4-Reasoning-Vision-15B | `model_candidate` | `new` | 2026-07-18 | 2026-07-18 | First appearance of this official multimodal candidate. |
| Future AGI | `project_opportunity` | `new` | 2026-07-18 | 2026-07-18 | First appearance with self-host sizing and a host-cost baseline. |
| mcp-agent | `project_opportunity` | `new` | 2026-07-18 | 2026-07-18 | First appearance with a constrained local-only demo estimate. |
| Raspberry Pi AI Camera + IMX500 Model Zoo | `project_opportunity` | `new` | 2026-07-18 | 2026-07-18 | First appearance with official camera metadata and three cost scenarios. |
| rtl_433 | `project_opportunity` | `new` | 2026-07-18 | 2026-07-18 | First appearance with a passive receive-only scope and hardware estimate. |
| WildBridge | `project_opportunity` | `new` | 2026-07-18 | 2026-07-18 | First appearance with passive and connected-hardware scopes separated. |
| SmolLM3-3B-GGUF | `model_candidate` | `new` | 2026-07-18 | 2026-07-18 | First appearance of the official ggml-org SmolLM3 GGUF packaging. |
| Bonsai-27B-gguf | `model_candidate` | `new` | 2026-07-18 | 2026-07-18 | First appearance of the compact 1-bit derivative and custom-runtime claims. |
| Dagu | `project_opportunity` | `new` | 2026-07-18 | 2026-07-18 | First appearance with recent release, file-backed workflow metadata, and GPL caveat. |
| AiderDesk | `project_opportunity` | `new` | 2026-07-18 | 2026-07-18 | First appearance with recent release and explicit worktree/tool-approval metadata. |
| LocalAI | `project_opportunity` | `new` | 2026-07-18 | 2026-07-18 | First appearance with recent release, Apple Silicon metadata, and scope-risk notes. |

## Top Recommendations

| Rank | Item | Type | Recommendation | Why now |
| --- | --- | --- | --- | --- |
| 1 | Raspberry Pi AI Camera + IMX500 Model Zoo | `project_opportunity` | `ready_for_review` | Best contained edge/portfolio lane; recommended prototype estimate is $195-$225 delivered. |
| 2 | SmolLM3-3B-GGUF | `model_candidate` | `needs_more_info` | Most practical new model delta: explicit 1.92 GB Q4 artifact and familiar local runtimes, pending exact artifact/template approval. |
| 3 | Dagu | `project_opportunity` | `ready_for_review` | Strong local workflow-governance reference with retries, approvals, recent maintenance, and no required DBMS. |
| 4 | Qwen3-Coder-Next-GGUF | `model_candidate` | `needs_more_info` | Potential high-end coding-agent successor to the current Qwen lane, but artifact/license/runtime review is unresolved. |
| 5 | rtl_433 | `project_opportunity` | `ready_for_review` | Strong passive SDR/sensor learning lane if strict legal receive-only boundaries are written first. |

## Candidate Review

| Candidate | Source | Why interesting | Risk notes | Recommended next step |
| --- | --- | --- | --- | --- |
| Qwen3-Coder-Next-GGUF | https://huggingface.co/unsloth/Qwen3-Coder-Next-GGUF | Coding-agent GGUF candidate with source claims around 80B total / 3B active parameters, local development, and long-horizon tool use. | External metadata only; license, exact artifact, checksum, quantization source, and runtime behavior are unreviewed. | `needs_more_info` |
| Qwopus3.6-27B-Coder-MTP-4bit.mlx | https://huggingface.co/jedisct1/Qwopus3.6-27B-Coder-MTP-4bit.mlx | MLX coding-agent artifact with local validation claims and source-visible 17 GB size metadata. | Packaging is not the upstream base model; patched templates and mixed parameter metadata need review. | `watchlist` |
| Phi-4-Reasoning-Vision-15B | https://huggingface.co/microsoft/Phi-4-reasoning-vision-15B | Official 15B multimodal reasoning model that could anchor a future vision lane. | Current benchmark is text-first; no reviewed local GGUF/MLX runtime path exists. | `watchlist` |
| Future AGI | https://github.com/future-agi/future-agi | Self-hostable eval/observability stack could inform confirmed-score workflow design. | Full platform with gateway/cloud-adjacent concepts; too heavy for direct dependency adoption. | `needs_more_info` |
| mcp-agent | https://github.com/lastmile-ai/mcp-agent | MCP workflow framework is useful for future agent/eval SOP design. | AI Lab OS v0 forbids agent orchestration in the RAG runtime. | `watchlist` |
| Raspberry Pi AI Camera + IMX500 Model Zoo | https://www.raspberrypi.com/documentation/accessories/ai-camera.html | Strong edge AI and portfolio lane for local field-system demos. | Hardware/software setup is outside radar and not approved here. | `ready_for_review` |
| rtl_433 | https://github.com/merbanan/rtl_433 | Passive SDR/sensor metadata lane for legal radio-learning and local dashboards. | Must stay receive-only, legal, and non-offensive. | `ready_for_review` |
| WildBridge | https://github.com/WildDrone/WildBridge | Drone telemetry/control reference for passive flight-log reporting concepts. | Live control/video/flight operation risk is high; keep to passive design review. | `watchlist` |
| SmolLM3-3B-GGUF | https://huggingface.co/ggml-org/SmolLM3-3B-GGUF | Compact official GGUF with explicit Q4/Q8/F16 sizes and familiar local runtime metadata. | Exact artifact/hash, Jinja thinking template, and approved local runner are unresolved. | `needs_more_info` |
| Bonsai-27B-gguf | https://huggingface.co/prism-ml/Bonsai-27B-gguf | Source claims a 3.9 GB 27B-class derivative with Metal support. | Custom kernels/runtime forks and derivative benchmark claims require separate review. | `needs_more_info` |
| Dagu | https://github.com/dagucloud/dagu | File-backed local workflow engine is a useful reliability/approval reference. | Script, SSH, container, webhook, MCP execution, and GPL embedding scope need review. | `ready_for_review` |
| AiderDesk | https://github.com/hotovo/aider-desk | Worktree isolation, diff review, and tool approvals map to safe coding-task UX. | Broad provider, repository, vector-memory, subagent, and extension trust boundary. | `watchlist` |
| LocalAI | https://github.com/mudler/LocalAI | Broad local inference control-plane reference with Apple Silicon paths. | Built-in downloads, backends, agents, fine-tuning, auth, and distributed services exceed current scope. | `needs_more_info` |

## Model Practicality

| Candidate | Artifact size | Disk requirement | Expected memory | Compatible local runtimes | Benchmark gap |
| --- | --- | --- | --- | --- | --- |
| Qwen3-Coder-Next-GGUF | Unknown until a quant is selected. | Unknown; artifact plus runtime/cache overhead. | Unknown until quant, context, and runtime are selected. | GGUF suggests llama.cpp, LM Studio, or Ollama; unverified. | Exact artifact, license, hash, template, context, and approved local runner. |
| Qwopus3.6-27B-Coder-MTP-4bit.mlx | 17 GB source-declared. | About 25 GB inferred planning allowance. | Unknown until MLX context and MTP behavior are reviewed. | MLX/MLX-LM expected; command/template unverified. | Publisher chain, license, hashes, template patch, runner, and comparability review. |
| Phi-4-Reasoning-Vision-15B | Unknown; no local artifact selected. | Unknown until artifact selection. | Unknown until precision, image/context workload, and runtime are selected. | Official Safetensors metadata; dependency-light local path unverified. | Reviewed local artifact plus a vision benchmark lane with fixtures and scoring rules. |
| SmolLM3-3B-GGUF | 1.92 GB Q4, 3.28 GB Q8, 6.16 GB F16, source-declared. | About 4-8 GB inferred for one artifact and overhead. | About 4-8 GB inferred for Q4 at moderate context; long context unverified. | llama.cpp, LM Studio, Ollama, ONNX, MLX, and MLC are source-visible; local ID unverified. | Exact artifact/hash, Jinja thinking template, approved runner, and execution approval. |
| Bonsai-27B-gguf | About 3.9 GB source-declared; optional 0.63 GB vision projection. | About 8-12 GB inferred with custom runtime overhead. | About 8-16 GB inferred for moderate context; full-context behavior unverified. | Custom llama.cpp Metal and MLX forks; stock runtime compatibility unknown. | Provenance, hashes, custom-kernel review, stock-runtime compatibility, and prompt comparability. |

## Project Explainers

### Future AGI

| Question | Plain-language answer |
| --- | --- |
| What is it? | A control center for checking how AI applications behave and collecting evidence about their answers and workflows. |
| What problem does it solve? | Teams often lack one place to trace AI failures, compare changes, and review whether quality or safety improved. |
| Who is it for? | Teams building AI assistants, automated workflows, or customer-facing AI features. |
| What is it commonly used for? | Reviewing answer quality, tracing failed tasks, comparing prompts/models, monitoring safety checks, and organizing test data. |
| How does it work in practice? | An AI application sends interaction records to the platform; checks organize the evidence, dashboards show patterns, and people review the results. |
| What would AI Lab build? | A static comparison mapping these review ideas to the lab's draft-versus-confirmed score flow, using mock records only. |
| What are the limitations? | It is a broad platform with gateway, cloud, agent, and container features. AI Lab would study the review pattern without running the platform. |

### mcp-agent

| Question | Plain-language answer |
| --- | --- |
| What is it? | A framework for AI assistants that perform several tool-based steps. MCP means Model Context Protocol, a standard way to connect approved tools. |
| What problem does it solve? | Multi-step AI work becomes hard to organize when it must remember progress, use several tools, pause for people, and recover from failures. |
| Who is it for? | Developers designing tool-using assistants and human-approved business automations. |
| What is it commonly used for? | Research workflows, document processing, multi-step business tasks, tool coordination, and approval checkpoints. |
| How does it work in practice? | A developer defines the steps and allowed tools; the framework tracks progress, requests human input when needed, and resumes from stored state. |
| What would AI Lab build? | A no-install operating procedure for one fictional tool workflow, with deterministic mock approvals and audit events. |
| What are the limitations? | It is not an AI model and does not make tools safe by itself. Real agent/tool execution remains outside the v0 RAG runtime. |

### Raspberry Pi AI Camera + IMX500 Model Zoo

| Question | Plain-language answer |
| --- | --- |
| What is it? | A camera with a small AI chip built in, allowing it to recognize objects or visual patterns before sending compact results to a Raspberry Pi. |
| What problem does it solve? | Ordinary camera projects may need powerful computers or cloud services to analyze every image, increasing cost, delay, power use, and privacy risk. |
| Who is it for? | Hobbyists, students, educators, makers, and small teams building private low-power camera or field-sensor projects. |
| What is it commonly used for? | Wildlife monitoring, counting approved objects, equipment status, offline field logging, and computer-vision demonstrations. |
| How does it work in practice? | The camera captures an image, its Sony IMX500 chip runs a visual model, and the Pi receives labels or locations that it can log or display. |
| What would AI Lab build? | One stock-model demo that writes privacy-safe event records to a local dashboard, beginning with synthetic events and a reviewed parts list. |
| What are the limitations? | Results depend on lighting, placement, and model choice. Licenses/privacy require review; facial recognition, covert monitoring, and custom training are excluded. |

### rtl_433

| Question | Plain-language answer |
| --- | --- |
| What is it? | Software that turns radio messages from many common wireless sensors into readable event data through a receive-only radio device. |
| What problem does it solve? | Sensors broadcast readings in many different formats, making it hard to collect them in one local dashboard. |
| Who is it for? | Radio hobbyists, students, facilities teams, and researchers studying approved unencrypted sensor broadcasts. |
| What is it commonly used for? | Weather readings, outdoor temperature sensors, approved equipment telemetry, environmental dashboards, and radio education. |
| How does it work in practice? | A small receiver hears approved sensor broadcasts; rtl_433 recognizes supported formats and converts them into ordinary fields for storage or display. |
| What would AI Lab build? | A receive-only event format and dashboard using synthetic sensor messages before any separate live-reception review. |
| What are the limitations? | It cannot decode every device. Reception and legality vary; transmission, protected communications, decryption, evasion, and private-activity monitoring are excluded. |

### WildBridge

| Question | Plain-language answer |
| --- | --- |
| What is it? | A bridge that makes supported DJI drone telemetry, logs, and video understandable to robotics software. AI Lab is considering passive recorded data only. |
| What problem does it solve? | Drone data can be locked inside a controller or mobile app, making it difficult to study flights with standard robotics tools. |
| Who is it for? | Drone and robotics researchers, ground-station developers, and teams reviewing flight data. |
| What is it commonly used for? | Flight-log review, telemetry dashboards, robotics research, video/position correlation, and ground-station workflows. |
| How does it work in practice? | A supported Android device receives drone/controller information and translates it into messages that computers can display, record, or analyze. |
| What would AI Lab build? | A passive dashboard and import format using synthetic flight records, with no live drone, controller, or video connection. |
| What are the limitations? | Compatibility is strict and live flight adds physical, legal, credential, and privacy risks. Command, control, autonomy, and live video are excluded. |

### Dagu

| Question | Plain-language answer |
| --- | --- |
| What is it? | A scheduler and control panel for repeatable computer jobs, similar to a more visible and manageable version of the traditional cron scheduler. |
| What problem does it solve? | Scripts and scheduled jobs can fail silently, overlap, or become difficult to understand when their steps, retries, and history are scattered. |
| Who is it for? | Small engineering, operations, and data teams running recurring jobs on local or self-hosted computers. |
| What is it commonly used for? | Backups, data pipelines, scheduled reports, health checks, sensor jobs, and approved internal support tasks. |
| How does it work in practice? | A workflow file lists jobs and their order; Dagu starts them on schedule, records outcomes, retries allowed failures, and shows status in a web interface. |
| What would AI Lab build? | A comparison between Dagu's workflow states and one existing automation, illustrated with a mock event transcript rather than running Dagu. |
| What are the limitations? | It can execute powerful commands, remote connections, and containers. Real deployment needs access controls, and GPL/commercial terms need review. |

### AiderDesk

| Question | Plain-language answer |
| --- | --- |
| What is it? | A desktop workbench for organizing AI-assisted coding tasks in separate code copies, with review and approval controls before merging changes. |
| What problem does it solve? | AI coding work can mix unrelated tasks, lose context, or change files before a person has clearly reviewed the result. |
| Who is it for? | Software developers and engineering teams using coding assistants while retaining human review. |
| What is it commonly used for? | Separate feature tasks, code review, comparing approaches, managing repositories, and requiring approval before tool use. |
| How does it work in practice? | Each task gets an isolated Git worktree, meaning a separate code copy; an assistant proposes changes there and the user reviews them before merging. |
| What would AI Lab build? | A static wireflow showing task isolation, approvals, and review states using fictional repository data, without installing or connecting a model. |
| What are the limitations? | It is not a coding model. Real use needs repository access, providers, credentials, memory storage, and executable extensions. |

### LocalAI

| Question | Plain-language answer |
| --- | --- |
| What is it? | A self-hosted server that gives many kinds of AI models one common local interface instead of sending every request to a cloud provider. |
| What problem does it solve? | Different local models and runtimes use different setup and interfaces, making text, image, speech, and retrieval tools difficult to manage consistently. |
| Who is it for? | Developers and teams operating several AI capabilities on their own computers or private infrastructure. |
| What is it commonly used for? | Local chat, text generation, image or speech workflows, embeddings, reranking, and routing requests across local backends. |
| How does it work in practice? | It manages selected model backends and exposes one local interface; applications send requests there and LocalAI routes them to the appropriate capability. |
| What would AI Lab build? | A capability comparison and mock model-role/health dashboard showing useful ideas for the existing Ollama and LM Studio provider harness. |
| What are the limitations? | The full platform can manage downloads, backends, agents, fine-tuning, authentication, and distributed services, all excluded from this comparison. |

## Model Candidate Security Gate

| Candidate | Security review | Download approval | License review | Provenance | Isolation notes |
| --- | --- | --- | --- | --- | --- |
| Qwen3-Coder-Next-GGUF | `needs_review` | `not_approved` | `needs_review` | `source_metadata_only` | Prefer reviewed GGUF local runtime only after user approval. |
| Qwopus3.6-27B-Coder-MTP-4bit.mlx | `needs_review` | `not_approved` | `unknown` | `source_metadata_only` | Prefer reviewed MLX/MLX-LM path only after source and template review. |
| Phi-4-Reasoning-Vision-15B | `needs_review` | `not_approved` | `needs_review` | `source_metadata_only` | Keep on watchlist until a vision/retrieval-specific eval lane exists. |
| SmolLM3-3B-GGUF | `needs_review` | `not_approved` | `needs_review` | `source_metadata_only` | Prefer an exact reviewed GGUF through an existing stock local runtime. |
| Bonsai-27B-gguf | `needs_review` | `not_approved` | `needs_review` | `source_metadata_only` | Block custom forks/kernels pending a separate source/code review. |

## Project Priority Review

| Project | Priority score | Priority rationale | Business tie-in | Learning value | Local fit | Risk notes |
| --- | --- | --- | --- | --- | --- | --- |
| Raspberry Pi AI Camera + IMX500 Model Zoo | 5 | Strong AI Lab OS edge/portfolio fit with official docs and contained review scope. | Local wildlife monitor, workshop safety camera, inventory counter, or field logger. | Edge inference, camera pipelines, sensor logging, dashboard ingestion. | Excellent as a separate edge event-log lane. | No package/model/hardware setup is approved by radar. |
| Future AGI | 4 | Strong eval/observability reference, but full-stack platform risk. | Client-facing AI reliability workbench inspiration. | Draft scores, traces, guardrails, and review workflow design. | Self-hosting docs claim data can remain inside user's network. | Gateway/SDK/cloud-adjacent behavior needs boundary review. |
| rtl_433 | 4 | Strong passive SDR learning and local sensor dashboard fit. | Facilities monitoring, home-lab telemetry, field dashboards. | SDR basics, decoder metadata, evidence logging. | Strong if limited to legal passive reception. | Avoid protected communications, transmission, evasion, or offensive workflows. |
| mcp-agent | 4 | Strong MCP workflow learning value but not v0 runtime scope. | Auditable client automations and tool coordination patterns. | MCP agent workflow structure and human-in-loop mechanics. | Useful for SOP/design only. | Do not import into `src/local_ai_lab` v0 RAG runtime. |
| WildBridge | 3 | Interesting telemetry reference, but flight-control risk makes it review-heavy. | Passive flight-log and telemetry dashboard concept. | ROS2/mobile ground station architecture. | Reference only for local telemetry import artifacts. | Live command/control requires separate safety/legal review. |
| Dagu | 4 | Strong local workflow reliability reference with recent maintenance; executable steps and GPL embedding terms need review. | Governed internal automation or client operations console. | File-backed state, retries, concurrency, approvals, observability. | Strong as a design reference without runtime adoption. | Script, SSH, container, webhook, MCP, cloud, and license boundaries. |
| AiderDesk | 4 | Strong worktree/review UX reference; broad agent/provider surface remains outside scope. | Local engineering workbench or client change-review workflow. | Worktree isolation, approvals, task forks, context controls. | Useful dashboard/task design reference only. | Provider, repository, memory, extension, and subagent trust boundaries. |
| LocalAI | 3 | Strong runtime breadth, but far larger than the narrow provider harness. | Private multi-model gateway or inference operations concept. | Backend modularity, role routing, quotas, health, Apple Silicon. | Conceptual comparison only. | Automatic downloads, agents, fine-tuning, auth, APIs, and distributed services. |

## Project Cost Estimates

Cost ranges are planning metadata observed on 2026-07-18. They are not quotes,
purchase approval, or authorization to install or run software. Each estimate
prices the smallest credible, safe local MVP; software-only projects include DIY
time so a `$0` license is not presented as costless work.

| Project | Scoped MVP | Source checked | Price valid until | Existing-lab cash | From-scratch prototype | Portfolio build | DIY effort | Recurring cost | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Raspberry Pi AI Camera + IMX500 Model Zoo | One stock-model camera pipeline, local event log, and small dashboard. | 2026-07-18 | 2026-08-17 | $80-$100 if a compatible Pi, power, and storage are owned. | $155-$180 with a Pi 5 1GB, camera, power, and storage. | $195-$225 with Pi 5 2GB, cooling, case or mount. | 8-16 hours | $1-$3/month local power | Medium |
| Future AGI | Single-user self-hosted eval/observability stack using an existing local model endpoint. | 2026-07-18 | 2026-08-17 | $0-$25 on the Mac Studio. | $220-$350 for a dedicated 16 GB / 512 GB mini PC. | $300-$700 with stronger host, backup, and power protection. | 16-32 hours | $2-$6/month always-on power | Medium |
| mcp-agent | Separate local-only MCP workflow demo using deterministic fixtures or the existing local runtime. | 2026-07-18 | 2026-08-17 | $0-$25 on existing lab hardware. | $220-$350 for an isolated dedicated mini PC. | $250-$500 with backup and demo accessories. | 12-24 hours | $0-$6/month | Medium |
| rtl_433 | Legal passive receive-only sensor dashboard with one receiver and antenna. | 2026-07-18 | 2026-08-17 | $40-$80 when reusing the Mac and buying a receiver kit. | $125-$180 with a low-memory Pi host and receiver kit. | $175-$300 with upgraded antenna, enclosure, and one test sensor. | 10-20 hours | $1-$3/month local power | Medium |
| WildBridge | Passive recorded-telemetry/dashboard proof first; connected bench priced separately, with no live control approval. | 2026-07-18 | 2026-08-17 | $0-$50 for the passive proof. | $1,300-$1,550 for one connected DJI/Android bench. | $1,500-$2,100 with batteries, case, network, and spares. | 24-60 hours; connected hardware adds 20-40 | $2-$10/month, excluding insurance/permits | Low |
| Dagu | Documentation-only workflow-governance comparison and deterministic mock lifecycle. | 2026-07-18 | 2026-08-17 | $0-$25 on the existing Mac. | $220-$350 for a later isolated dedicated host. | $250-$500 with backup/power/presentation finish. | 8-16 hours | $0-$6/month | Medium |
| AiderDesk | No-install UX/architecture teardown and static approval-flow prototype. | 2026-07-18 | 2026-08-17 | $0-$25 on existing hardware. | $220-$350 for a later isolated demo host. | $250-$500 with backup and presentation finish. | 8-16 hours | $0-$6/month | Medium |
| LocalAI | Documentation-only capability-gap analysis against the current provider harness. | 2026-07-18 | 2026-08-17 | $0-$50 on the Mac Studio. | $220-$500 for a dedicated local host. | $500-$1,500 depending on compute/storage finish. | 16-40 hours | $0-$10/month | Low |

Raspberry Pi estimate assumptions and exclusions:

- The AI Camera is $70 MSRP and was observed at $74.95 from a Raspberry Pi
  approved US reseller. It includes the IMX500 accelerator and camera cables,
  so no separate AI HAT is included.
- The recommended host is the $65 Raspberry Pi 5 2GB. The estimate also uses a
  $12.95 official power supply and a $10.95 active cooler, plus allowances for
  microSD storage, a basic case or mount, tax, and shipping.
- Weatherproofing, battery or UPS power, custom fabrication, labor, replacement
  parts, and expedited shipping are excluded. A field-ready build would likely
  raise the total to roughly $250-$350, with low confidence until its deployment
  requirements are defined.
- The model zoo has no purchase price, but its models have mixed licenses. A
  project review must select and review the exact model license before any
  business-facing prototype.

Other project estimate assumptions and exclusions:

- Future AGI publishes a single-user minimum of 4 CPU cores, 8 GB RAM, and 20 GB
  disk. The dedicated-host estimate uses an observed $219 16 GB / 512 GB x86
  mini PC as its floor. It excludes cloud model providers, paid support,
  production redundancy, and labor valuation.
- mcp-agent is Apache-2.0. Its estimate assumes a separate local-only prototype
  with deterministic fixtures or an existing local model runtime; cloud
  inference, managed deployment, and credentialed third-party connectors are
  excluded.
- rtl_433 uses the vendor's $29.95 dongle-only or $39.95 antenna-kit observation.
  Host, upgraded antenna, enclosure, test sensor, tax, and shipping are planning
  allowances. The scope remains passive, legal, and receive-only.
- WildBridge's safe first project is recorded-telemetry analysis. The connected
  bench estimate uses a $759 DJI Mini 4 Pro package and a $499 Android phone.
  The exact controller/app combination is unresolved, and live flight, command,
  or autonomous control remains outside this approval.
- Dagu and AiderDesk estimates price documentation/static mock scopes on the
  existing Mac. Their dedicated-host scenarios reuse the observed $219 mini-PC
  floor but do not claim workload compatibility. Installers, providers,
  repositories, scripts, and workflow execution are excluded.
- LocalAI pricing is intentionally low-confidence because model roles, backends,
  context, concurrency, and storage can dominate hardware needs. The safe scope
  is architecture comparison only and excludes all backend/model retrieval,
  agents, fine-tuning, API exposure, and distributed services.

Price sources:

- [Raspberry Pi AI Camera](https://www.raspberrypi.com/products/ai-camera/)
- [Raspberry Pi February 2026 pricing](https://www.raspberrypi.com/news/more-memory-driven-price-rises/)
- [Raspberry Pi 5 2GB reseller observation](https://www.pishop.us/product/raspberry-pi-5-2gb/)
- [Official 27W power supply reseller observation](https://www.pishop.us/product/raspberry-pi-27w-usb-c-power-supply-black-us/)
- [Active Cooler reseller observation](https://www.pishop.us/product/raspberry-pi-active-cooler/)
- [Official IMX500 model zoo and license list](https://github.com/raspberrypi/imx500-models)
- [Future AGI self-host requirements](https://docs.futureagi.com/docs/self-hosting/requirements/)
- [Future AGI license and local-runtime metadata](https://github.com/future-agi/future-agi)
- [16 GB / 512 GB mini-PC price observation](https://store.minisforum.com/en-ph/products/minisforum-un100p)
- [mcp-agent license and runtime metadata](https://github.com/lastmile-ai/mcp-agent)
- [RTL-SDR Blog V4 price observation](https://www.rtl-sdr.com/rtl-sdr-blog-v4-dongle-initial-release/)
- [WildBridge prerequisites and supported hardware](https://github.com/WildDrone/WildBridge)
- [DJI Mini 4 Pro price observation](https://store.dji.com/product/dji-mini-4-pro)
- [Pixel 9a price observation](https://store.google.com/config/pixel_9a?hl=en-US)
- [Dagu license, release, and local workflow metadata](https://github.com/dagucloud/dagu)
- [AiderDesk license, release, worktree, and approval metadata](https://github.com/hotovo/aider-desk)
- [LocalAI license, release, Apple Silicon, and capability metadata](https://github.com/mudler/LocalAI)

Refresh reason for all eight projects is initial discovery and baseline pricing.
Refresh earlier than 2026-08-17 after a material release, license, maintenance,
compatibility, price, legal, or safety change. Otherwise, refresh public hardware
prices when the 30-day validity window expires.

## Effort-Versus-Value View

These are planning groups, not rankings. Cash, hours, learning value, business
value, and risk remain independent. Maximum DIY hours and the portfolio budget
are not yet confirmed in the local profile.

### Weekend Projects

| Project | Cash | DIY hours | Learning value | Business value | Risk |
| --- | --- | --- | --- | --- | --- |
| Raspberry Pi AI Camera + IMX500 Model Zoo | $80-$100 with compatible owned Pi; $155-$180 from scratch | 8-16 | Edge inference, camera/event pipelines | Strong visual portfolio demo | Privacy, model license, and hardware compatibility review |
| rtl_433 | $40-$80 existing lab; $125-$180 from scratch | 10-20 | Passive SDR and event normalization | Facilities/sensor dashboard concept | Legal receive-only scope required |
| mcp-agent design study | $0-$25 existing lab | 12-24 | MCP state, approval, and audit patterns | Auditable automation design artifact | Agent framework stays outside v0 runtime |
| Dagu design study | $0-$25 existing lab | 8-16 | Workflow states, retries, approvals, observability | Governed automation/product pattern | Executable steps and GPL embedding boundary |
| AiderDesk UX study | $0-$25 existing lab | 8-16 | Worktrees, tool approvals, diff review, task forks | Local engineering workbench concept | Broad provider/repository/extension boundary |

### Sub-$300 Builds

| Project | Cash | DIY hours | Learning value | Business value | Risk |
| --- | --- | --- | --- | --- | --- |
| Raspberry Pi AI Camera + IMX500 Model Zoo | $155-$225 depending on finish | 8-16 | Edge AI and local field systems | Strong resume-grade visual demo | Inventory/privacy/license checks |
| rtl_433 | $125-$300 depending on antenna and finish | 10-20 | Passive radio and sensor ingestion | Local monitoring prototype | Legal and private-activity boundaries |
| Future AGI design or basic host lane | $0-$25 existing lab; $220-$350 dedicated host | 16-32 | Eval review and observability architecture | AI reliability workbench concept | Full-stack/cloud-adjacent behavior |
| mcp-agent design or basic host lane | $0-$25 existing lab; $220-$350 dedicated host | 12-24 | MCP workflow design | Client automation patterns | v0 scope and credential boundaries |
| Dagu design or basic host lane | $0-$25 existing lab; $220-$350 dedicated host | 8-16 | Workflow reliability and recovery | Governed operations console | GPL and execution surface |
| AiderDesk design or basic host lane | $0-$25 existing lab; $220-$350 dedicated host | 8-16 | Coding-task isolation and review UX | Engineering workbench | Provider/repository/agent trust surface |

### Larger Portfolio Investments

| Project | Cash | DIY hours | Learning value | Business value | Risk |
| --- | --- | --- | --- | --- | --- |
| WildBridge connected bench | $1,300-$2,100 | 44-100 including connected work | Telemetry, mobile, ROS2 architecture | Distinctive passive flight-log dashboard | Highest physical, legal, compatibility, and control risk |
| Future AGI dedicated presentation build | $300-$700 | 16-32 | Eval/observability product architecture | Client-facing reliability workbench | Platform weight, telemetry, and cloud assumptions |
| LocalAI architecture/control-plane build | $500-$1,500 | 16-40 | Multi-runtime roles, routing, quotas, and health | Private inference operations concept | Automatic downloads, backends, agents, auth, and distributed scope |

## MVP Action Cards

### Future AGI

| Field | Value |
| --- | --- |
| One-week deliverable | No-install architecture comparison mapping Future AGI concepts to AI Lab OS draft/confirmed score boundaries. |
| Success criteria | Identifies reusable concepts, rejected dependencies, data boundaries, and one approval-sized follow-up. |
| Expected demo artifact | Sanitized Markdown comparison and mock evaluator-review flow. |
| Prerequisites | Approval for documentation-only review; no install, repository execution, or cloud-provider setup. |
| First three tasks | 1. Map public components. 2. Document local-first and confirmed-score gaps. 3. Draft comparison and approval task. |
| Blockers | Telemetry, privileged containers, x86/Rosetta assumptions, and v0 agent boundary. |
| Stop conditions | Stop if learning requires execution, credentials, privileged services, or v0 runtime adoption. |
| Safety notes | No SDK, gateway, provider, telemetry, credential, or container execution is approved. |

### mcp-agent

| Field | Value |
| --- | --- |
| One-week deliverable | No-install MCP workflow SOP using deterministic mock steps and explicit approvals. |
| Success criteria | Defines one bounded workflow, audit events, failure handling, credential boundaries, and post-v0 decision point. |
| Expected demo artifact | Sanitized sequence diagram and deterministic mock event transcript. |
| Prerequisites | Design-only approval; framework code remains outside `src/local_ai_lab`. |
| First three tasks | 1. Select one mock workflow. 2. Map state, approvals, and audit events. 3. Draft SOP and transcript. |
| Blockers | Agent orchestration is excluded from v0; provider credentials and connectors are out of scope. |
| Stop conditions | Stop if installation, cloud inference, credentials, or a v0 dependency is required. |
| Safety notes | No framework import, tool execution, cloud call, secret, or MCP server install is approved. |

### Raspberry Pi AI Camera + IMX500 Model Zoo

| Field | Value |
| --- | --- |
| One-week deliverable | No-install project brief, reviewed BOM, edge-event schema, and mock dashboard data for one stock-model use case. |
| Success criteria | Selects one use case/model license, distinguishes owned and required hardware, and defines demo acceptance criteria. |
| Expected demo artifact | Sanitized mock event log plus dashboard wireframe or static report. |
| Prerequisites | Confirm Pi/camera inventory, approve project lane, and review the exact model-zoo license. |
| First three tasks | 1. Confirm inventory/use case. 2. Review model license and event schema. 3. Draft BOM, mock data, and acceptance brief. |
| Blockers | Pi inventory, deployment environment, privacy expectations, and exact model are unconfirmed. |
| Stop conditions | Stop for incompatible license, budget overrun, or a biometric-surveillance use case. |
| Safety notes | No deployment, download, facial recognition, biometric identification, covert monitoring, or purchase is approved. |

### rtl_433

| Field | Value |
| --- | --- |
| One-week deliverable | Passive-only SDR brief, sanitized sensor schema, mock dataset, and dashboard acceptance plan. |
| Success criteria | Limits scope to legal public sensor broadcasts and defines a no-reception mock-data demo. |
| Expected demo artifact | Synthetic sensor events and static local dashboard/report mockup. |
| Prerequisites | Confirm local law/policy, receiver inventory, allowed sensor class, and receive-only scope. |
| First three tasks | 1. Define allowed sensor/legal check. 2. Specify schema/mock records. 3. Draft brief and stop conditions. |
| Blockers | Jurisdiction, target sensor class, antenna needs, and SDR inventory. |
| Stop conditions | Stop for transmission, protected communications, access controls, evasion, or identifiable private activity. |
| Safety notes | No interception, decryption, transmission, exploitation, or live collection is approved. |

### WildBridge

| Field | Value |
| --- | --- |
| One-week deliverable | Passive flight-log schema, synthetic fixtures, and telemetry dashboard brief with no live drone connection. |
| Success criteria | Uses only approved synthetic/sanitized records, documents provenance, and excludes control/live video. |
| Expected demo artifact | Synthetic telemetry log and static local flight-summary dashboard/report mockup. |
| Prerequisites | Approve passive log analysis, identify sanitized data, and exclude flight/controller integration. |
| First three tasks | 1. Define passive schema. 2. Create synthetic records/privacy rules. 3. Draft dashboard and review questions. |
| Blockers | Sanitized telemetry, controller compatibility, legal requirements, and hardware inventory. |
| Stop conditions | Stop if live flight, control, autonomy, public video, credentials, or purchase is required. |
| Safety notes | No flight, live connection, command/control, autonomy, video publishing, or purchase is approved. |

### Dagu

| Field | Value |
| --- | --- |
| One-week deliverable | No-install workflow-governance comparison and deterministic mock lifecycle for one AI Lab OS automation. |
| Success criteria | Maps states, retries, concurrency, approvals, audit events, and failure recovery to current boundaries. |
| Expected demo artifact | Sanitized state diagram and mock JSONL/Markdown workflow event transcript. |
| Prerequisites | Approve documentation-only review and select one non-sensitive automation case. |
| First three tasks | 1. Map public workflow concepts. 2. Define mock states/failures/retries/approvals. 3. Draft comparison and follow-up. |
| Blockers | GPL embedding posture, executable-step breadth, MCP controls, and managed/cloud boundaries. |
| Stop conditions | Stop if installation, execution, credentials, SSH, containers, webhooks, or runtime adoption are required. |
| Safety notes | No installer, binary, workflow, script, container, SSH, webhook, MCP, credential, or managed service use is approved. |

### AiderDesk

| Field | Value |
| --- | --- |
| One-week deliverable | Static coding-task approval-flow comparison covering worktrees, diff review, task forks, and context controls. |
| Success criteria | Identifies three reusable UX patterns, rejected runtime assumptions, and one dashboard-sized follow-up. |
| Expected demo artifact | Sanitized wireflow and mock task/review transcript using fictional repository data. |
| Prerequisites | Approve design-only review and define the current task/review flow being compared. |
| First three tasks | 1. Map controls to current task states. 2. Threat-model provider/repository/memory/extension boundaries. 3. Draft wireflow. |
| Blockers | No approved need for a second coding-agent UI; provider, memory, extension, and repository boundaries remain broad. |
| Stop conditions | Stop if installation, repository attachment, credentials, vector indexing, extension code, or agent execution are required. |
| Safety notes | No download, launch, repository access, provider connection, secret, extension, tool call, or agent action is approved. |

### LocalAI

| Field | Value |
| --- | --- |
| One-week deliverable | No-install capability-gap matrix between LocalAI and the current Ollama/LM Studio provider harness. |
| Success criteria | Separates useful provider-control concepts from rejected model-management, agent, fine-tuning, auth, and distributed features. |
| Expected demo artifact | Sanitized architecture diagram and mock model-role/health dashboard data. |
| Prerequisites | Approve documentation-only comparison and define the provider-harness questions. |
| First three tasks | 1. Inventory public capabilities/current boundaries. 2. Classify useful/redundant/prohibited features. 3. Draft matrix and follow-up. |
| Blockers | Backend supply chain, automatic downloads, API/auth behavior, telemetry, and production hardening. |
| Stop conditions | Stop if installation, backend/model retrieval, fine-tuning, agents, keys, public endpoints, or distributed services are required. |
| Safety notes | No platform/backend/model download, quantization, fine-tuning, agent, API, key, public endpoint, or distributed execution is approved. |

## Ready For Eval

None. External model candidates are metadata-only and default to
`download_approval=not_approved`. They need explicit approval before registry
entry, artifact review, or local benchmark work.

## Watchlist

| Candidate | Reason | Revisit trigger |
| --- | --- | --- |
| Qwopus3.6-27B-Coder-MTP-4bit.mlx | Interesting MLX coding-agent artifact, but source chain and template changes are unresolved. | User approves a security/provenance review for this exact artifact. |
| Phi-4-Reasoning-Vision-15B | Official compact multimodal model, but current harness is text-first. | AI Lab OS adds a vision/retrieval-specific evaluation lane. |
| mcp-agent | Useful MCP workflow reference, but not a v0 runtime dependency. | User asks for an agent workflow SOP or post-v0 integration review. |
| WildBridge | Useful drone telemetry reference, but live-control risk is high. | User asks for passive flight-log parsing or telemetry dashboard design only. |
| AiderDesk | Useful worktree/review UX reference, but broad agent/provider/repository scope. | User approves a design-only coding-task UX comparison. |

## Import Or Task Notes

- Registry updates: none. Do not edit `data/model_registry/candidates.csv` or
  `data/project_registry/github_repos.csv` without explicit approval.
- Benchmark follow-ups: SmolLM3-3B-GGUF is the most practical new baseline, but
  it still needs exact Q4 artifact/hash, Jinja template, local runner, and
  execution approval before `evals/local-llm-benchmark/SPEC.md` work.
- Dashboard follow-ups: no dashboard import was created. The local dashboard
  link is [Radar candidates](http://127.0.0.1:8765/radar) when the dashboard is
  running.
- Next approval task: choose one item to approve for a focused registry-review
  packet. Best first choices are `20260718-raspberry-pi-ai-camera-imx500` or
  `20260718-dagu-workflow-engine` for a project lane, and
  `20260718-smollm3-3b-gguf` for a compact model security review.

## Safety Posture

This run used public metadata discovery only. It did not clone repositories,
download packages or models, install software, run models, run repository code,
run model-card code, call inference APIs, add SDK/API clients, use API keys,
use secrets, create install instructions, add dependencies, create eval scores,
or write dashboard/model/project registry rows.

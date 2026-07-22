# AI Lab Radar Report

Date: 2026-07-22
Reviewer: Codex automation
Source packet: `automations/ai-lab-radar/inputs/2026-07-22-daily-external-radar.md`
Approved for radar review: no
Safe to commit: no
Dashboard: [Radar candidates](http://127.0.0.1:8765/radar) after starting the
local dashboard.

## Summary

- Public metadata items reviewed: 35; high-signal new items reported: 5.
- Ready for evaluation: 0 model candidates.
- Ready for design review: 3 project opportunities.
- Needs more information: 2 project opportunities.
- Best immediate project: OpenTelemetry GenAI trace privacy map at $0
  incremental cash and 8-14 DIY hours.
- Strongest policy task: ToolHive MCP trust-policy crosswalk at $0 incremental
  cash and 10-18 DIY hours.
- Largest portfolio investment: Reachy Mini planning is $0, while a later
  physical build is estimated at $425-$700 before unresolved shipping and tax.
- No registry, benchmark, score, dashboard, installation, Growth, purchase, or
  runtime decision was made.

## Delta Summary

| Item | Type | Status | First seen | Last seen | Change summary |
| --- | --- | --- | --- | --- | --- |
| OpenTelemetry GenAI trace privacy map | project_opportunity | `new` | 2026-07-22 | 2026-07-22 | First radar appearance of the dedicated semantic-conventions project as a trace-privacy and evidence mapping opportunity. |
| ToolHive MCP trust-policy crosswalk | project_opportunity | `new` | 2026-07-22 | 2026-07-22 | First radar appearance; the 2026-07-20 release provides current registry, skill-schema, authorization, audit, and runtime concepts. |
| Langfuse local observability architecture review | project_opportunity | `new` | 2026-07-22 | 2026-07-22 | First radar appearance of Langfuse as a local observability product and architecture reference. |
| QGroundControl offline flight-review storyboard | project_opportunity | `new` | 2026-07-22 | 2026-07-22 | First radar appearance, narrowed to synthetic offline review because the upstream product has vehicle-control authority. |
| Reachy Mini local interaction portfolio build | project_opportunity | `new` | 2026-07-22 | 2026-07-22 | First radar appearance with a Mac-powered Lite path, regional price evidence, and explicit motion, media, app, and license risks. |

No unchanged prior item was repeated. Twenty Hugging Face entries were reviewed,
but none established a sufficiently practical exact artifact, provenance path,
compatible local runtime, and specific benchmark gap.

## Candidate Review

| Candidate | Source | Why interesting | Risk notes | Recommended next step |
| --- | --- | --- | --- | --- |
| OpenTelemetry GenAI trace privacy map | [Official repository](https://github.com/open-telemetry/semantic-conventions) | Could give the benchmark, RAG harness, and dashboard one evidence vocabulary with explicit privacy defaults. | Standard fields may expose prompts, chunks, tools, files, identifiers, and exception text; conventions are still evolving. | `ready_for_review`: static 20-field privacy map only. |
| ToolHive MCP trust-policy crosswalk | [Official repository](https://github.com/stacklok/toolhive) | Its registry, runtime, gateway, and portal layers can test whether radar and Growth authority boundaries are complete. | Upstream installs, builds, runs, proxies, authenticates, and observes servers; catalog presence never grants trust. | `ready_for_review`: static policy crosswalk only, with no installation authority. |
| Langfuse local observability architecture review | [Official repository](https://github.com/langfuse/langfuse) | Mature trace, dataset, prompt, and evaluation UX can inform smaller AI Lab dashboard improvements. | Heavy storage stack, credentials, migrations, telemetry, retention, open-core boundaries, and sensitive traces. | `needs_more_info`: telemetry, retention, license, and minimum-stack review. |
| QGroundControl offline flight-review storyboard | [Official repository](https://github.com/mavlink/qgroundcontrol) | A clear field-operations portfolio artifact can be designed without a real drone or flight. | Full upstream authority includes missions, vehicle configuration, telemetry, video, and control; latest stable release is from 2025. | `ready_for_review`: synthetic static after-action storyboard only. |
| Reachy Mini local interaction portfolio build | [Official repository](https://github.com/pollen-robotics/reachy_mini) | A physical expressive robot could become a distinctive staged local-first portfolio project. | Purchase, moving hardware, camera, microphones, apps, models, regional prices, and separate hardware terms require review. | `needs_more_info`: no-purchase decision packet first. |

## Model Practicality

No model candidate cleared today's threshold. The review included compact
robotics and speech models, large official families, and community GGUF or MLX
derivatives. Custom execution paths, role mismatch, impractical size,
derivative provenance, prior-family overlap, and missing benchmark fixtures
prevented a candidate record. No artifact size, disk, memory, runtime,
download, or benchmark proposal was created.

## Project Explainers

### OpenTelemetry GenAI trace privacy map

| Question | Plain-language answer |
| --- | --- |
| What is it? | OpenTelemetry Semantic Conventions provide shared names for recording what software did, how long it took, and what failed. The generative AI section covers model requests, retrieval, tools, agents, and evaluations. |
| What problem does it solve? | Traces are difficult to compare or protect when each application uses different field names or mixes safe operational facts with private prompts and tool data. |
| Who is it for? | Developers, observability teams, security reviewers, and product teams designing repeatable AI evidence. |
| What is it commonly used for? | Naming model and retrieval work, recording timing and token counts, tracing tool calls, representing evaluations, and documenting disabled content fields. |
| How does it work in practice? | An application records structured events with agreed field names. A viewer can group related work, compare timings, and apply privacy rules consistently. |
| What would AI Lab build? | A static map from current evidence to 20 standard fields, each labeled allow, redact, local-only, or prohibit. Three invented traces would demonstrate the policy without collecting telemetry. |
| What are the limitations? | Shared names do not guarantee safe collection, the AI conventions are evolving, and content, tool, exception, or file fields can contain private information. |

### ToolHive MCP trust-policy crosswalk

| Question | Plain-language answer |
| --- | --- |
| What is it? | ToolHive is a platform for cataloging, approving, running, and controlling Model Context Protocol servers, which let AI assistants use external tools. |
| What problem does it solve? | Teams need to separate discovering a tool from trusting it, then control what an approved tool can access or do. |
| Who is it for? | AI platform teams, security engineers, administrators, and developers managing tool integrations. |
| What is it commonly used for? | Curating catalogs, checking provenance, assigning permissions, isolating servers, auditing access, and exposing approved tools through a gateway. |
| How does it work in practice? | The upstream platform can discover entries, verify metadata, install or launch servers, proxy connections, enforce policy, store secrets, and record activity. |
| What would AI Lab build? | A paper comparison between ToolHive's registry, runtime, gateway, and portal layers and AI Lab's radar, reviewed Growth policy, official-host command allowlist, and rollback evidence. |
| What are the limitations? | A platform does not make its catalog trustworthy. Containers, package managers, credentials, remote servers, cloud interfaces, and one-click installation remain sensitive authority boundaries. |

### Langfuse local observability architecture review

| Question | Plain-language answer |
| --- | --- |
| What is it? | Langfuse is a workspace for recording and reviewing AI traces, prompts, datasets, quality checks, costs, and feedback. |
| What problem does it solve? | AI debugging evidence becomes scattered when prompts, retrieved material, model calls, scores, and feedback live in different systems. |
| Who is it for? | AI product teams, developers, quality reviewers, and operations teams. |
| What is it commonly used for? | Inspecting traces, comparing prompt versions, managing evaluation datasets, reviewing feedback, and monitoring failures or costs. |
| How does it work in practice? | Applications send events to web and worker services, which store records across PostgreSQL, ClickHouse, Redis or Valkey, and object storage for dashboard review. |
| What would AI Lab build? | A static architecture and feature comparison, followed by two smaller dashboard concepts that preserve local evidence and confirmed-score rules. |
| What are the limitations? | The self-hosted stack is heavy, some features need providers, open-source telemetry is enabled by default, and retention or enterprise features vary by edition. |

### QGroundControl offline flight-review storyboard

| Question | Plain-language answer |
| --- | --- |
| What is it? | QGroundControl is an application for planning drone missions, configuring vehicles, watching telemetry, viewing maps and video, and reviewing flight information. |
| What problem does it solve? | Drone operations are difficult to understand when routes, warnings, positions, batteries, and operator actions are scattered across screens and logs. |
| Who is it for? | Drone pilots, field teams, developers, educators, and mission reviewers. |
| What is it commonly used for? | Planning routes, configuring vehicles, monitoring battery and position, viewing camera feeds, and reviewing telemetry. |
| How does it work in practice? | The full application connects to a compatible vehicle or recording and presents maps, instruments, mission steps, parameters, alerts, and media together. |
| What would AI Lab build? | A static six-screen review for one invented survey flight, including preflight evidence, timeline, map, alert, battery, and after-action views. |
| What are the limitations? | A storyboard cannot validate aircraft behavior. Real use involves safety-critical control, radio links, maps, video, precise locations, and platform binaries. |

### Reachy Mini local interaction portfolio build

| Question | Plain-language answer |
| --- | --- |
| What is it? | Reachy Mini is a small expressive desktop robot with moving head parts, a camera, microphones, and a speaker. Its Lite version uses an external Mac or Linux computer. |
| What problem does it solve? | Software-only demos do not show how people understand motion, attention, timing, sound, and physical presence during an interaction. |
| Who is it for? | Robotics learners, educators, human-computer interaction researchers, AI demo builders, and portfolio developers. |
| What is it commonly used for? | Learning robot motion, prototyping expressive interfaces, testing local media concepts, demonstrating interaction, and building educational apps. |
| How does it work in practice? | The kit is assembled, connected to local compute, and controlled through software that can move motors and access camera, microphone, speaker, and optional AI apps. |
| What would AI Lab build? | First, a no-purchase safety and interaction design. A later separately approved Lite build would start with typed local commands and motion only, with camera, microphones, apps, and models disabled. |
| What are the limitations? | It has no arms or locomotion, requires assembly, introduces moving hardware and media privacy, and its apps can add downloads, credentials, cloud calls, and broader authority. |

## Project Priority Review

| Project | Priority | Business value | Learning value | Local fit | Risk notes | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| OpenTelemetry GenAI trace privacy map | 5 | High governance and product value | High | High for static mapping | Sensitive content, evolving fields, retention and logging boundaries | `ready_for_review` |
| ToolHive MCP trust-policy crosswalk | 5 | High automation governance value | High | High for static policy work | Installation, packages, containers, secrets, remote servers, authority confusion | `ready_for_review` |
| Langfuse local observability architecture review | 3 | High product-reference value | High | Medium direct, high as reference | Heavy stack, telemetry, credentials, retention, open-core boundaries | `needs_more_info` |
| QGroundControl offline flight-review storyboard | 3 | Medium-high portfolio and field-ops value | High | High for static design | Safety-critical control, locations, video, stale stable release | `ready_for_review` |
| Reachy Mini local interaction portfolio build | 4 | High portfolio and interaction value | High | Good Lite path after review | Hardware motion, privacy, purchase, regional pricing, apps and models | `needs_more_info` |

## Project Cost Estimates

| Project | Cost scope | Cost as of | Source checked | Price valid until | Incremental cost | From-scratch prototype | Portfolio build | DIY effort | Recurring cost | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpenTelemetry GenAI trace privacy map | Static field map, privacy dispositions, synthetic traces, and evidence card | 2026-07-22 | 2026-07-22 | 2026-08-21 | $0 | $0-$25 | $0-$100 | 8-14h | $0/month | High cash, Medium effort |
| ToolHive MCP trust-policy crosswalk | Static architecture, authority, immutable-source, and rollback comparison | 2026-07-22 | 2026-07-22 | 2026-08-21 | $0 | $0-$25 | $0-$100 | 10-18h | $0/month | High cash, Medium effort |
| Langfuse local observability architecture review | Public architecture and feature review plus two static screens | 2026-07-22 | 2026-07-22 | 2026-08-21 | $0 | $0-$25 | $0-$125 | 12-20h | $0/month | High cash, Medium effort |
| QGroundControl offline flight-review storyboard | Static six-screen synthetic after-action review | 2026-07-22 | 2026-07-22 | 2026-08-21 | $0 | $0-$25 | $0-$125 | 10-18h | $0/month | High cash, Medium effort |
| Reachy Mini local interaction portfolio build | $0 decision week; later Lite physical MVP using confirmed Mac | 2026-07-22 | 2026-07-22 | 2026-08-05 | $0 planning; $399-$499 later kit | $425-$575 plus unresolved shipping and tax | $475-$700 | 16-30h | $0/month local motion-only | Medium |

Cost assumptions and exclusions:

- The four software and design projects reuse the confirmed Mac, existing
  editor, and existing local design tools. They exclude implementation,
  packages, services, containers, telemetry, and private data.
- Reachy Mini pricing uses current official regional pages. The Lite path can
  reuse confirmed Mac compute, but no owned robot, tools, workspace, or
  accessories are assumed.
- Reachy Mini shipping, tax, duties, lead time, replacement parts, camera or
  audio use, apps, models, and cloud services are excluded. A price refresh is
  due within 14 days because regional availability and pricing differ.
- No estimate authorizes purchase, installation, Growth mutation, device
  control, telemetry, flight, model execution, or data collection.

Price sources:

- OpenTelemetry: https://github.com/open-telemetry/semantic-conventions,
  checked 2026-07-22.
- ToolHive: https://github.com/stacklok/toolhive, checked 2026-07-22.
- Langfuse: https://github.com/langfuse/langfuse and
  https://langfuse.com/self-hosting, checked 2026-07-22.
- QGroundControl: https://github.com/mavlink/qgroundcontrol, checked
  2026-07-22.
- Reachy Mini: https://reachy-mini.ai/ and
  https://store.pollen-robotics.com/, checked 2026-07-22.

Refresh notes:

- Refresh software planning estimates by 2026-08-21 or earlier after a
  material license, release, telemetry, retention, authority, or architecture
  change. Refresh Reachy Mini pricing by 2026-08-05 or earlier after regional
  price, stock, shipping, terms, kit contents, or compatibility changes.

## Effort-Versus-Value View

The groups show independent planning dimensions. They are not rankings,
composite scores, ROI, or purchasing recommendations.

### Weekend Projects

| Project | Cash | DIY hours | Learning value | Business value | Risk |
| --- | --- | --- | --- | --- | --- |
| OpenTelemetry GenAI trace privacy map | $0 incremental | 8-14h | High | High | Medium: sensitive fields and evolving standard |
| ToolHive MCP trust-policy crosswalk | $0 incremental | 10-18h | High | High | Medium-high: authority and supply-chain boundaries |
| QGroundControl offline flight-review storyboard | $0 incremental | 10-18h | High | Medium-high | Medium: control-domain accuracy and stale stable release |

### Sub-$300 Builds

| Project | Cash | DIY hours | Learning value | Business value | Risk |
| --- | --- | --- | --- | --- | --- |
| OpenTelemetry GenAI trace privacy map | $0-$100 portfolio scope | 8-14h | High | High | Medium |
| ToolHive MCP trust-policy crosswalk | $0-$100 portfolio scope | 10-18h | High | High | Medium-high |
| Langfuse local observability architecture review | $0-$125 portfolio scope | 12-20h | High | High | High until architecture and telemetry review |
| QGroundControl offline flight-review storyboard | $0-$125 portfolio scope | 10-18h | High | Medium-high | Medium |
| Reachy Mini decision packet only | $0 planning cash | 6-10h of the total | Medium-high | High | High until budget, price, privacy, and safety review |

### Larger Portfolio Investments

| Project | Cash | DIY hours | Learning value | Business value | Risk |
| --- | --- | --- | --- | --- | --- |
| Reachy Mini local interaction portfolio build | $425-$575 physical prototype; $475-$700 polished build | 16-30h | High | High | High: purchase, motion, media privacy, apps, models, regional terms |

## MVP Action Cards

### OpenTelemetry GenAI trace privacy map

| Field | Value |
| --- | --- |
| One-week deliverable | Twenty-field crosswalk with allow, redact, local-only, and prohibit dispositions plus three synthetic traces. |
| Success criteria | Every field has a purpose, source, privacy disposition, retention note, and rule preventing prompts, chunks, secrets, or private paths from entering default logs. |
| Expected demo artifact | Markdown field map and static dashboard evidence-card mockup. |
| Prerequisites | Approval for documentation only and selection of three synthetic workflow shapes. |
| First three tasks | 1. Inventory current benchmark and RAG evidence fields. 2. Map 20 fields and privacy dispositions. 3. Draft synthetic traces and evidence card. |
| Blockers | Retention, field ownership, and whether later implementation needs an architecture decision record. |
| Stop conditions | Stop before instrumentation, real-trace collection, private-content logging, telemetry export, dependencies, or runtime changes. |
| Safety notes | Synthetic documentation only; no telemetry, prompt, chunk, tool result, path, collector, exporter, server, package, or execution. |

### ToolHive MCP trust-policy crosswalk

| Field | Value |
| --- | --- |
| One-week deliverable | Four-layer crosswalk, authority matrix, immutable-source checklist, rollback checklist, and one synthetic server-review record. |
| Success criteria | Reviewers can distinguish discovery from approval, policy from inventory, official-host execution from forbidden fallbacks, and qualification from installation authority. |
| Expected demo artifact | Markdown policy map and static approval-flow diagram. |
| Prerequisites | Approval for documentation only and confirmation that Growth policy remains the sole installation authority. |
| First three tasks | 1. Map registry, runtime, gateway, and portal layers. 2. Compare each with radar and Growth authority. 3. Draft synthetic approval and rollback records. |
| Blockers | Ownership between radar and Growth documentation and final document location. |
| Stop conditions | Stop before installing ToolHive, reading host inventory, mutating a skill, plugin, server, or connector, running package managers or containers, using credentials, or changing Growth policy. |
| Safety notes | Static metadata only; radar grants no installation, removal, enablement, inventory, package, container, credential, gateway, or execution authority. |

### Langfuse local observability architecture review

| Field | Value |
| --- | --- |
| One-week deliverable | Architecture and feature-gap matrix, telemetry and retention review, and two static dashboard concepts. |
| Success criteria | Reviewers can identify useful features, excluded infrastructure, privacy differences, score conflicts, and whether either screen belongs on the roadmap. |
| Expected demo artifact | Markdown architecture review and two static dashboard mockups. |
| Prerequisites | Selection of two AI Lab workflows and approval for public-metadata design work only. |
| First three tasks | 1. Map services, storage, telemetry, and editions. 2. Compare trace, dataset, prompt, and score workflows. 3. Draft two smaller local-first screens. |
| Blockers | Preferred workflows, retention requirements, portfolio budget, and maximum DIY hours. |
| Stop conditions | Stop before containers, credentials, providers, trace ingestion, prompt storage, telemetry, dependencies, or dashboard code changes. |
| Safety notes | Static metadata only; no service, database, container, credential, model, provider, telemetry, trace, prompt, private data, installation, migration, or execution. |

### QGroundControl offline flight-review storyboard

| Field | Value |
| --- | --- |
| One-week deliverable | Six-screen after-action storyboard with mission, map, timeline, battery, alert, evidence, and uncertainty views. |
| Success criteria | A non-technical reviewer can explain the planned route, synthetic event, evidence, operator decision, and uncertainty without implying a real flight. |
| Expected demo artifact | Click-through static mockup or slide sequence with narrated review. |
| Prerequisites | Approval for static design and selection of one invented survey scenario. |
| First three tasks | 1. Define the synthetic mission and review question. 2. Draft map, timeline, battery, alert, and evidence states. 3. Add provenance and no-control labels. |
| Blockers | Target industry, map style, presentation format, maximum DIY hours, and portfolio location. |
| Stop conditions | Stop before installation, maps or logs, simulation, vehicle connection, radio, real mission planning, precise locations, or flight. |
| Safety notes | Static synthetic review only; no app, map service, log, simulator, drone, controller, radio, video, telemetry, mission, flight, or control. |

### Reachy Mini local interaction portfolio build

| Field | Value |
| --- | --- |
| One-week deliverable | No-purchase decision packet with interaction storyboard, workspace plan, privacy states, motion limits, acceptance checklist, refreshed landed-cost worksheet, and go or no-go recommendation. |
| Success criteria | The packet identifies exact kit and price, workspace and supervision, motion limits, media defaults, power-off steps, excluded apps and models, and a budget decision. |
| Expected demo artifact | Static interaction storyboard, tabletop layout, safety checklist, and priced decision sheet; no robot required. |
| Prerequisites | Confirm portfolio budget, maximum DIY hours, region without storing an address, tools, tabletop space, and comfort with a media-capable device. |
| First three tasks | 1. Refresh regional kit price, contents, terms, and lead time without entering a cart. 2. Draft motion and acceptance limits. 3. Complete privacy, workspace, cost, and go or no-go review. |
| Blockers | Budget, DIY hours, tools, region, shipping and tax, workspace, supervision, media policy, and exact kit terms. |
| Stop conditions | Stop before a cart, personal data, purchase, installation, app or skill enablement, model download, hardware connection, motor power, camera, microphone, or unresolved terms. |
| Safety notes | Planning only; no cart, personal data, purchase, shipment, assembly, power, motion, media, app, skill, plugin, connector, model, installation, cloud call, credential, or control. |

## Ready For Eval

No model candidate is ready for evaluation. No item was connected to
`evals/local-llm-benchmark/SPEC.md` or `skills/local-llm-eval`.

## Watchlist

| Candidate | Reason | Retest or revisit trigger |
| --- | --- | --- |
| Langfuse local observability architecture review | Strong product reference, but the minimum stack, telemetry, retention, credentials, and open-core boundaries are broader than the current dashboard. | Revisit after the static architecture review or a material license, telemetry, retention, or deployment change. |
| Reachy Mini local interaction portfolio build | Strong physical portfolio potential, but the budget, landed price, workspace, media privacy, physical limits, and kit terms are unresolved. | Revisit after profile confirmation and a no-purchase decision packet with refreshed regional pricing. |
| NVIDIA Nemotron embedding family | Retrieval role is relevant, but today's visible BF16 entry lacked a reviewed local artifact and retrieval-specific benchmark gap. | Revisit when an exact local-compatible artifact and retrieval evaluation specification exist. |

## Skips

| Candidate | Reason |
| --- | --- |
| Remaining 19 Hugging Face entries | Impractical size, custom task/runtime, derivative provenance, prior-family overlap, or no distinct benchmark gap. |
| MCP Inspector and Microsoft MCP Gateway | Direct server exercise or Kubernetes and cloud scope is broader than today's static ToolHive policy comparison. |
| Opik, Phoenix, Ragas, and Open RAG Eval | Framework, provider, model-judge, hosted, or prior-review overlap offers less immediate value than the selected standards map. |
| MAVSDK, Open-RMF, Aerostack2, and RViz | Live control authority or Robot Operating System 2 dependency scope exceeds the QGroundControl static review MVP. |

## Import Or Task Notes

- Registry updates: none; model and project registry CSVs were not edited.
- Benchmark follow-ups: none; no model candidate cleared the threshold.
- Dashboard follow-ups: none; all screen ideas remain static action cards.
- Growth authority: unchanged. Radar discovery and ToolHive metadata grant no
  skill, plugin, Model Context Protocol server, or connector mutation rights.
- Profile fields needing confirmation: maximum DIY hours, portfolio investment
  budget, and Raspberry Pi, radio, drone, controller, camera, sensor, robotics,
  workspace, and tool inventory.
- Best next approval task: approve or decline the OpenTelemetry 20-field trace
  privacy map. The ToolHive crosswalk is the second recommended task.

## Safety Posture

- Metadata-only boundaries: 35 public items were reviewed. No repository,
  package, model, model-card code, binary, map, log, simulator, server, app, or
  device was downloaded, installed, opened, or executed.
- Registry and evidence changes: none. No score, benchmark, final label,
  dashboard decision, Growth policy, purchase, or registry row was created.
- Skills, plugins, servers, and connectors: none were installed, removed,
  enabled, disabled, inventoried, or mutated. Radar has no such authority.
- APIs and secrets: no inference or hosted service was called; no credential,
  token, key, environment file, personal data, cart, or checkout was used.
- Physical and radio safety: no purchase, shipment, assembly, powered motion,
  camera, microphone, vehicle connection, map retrieval, live telemetry,
  simulation, mission planning, flight, control, reception, or transmission.
- Privacy: the ignored local profile informed only planning assumptions; no
  private inventory detail, path, prompt, response, trace, or benchmark
  artifact was copied into this report.
- Cost estimates and action cards are planning records only and do not
  authorize spending, installation, execution, mutation, data collection, or
  registry entry.

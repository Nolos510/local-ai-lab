# AI Lab Radar Report

Date: 2026-07-21
Reviewer: Codex automation
Source packet: `automations/ai-lab-radar/inputs/2026-07-21-daily-external-radar.md`
Approved for radar review: no
Safe to commit: no
Dashboard: [Radar candidates](http://127.0.0.1:8765/radar) after starting the
local dashboard.

## Summary

- Public metadata items reviewed: 39; high-signal new items reported: 5.
- Ready for evaluation: 0 model candidates.
- Ready for design review: 4 project opportunities.
- Needs more information: 1 project opportunity.
- Best immediate task: Cisco MCP Scanner static security review at $0
  incremental cash and 8-14 DIY hours.
- Best low-effort foundation: MCAP robotics log catalog at $0 incremental cash
  and 6-10 DIY hours.
- No candidate, registry, benchmark, dashboard, download, install, execution,
  credential, or purchase decision was made.

## Delta Summary

| Item | Type | Status | First seen | Last seen | Change summary |
| --- | --- | --- | --- | --- | --- |
| Cisco MCP Scanner static security review | project_opportunity | `new` | 2026-07-21 | 2026-07-21 | First radar appearance of a Model Context Protocol security-review reference with static and connected modes requiring distinct trust boundaries. |
| MCAP robotics log catalog | project_opportunity | `new` | 2026-07-21 | 2026-07-21 | First radar appearance of a standard robotics recording container and evidence-catalog opportunity. |
| Rerun robotics visualization storyboard | project_opportunity | `new` | 2026-07-21 | 2026-07-21 | First radar appearance of a multimodal robotics timeline and incident-review design opportunity. |
| DeepEval RAG metric crosswalk | project_opportunity | `new` | 2026-07-21 | 2026-07-21 | First radar appearance of this evaluation framework, limited to a no-score metric crosswalk. |
| Kiln local AI workbench comparison | project_opportunity | `new` | 2026-07-21 | 2026-07-21 | First radar appearance of this local-first workbench as a product-reference comparison. |

No unchanged prior project was repeated. The 30 recently modified GGUF entries
did not clear the provenance, role, local-runtime, and benchmark-gap threshold.

## Candidate Review

| Candidate | Source | Why interesting | Risk notes | Recommended next step |
| --- | --- | --- | --- | --- |
| Cisco MCP Scanner static security review | [Official GitHub repository](https://github.com/cisco-ai-defense/mcp-scanner) | Provides a concrete vocabulary for reviewing tool authority, prompt injection, packages, secrets, and network paths. | Upstream modes can launch servers, fetch packages, accept tokens, or use a hosted analyzer. | `ready_for_review`: static taxonomy and synthetic descriptors only. |
| MCAP robotics log catalog | [Official GitHub repository](https://github.com/foxglove/mcap) | Connects robotics evidence, provenance, retention, and future viewers through a common recording format. | Real logs can be large, malformed, private, or location-sensitive. | `ready_for_review`: synthetic catalog schema only. |
| Rerun robotics visualization storyboard | [Official GitHub repository](https://github.com/rerun-io/rerun) | Could make robotics and edge-AI evidence understandable to non-specialists. | Real use adds file, server, telemetry, privacy, dependency, and toolchain review. | `ready_for_review`: static synthetic storyboard only. |
| DeepEval RAG metric crosswalk | [Official GitHub repository](https://github.com/confident-ai/deepeval) | Its metric definitions can expose gaps in current retrieval evidence without importing its framework. | Model judges, cloud sync, providers, logins, and environment loading can conflict with local-first evidence rules. | `ready_for_review`: static six-metric crosswalk; no scores. |
| Kiln local AI workbench comparison | [Official GitHub repository](https://github.com/Kiln-AI/Kiln) | Useful product reference for organizing local prompts, datasets, retrieval, and evaluation evidence. | Mixed licensing and broad cloud, provider, agent, fine-tuning, Git-sync, and paid-feature surfaces. | `needs_more_info`: license and feature-boundary review first. |

## Model Practicality

No model candidate cleared today's threshold. The scan reviewed 30 recently
modified GGUF entries, but the highest-visible items were derivatives,
roleplay or abliterated variants, unsupported task/runtime formats, or model
families without a specific new benchmark gap. Therefore there is no artifact
size, disk, memory, runtime, download, or benchmark proposal in this report.

## Project Explainers

### Cisco MCP Scanner static security review

| Question | Plain-language answer |
| --- | --- |
| What is it? | Cisco MCP Scanner is a security checker for tools that let AI assistants connect to files, services, or other software through the Model Context Protocol. It looks for suspicious instructions, risky tool descriptions, and configuration concerns. |
| What problem does it solve? | An AI connection can appear helpful while requesting too much authority, hiding unsafe instructions, exposing secrets, or pulling in unexpected packages and network services. |
| Who is it for? | Security reviewers, AI integration teams, Model Context Protocol server authors, and maintainers deciding whether a tool deserves deeper review. |
| What is it commonly used for? | Checking tool descriptions, server configurations, prompt-injection patterns, policy concerns, and readiness before adoption. |
| How does it work in practice? | The full upstream scanner applies selected analyzers to component descriptions or connected servers. Some modes can start servers, fetch packages, receive tokens, or use a hosted analyzer. |
| What would AI Lab build? | A much smaller static worksheet that applies five security categories to 12 invented tool descriptions. It would not scan, connect, fetch, install, or execute anything. |
| What are the limitations? | Static checks cannot prove runtime safety, findings can be wrong, and scanner output still requires human judgment and separate execution review. |

### MCAP robotics log catalog

| Question | Plain-language answer |
| --- | --- |
| What is it? | MCAP is a file container for time-stamped messages from robots, vehicles, and sensors. It keeps related data streams and descriptions together so compatible tools can inspect one recording. |
| What problem does it solve? | Robotics evidence is difficult to organize when camera, map, position, and sensor data arrive at different times and use different formats. |
| Who is it for? | Robotics developers, autonomous-system teams, drone and sensor researchers, and people responsible for repeatable experiment records. |
| What is it commonly used for? | Recording sensor channels, sharing test logs, cataloging simulation runs, and moving evidence between compatible analysis or visualization tools. |
| How does it work in practice? | A recorder writes timestamped messages, schemas, and metadata into one file. A compatible reader can inspect selected channels later. |
| What would AI Lab build? | A metadata catalog for three invented recordings, covering provenance, channels, time range, privacy, integrity, retention, and approved viewers. No MCAP file would be created or opened. |
| What are the limitations? | The container does not prove sensor accuracy or make an untrusted recording safe. Real files can be very large and can reveal people, locations, or proprietary details. |

### Rerun robotics visualization storyboard

| Question | Plain-language answer |
| --- | --- |
| What is it? | Rerun is a viewer that places camera images, maps, robot positions, measurements, and three-dimensional scenes on a shared timeline. |
| What problem does it solve? | A robot incident or experiment is hard to explain when its video, maps, movement, and measurements are scattered across separate files and tools. |
| Who is it for? | Robotics and computer-vision developers, simulation teams, operations reviewers, and portfolio builders. |
| What is it commonly used for? | Replaying robot runs, comparing sensor streams, inspecting maps and positions, debugging perception, and presenting evidence. |
| How does it work in practice? | Software records or streams structured observations, and the viewer lets a person inspect connected timeline, camera, map, chart, text, and three-dimensional panels. |
| What would AI Lab build? | A static five-panel storyboard using invented camera, map, path, and chart data, with a proposed link back to an MCAP catalog record. No Rerun software would run. |
| What are the limitations? | A good viewer cannot fix bad data. Real use adds toolchain, file, server, telemetry, performance, and privacy concerns. |

### DeepEval RAG metric crosswalk

| Question | Plain-language answer |
| --- | --- |
| What is it? | DeepEval is a testing framework for AI systems. It defines checks for whether an answer used the right source material, stayed faithful to it, answered the question, or completed a task. |
| What problem does it solve? | AI demonstrations can sound convincing while using weak evidence, inventing facts, or changing after a prompt or model update. |
| Who is it for? | Developers and quality teams testing question-answering, retrieval-augmented generation, AI assistants, and tool-using workflows. |
| What is it commonly used for? | Reviewing answer relevance, retrieval quality, source faithfulness, prompt regressions, and agent or tool-use behavior. |
| How does it work in practice? | The full upstream framework runs test cases through chosen metrics. Many metrics ask another model to judge the result, and optional online services can store or compare results. |
| What would AI Lab build? | A paper crosswalk from six metric definitions to current AI Lab evidence, missing test fixtures, draft-score rules, and human-confirmation gates. It would calculate no scores. |
| What are the limitations? | Model judges can be inconsistent or biased, hosted storage changes privacy, and a familiar metric name does not prove compatibility with AI Lab's evidence rules. |

### Kiln local AI workbench comparison

| Question | Plain-language answer |
| --- | --- |
| What is it? | Kiln is a desktop workbench for keeping prompts, example data, quality checks, retrieval, and model comparisons in one AI project workspace. |
| What problem does it solve? | Experiment evidence often becomes scattered across scripts, spreadsheets, prompts, settings, and separate tools, making work difficult to repeat or explain. |
| Who is it for? | AI developers, product teams, researchers, and consultants managing several AI experiments. |
| What is it commonly used for? | Organizing prompts and datasets, comparing models, reviewing generated examples, and prototyping retrieval or evaluation workflows. |
| How does it work in practice? | The full upstream application stores tasks, data, prompts, model connections, and evaluation records. It can use local runtimes or configured online providers. |
| What would AI Lab build? | A public-metadata feature comparison and two static dashboard concepts for the most useful workflow gaps. Kiln would not be installed or connected to any data or provider. |
| What are the limitations? | Its scope is much broader than AI Lab's current product, its core and desktop code have different terms, and cloud, fine-tuning, agent, sync, and paid features complicate adoption. |

## Project Priority Review

| Project | Priority | Business value | Learning value | Local fit | Risk notes | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| Cisco MCP Scanner static security review | 5 | High governance and client-review value | High | High for static documentation | Connected scans, package retrieval, tokens, hosted analyzer, secrets | `ready_for_review` |
| MCAP robotics log catalog | 4 | Medium-high evidence and handoff value | High | High for a synthetic schema | Private or malformed logs, storage, schema and parser risk | `ready_for_review` |
| Rerun robotics visualization storyboard | 4 | High demo and observability value | High | High for a static storyboard | Toolchain, telemetry, servers, private recordings, accuracy claims | `ready_for_review` |
| DeepEval RAG metric crosswalk | 4 | High RAG QA and acceptance-test value | High | High for documentation | Provider calls, model judges, sync, environment files, fake precision | `ready_for_review` |
| Kiln local AI workbench comparison | 3 | Medium-high product and workflow value | Medium-high | Medium direct, high comparison | Mixed licensing, credentials, cloud, paid features, scope expansion | `needs_more_info` |

## Project Cost Estimates

| Project | Cost scope | Cost as of | Source checked | Price valid until | Incremental cost | From-scratch prototype | Portfolio build | DIY effort | Recurring cost | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Cisco MCP Scanner static security review | Static taxonomy, synthetic descriptors, review rubric, and storyboard | 2026-07-21 | 2026-07-21 | 2026-08-20 | $0 | $0-$25 | $0-$75 | 8-14h | $0/month | High cash, Medium effort |
| MCAP robotics log catalog | Catalog schema, synthetic manifests, retention, and viewer review gates | 2026-07-21 | 2026-07-21 | 2026-08-20 | $0 | $0-$25 | $0-$75 | 6-10h | $0/month | High cash, Medium effort |
| Rerun robotics visualization storyboard | Five-panel synthetic incident-review design and evidence navigation | 2026-07-21 | 2026-07-21 | 2026-08-20 | $0 | $0-$25 | $0-$100 | 10-18h | $0/month | High cash, Medium effort |
| DeepEval RAG metric crosswalk | Six-metric evidence map, gap list, and no-score guardrails | 2026-07-21 | 2026-07-21 | 2026-08-20 | $0 | $0-$25 | $0-$100 | 10-18h | $0/month | High cash, Medium effort |
| Kiln local AI workbench comparison | Public feature map and two static AI Lab dashboard concepts | 2026-07-21 | 2026-07-21 | 2026-08-20 | $0 | $0-$25 | $0-$125 | 12-20h | $0/month | High cash, Medium effort |

Cost assumptions and exclusions:

- All estimates price the smallest credible, safe, planning-only MVP and reuse
  the confirmed Mac Studio, existing editor, and existing local design tools.
- From-scratch estimates assume a general-purpose computer is already
  available. They cover incidental project materials, not the computer.
- Portfolio estimates cover extra documentation, static screens, synthetic
  assets, and a recorded walkthrough. They do not add execution scope.
- Estimates exclude packages, models, installations, runtimes, servers,
  hosted services, credentials, real logs, robots, drones, sensors, storage
  upgrades, electricity, taxes, shipping, and paid support.
- The local profile does not confirm Raspberry Pi, robotics, radio, drone, or
  sensor inventory. None of those items is required for today's MVPs.

Price sources:

- Cisco MCP Scanner: https://github.com/cisco-ai-defense/mcp-scanner,
  checked 2026-07-21.
- MCAP: https://github.com/foxglove/mcap, checked 2026-07-21.
- Rerun: https://github.com/rerun-io/rerun, checked 2026-07-21.
- DeepEval: https://github.com/confident-ai/deepeval, checked 2026-07-21.
- Kiln: https://github.com/Kiln-AI/Kiln, checked 2026-07-21.

Refresh notes:

- Refresh by 2026-08-20, or earlier after a license, price, release,
  maintenance, hosted-service, telemetry, data-handling, package, or runtime
  boundary change. A routine recheck with no material change does not make an
  item eligible for a new daily delta.

## Effort-Versus-Value View

The groups overlap intentionally. They are planning views, not rankings, ROI,
or composite opportunity scores.

### Weekend Projects

| Project | Cash | DIY hours | Learning value | Business value | Risk |
| --- | --- | --- | --- | --- | --- |
| MCAP robotics log catalog | $0 incremental | 6-10h | High | Medium-high | Medium: privacy, provenance, schema scope |
| Cisco MCP Scanner static security review | $0 incremental | 8-14h | High | High | Medium-high: security claims and connected upstream modes |
| Rerun robotics visualization storyboard | $0 incremental | 10-18h | High | High | Medium: privacy, evidence accuracy, tool boundaries |

### Sub-$300 Builds

| Project | Cash | DIY hours | Learning value | Business value | Risk |
| --- | --- | --- | --- | --- | --- |
| Cisco MCP Scanner static security review | $0-$75 portfolio scope | 8-14h | High | High | Medium-high |
| MCAP robotics log catalog | $0-$75 portfolio scope | 6-10h | High | Medium-high | Medium |
| Rerun robotics visualization storyboard | $0-$100 portfolio scope | 10-18h | High | High | Medium |
| DeepEval RAG metric crosswalk | $0-$100 portfolio scope | 10-18h | High | High | Medium-high |
| Kiln local AI workbench comparison | $0-$125 portfolio scope | 12-20h | Medium-high | Medium-high | High until licensing is reviewed |

### Larger Portfolio Investments

No new project needs more than $300 for its defined MVP. A real robotics,
camera, drone, sensor, server, or storage build would be a separate project
with a fresh inventory check, cost packet, risk review, and explicit approval.

## MVP Action Cards

### Cisco MCP Scanner static security review

| Field | Value |
| --- | --- |
| One-week deliverable | Threat-category matrix, 12 synthetic tool descriptions, human-review rubric, and static results storyboard. |
| Success criteria | Every synthetic item is reviewed for authority, prompt injection, packages, secrets, and network paths; findings are clearly not final safety decisions. |
| Expected demo artifact | Sanitized Markdown review packet and static results-table mockup. |
| Prerequisites | Approval for documentation only and agreement on the five review categories. |
| First three tasks | 1. Map upstream concepts to AI Lab trust boundaries. 2. Write 12 synthetic safe and risky descriptors. 3. Draft the rubric and results storyboard. |
| Blockers | Category ownership, acceptable false-positive handling, and whether the checklist belongs in radar or security documentation. |
| Stop conditions | Stop before installation, scanning, package retrieval, server launch or connection, token use, real configuration access, or any claim of proven safety. |
| Safety notes | Synthetic static review only; no live target, secret, package, server, network, installation, or execution. |

### MCAP robotics log catalog

| Field | Value |
| --- | --- |
| One-week deliverable | Catalog schema, three synthetic recording manifests, privacy and retention labels, and viewer-review gates. |
| Success criteria | Each record communicates provenance, channels, time span, privacy, integrity evidence, retention, and approved viewer status without opening a file. |
| Expected demo artifact | Markdown specification and static three-record catalog mockup. |
| Prerequisites | Approval for schema-only work and selection of three synthetic robotics scenarios. |
| First three tasks | 1. Define manifest and privacy fields. 2. Draft three synthetic records. 3. Map retention, integrity, and viewer-review gates. |
| Blockers | Storage location, checksum policy, privacy vocabulary, and future viewer list. |
| Stop conditions | Stop before library download, untrusted-log access, live telemetry, personal or location data collection, or an unapproved registry schema change. |
| Safety notes | Synthetic metadata only; no real log, parser, robot, drone, sensor, library, command-line tool, or telemetry. |

### Rerun robotics visualization storyboard

| Field | Value |
| --- | --- |
| One-week deliverable | Five-panel synthetic incident storyboard with timeline, camera, map, path, chart, and evidence-record navigation. |
| Success criteria | A non-technical reviewer can explain the event, timing, supporting evidence, and remaining uncertainty. |
| Expected demo artifact | Click-through static mockup or slide sequence with an annotated walkthrough. |
| Prerequisites | Approval for static design and agreement on one invented robotics incident. |
| First three tasks | 1. Define the incident and review questions. 2. Draft five synthetic panel states. 3. Add uncertainty, provenance, and MCAP-record navigation. |
| Blockers | Target audience, design tool, and dashboard versus portfolio ownership. |
| Stop conditions | Stop before installation, server use, telemetry, real-log access, personal or location data, or unmeasured sensor-accuracy claims. |
| Safety notes | Static synthetic design only; no viewer, server, library, telemetry, log, camera, sensor, robot, or flight. |

### DeepEval RAG metric crosswalk

| Field | Value |
| --- | --- |
| One-week deliverable | Six-metric crosswalk covering definitions, evidence, fixture gaps, draft status, human confirmation, and misuse warnings. |
| Success criteria | Each metric states its evidence needs, current coverage, missing fixtures, and why source or model-judge claims are not confirmed scores. |
| Expected demo artifact | Markdown metric map and static synthetic evidence-card mockup. |
| Prerequisites | Approval for documentation only and selection of six retrieval metrics. |
| First three tasks | 1. Restate six metrics in AI Lab terms. 2. Map current evidence and missing fixtures. 3. Add draft, confirmation, privacy, and no-score guardrails. |
| Blockers | Intended RAG evidence fields and owner preference on model-judge metrics. |
| Stop conditions | Stop before installation, environment-file access, provider or model calls, login, sync, benchmark execution, or score creation. |
| Safety notes | Static documentation only; no package, model, provider, API, credential, sync, benchmark, or score. |

### Kiln local AI workbench comparison

| Field | Value |
| --- | --- |
| One-week deliverable | Feature and boundary comparison plus two static AI Lab dashboard concepts for the highest-value workflow gaps. |
| Success criteria | Reviewers can distinguish shared features, useful gaps, out-of-scope features, licensing, local versus cloud paths, and the two dashboard concepts. |
| Expected demo artifact | Markdown comparison matrix, two static screens, and a narrated walkthrough. |
| Prerequisites | Desktop-license review, comparison-goal confirmation, and selection of two AI Lab workflows. |
| First three tasks | 1. Map public Kiln features to AI Lab OS. 2. Separate local, cloud, paid, and out-of-scope surfaces. 3. Draft two concepts and a build-or-defer recommendation. |
| Blockers | License interpretation, Pro boundaries, preferred workflows, and unconfirmed maximum DIY hours. |
| Stop conditions | Stop before installation, license acceptance, credential entry, private-data import, Git sync, provider calls, fine-tuning, or agent scope. |
| Safety notes | Public metadata and static design only; no app, server, provider, credential, private data, sync, model, fine-tuning, agent, installation, or execution. |

## Ready For Eval

No model candidate is ready for evaluation. No item was connected to
`evals/local-llm-benchmark/SPEC.md` or `skills/local-llm-eval` because today's
reported items are project opportunities, not model artifacts.

## Watchlist

| Candidate | Reason | Retest or revisit trigger |
| --- | --- | --- |
| Kiln local AI workbench comparison | The product reference is useful, but desktop versus core licensing and broad provider, paid, agent, fine-tuning, and sync surfaces need separation. | Revisit after a static license and feature-boundary review, or after a material license, release, pricing, or local-runtime change. |
| HalluGuard-Qwen3-4B-GGUF | A compact hallucination-guard role could eventually be relevant, but there is no approved judge-model lane or exact-artifact review. | Revisit only when the benchmark defines a judge role and an exact artifact has provenance, license, runtime, and fixture evidence. |

## Skips

| Candidate | Reason |
| --- | --- |
| Remaining 29 recently modified GGUF entries | Derivative provenance, role mismatch, unsupported format, overlap, or lack of a specific benchmark gap. |
| linorobot2 | Physical hardware, Robot Operating System 2, and install-script scope are too broad for this one-week lane. |
| RoboCasa | Heavy simulation, asset, and dataset requirements exceed the current MVP. |
| mcp-local-rag | Package and model retrieval behavior plus overlap with the existing RAG backbone. |
| AI DIAL RAG Eval | Provider URL or credential assumptions and low visible adoption offer less value than a static metric crosswalk. |

## Import Or Task Notes

- Registry updates: none; neither candidate registry was edited.
- Benchmark follow-ups: none; no model candidate cleared the review threshold.
- Dashboard follow-ups: none; the Rerun and Kiln concepts remain static action
  cards and do not authorize dashboard changes.
- Best next approval task: approve or decline the Cisco MCP Scanner static
  taxonomy and 12 synthetic-descriptor review.
- Profile fields needing confirmation: maximum DIY hours, portfolio investment
  budget, and Raspberry Pi, robotics, radio, drone, camera, sensor, and storage
  inventory. These unknowns did not change today's $0 design MVPs.

## Safety Posture

- Metadata-only boundaries: 39 public metadata items were reviewed; no source
  repository, package, model, model-card code, server, file, or sample was
  downloaded, installed, opened, or executed.
- Registry changes: none. No score, benchmark result, final model label,
  dashboard decision, or purchase decision was created.
- Downloads, installs, execution, APIs, and secrets: none. No inference API,
  hosted analyzer, provider, login, token, API key, environment file, cart,
  purchase, live telemetry, flight, control, or radio transmission was used.
- Privacy: the ignored local profile informed cost assumptions, but no private
  inventory detail, machine path, prompt, response, or benchmark artifact was
  copied into this report.
- Cost and action cards are estimates and planning records only. They do not
  authorize spending, execution, data collection, integration, or registry
  entry.

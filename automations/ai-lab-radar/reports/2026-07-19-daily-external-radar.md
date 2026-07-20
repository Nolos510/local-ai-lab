# AI Lab Radar Report

Date: 2026-07-19
Reviewer: Codex automation
Source packet: `automations/ai-lab-radar/inputs/2026-07-19-daily-external-radar.md`
Approved for radar review: no
Safe to commit: no
Dashboard: [Radar candidates](http://127.0.0.1:8765/radar) after starting the
local dashboard.

## Summary

- Candidates reviewed: 6 high-signal deltas from 30 public metadata items.
- Ready for evaluation: 0.
- Watchlist or needs more information: 2 model candidates.
- Project review opportunities: 4.
- Skipped: 0 normalized items; 24 source-set items were de-duplicated or not shortlisted.
- Best immediate review task: a static `agentevals` trace/evaluator mapping.
- Best tangible edge build: Raspberry Pi AI HAT+ 2, pending inventory and budget confirmation.

## Delta Summary

| Item | Type | Status | First seen | Last seen | Change summary |
| --- | --- | --- | --- | --- | --- |
| Ornith-1.0-9B-GGUF | model_candidate | `new` | 2026-07-19 | 2026-07-19 | First radar appearance of this exact compact coding GGUF. |
| MiniCPM5-1B-Agentic-Tooluse-GGUF | model_candidate | `new` | 2026-07-19 | 2026-07-19 | First radar appearance of this exact 688 MB tool-use GGUF. |
| agentevals | project_opportunity | `new` | 2026-07-19 | 2026-07-19 | First local-first trace-evaluation opportunity in radar. |
| Raspberry Pi AI HAT+ 2 | project_opportunity | `new` | 2026-07-19 | 2026-07-19 | First radar appearance with official current $200 hardware metadata. |
| PlotJuggler | project_opportunity | `new` | 2026-07-19 | 2026-07-19 | First passive robotics log-visualization opportunity in radar. |
| SigMF capture catalog | project_opportunity | `new` | 2026-07-19 | 2026-07-19 | First standards-based passive signal catalog opportunity in radar. |

## Candidate Review

| Candidate | Source | Why interesting | Risk notes | Recommended next step |
| --- | --- | --- | --- | --- |
| Ornith-1.0-9B-GGUF | [Hugging Face](https://huggingface.co/deepreinforce-ai/Ornith-1.0-9B-GGUF) | 5.63 GB Q4 coding-agent artifact is practical for local review. | Special parser/template behavior, exact hash, and artifact provenance are unresolved. | `needs_more_info`: exact-artifact security review. |
| MiniCPM5-1B-Agentic-Tooluse-GGUF | [Hugging Face](https://huggingface.co/ewinregirgojr/MiniCPM5-1B-Agentic-Tooluse-GGUF) | 688 MB Q4 artifact could support a cheap deterministic tool-call fixture. | License is `other`; source reports weak clean stopping and quant-specific eval gaps. | `needs_more_info`: license chain and non-executing tool fixture review. |
| agentevals | [GitHub](https://github.com/agentevals-dev/agentevals) | Saved traces could strengthen evidence lineage without re-running agents. | Dependencies, optional cloud graders, and sensitive trace content require review. | `ready_for_review`: static mapping only. |
| Raspberry Pi AI HAT+ 2 | [Raspberry Pi](https://www.raspberrypi.com/products/ai-hat-plus-2/) | Tangible local generative-AI edge project with 8 GB dedicated memory. | Inventory, model compatibility, thermals, supply chain, and budget are unresolved. | `needs_more_info`: inventory and bill-of-materials review. |
| PlotJuggler | [GitHub](https://github.com/PlotJuggler/PlotJuggler) | Passive local charts for drone and robot logs avoid live flight/control work. | Native binary, plugins, beta release, telemetry posture, and log trust need review. | `ready_for_review`: static storyboard and file threat review. |
| SigMF capture catalog | [GitHub](https://github.com/sigmf/SigMF) | Standard metadata makes passive signal datasets reproducible and searchable. | Metadata can expose location/equipment; live capture raises legal and privacy questions. | `ready_for_review`: synthetic metadata specification only. |

## Model Practicality

| Candidate | Artifact size | Disk requirement | Memory range | Compatible local runtimes | Benchmark gap |
| --- | --- | --- | --- | --- | --- |
| Ornith-1.0-9B-GGUF | Source-declared 5.63 GB Q4_K_M or 6.47 GB Q5_K_M | Inferred 8-10 GB | Inferred 8-16 GB at modest context; long context may need much more | Source metadata lists llama.cpp, LM Studio, and Ollama; unverified | Exact artifact/hash, license/provenance, template, reasoning/tool parser, context cap, runner approval, and coding-agent fixture. |
| MiniCPM5-1B-Agentic-Tooluse-GGUF | Source-declared 688 MB Q4_K_M, 1.15 GB Q8_0, or 2.17 GB F16 | Inferred 2-4 GB | Inferred 2-6 GB | Source metadata lists llama.cpp, LM Studio, and Ollama; XML tool parser unverified | Exact artifact/hash, license chain, template, bounded stopping, and deterministic fake-tool fixture. |

Neither model is `ready_for_eval`. A later approval must select one exact
artifact and connect it to `evals/local-llm-benchmark/SPEC.md` and
`skills/local-llm-eval` without giving a tool-use model real authority.

## Project Explainers

### agentevals

| Question | Plain-language answer |
| --- | --- |
| What is it? | A checker for whether a multi-step AI assistant followed the expected sequence of actions. |
| What problem does it solve? | It helps locate which tool call or intermediate step caused a bad result without asking the assistant to repeat the task. |
| Who is it for? | Teams building task-oriented assistants, quality reviewers, and developers responsible for reliable automation. |
| What is it commonly used for? | Checking tool sequences, comparing observed and expected behavior, reviewing failures, and creating deterministic release gates. |
| How does it work in practice? | It reads an OpenTelemetry trace, a structured timeline of application activity, and compares it with expected behavior definitions. |
| What would AI Lab build? | A static mapping from one sanitized benchmark artifact to a trace-like fixture and three deterministic review checks. |
| What are the limitations? | It is not optimized for long coding sessions, expects a particular trace shape, and broader integrations would add dependencies and sensitive telemetry. |

### Raspberry Pi AI HAT+ 2

| Question | Plain-language answer |
| --- | --- |
| What is it? | An add-on board that gives a Raspberry Pi 5 dedicated hardware and memory for running small language and vision AI locally. |
| What problem does it solve? | It makes useful edge AI possible without relying continuously on a cloud service or overloading the Pi's main processor. |
| Who is it for? | Edge-computing learners, educators, prototype builders, and teams working in low-connectivity or privacy-sensitive settings. |
| What is it commonly used for? | Small document assistants, translation, camera scene descriptions, speech experiments, and other compact local AI tasks. |
| How does it work in practice? | The Pi runs the application and user interface while the HAT handles supported AI calculations using its accelerator and 8 GB of memory. |
| What would AI Lab build? | A field-assistant concept comparing local document question answering with camera scene summaries. |
| What are the limitations? | It needs a Pi 5 and supported Hailo software, runs much smaller models than the Mac Studio, and costs more than the confirmed $300 tier from scratch. |

### PlotJuggler

| Question | Plain-language answer |
| --- | --- |
| What is it? | A desktop tool that turns recorded robot, drone, or sensor measurements into interactive charts on a shared timeline. |
| What problem does it solve? | Raw logs contain too many time-stamped numbers to understand easily when diagnosing an unusual event. |
| Who is it for? | Robotics learners, drone-log reviewers, test engineers, and developers troubleshooting sensors or controls. |
| What is it commonly used for? | Reviewing saved flight logs, comparing commanded and actual motion, checking sensor timing, and reusing chart layouts across tests. |
| How does it work in practice? | A user opens a supported file, chooses measurements, and arranges charts so events can be compared at the same moment. |
| What would AI Lab build? | A passive three-panel flight-log review storyboard using synthetic or explicitly approved recorded data. |
| What are the limitations? | It visualizes data rather than automatically explaining every fault; plugins, file formats, and robot-specific concepts still need review. |

### SigMF capture catalog

| Question | Plain-language answer |
| --- | --- |
| What is it? | A catalog based on the Signal Metadata Format, a standard for labeling recorded radio or sensor signals. |
| What problem does it solve? | Recordings lose value when frequency, sample rate, time, equipment, and annotations are missing or inconsistent. |
| Who is it for? | Radio learners, researchers, educators, and teams archiving passive signal datasets. |
| What is it commonly used for? | Describing recordings, validating metadata, marking interesting time ranges, and sharing sanitized dataset descriptions. |
| How does it work in practice? | A recording has raw data plus a small JSON metadata file; the catalog checks approved metadata and presents searchable summaries. |
| What would AI Lab build? | A synthetic-only metadata validator and local catalog mockup with no live radio capture. |
| What are the limitations? | SigMF is a standard rather than a complete application, raw files can be large, and metadata may reveal sensitive locations or equipment. |

## Project Priority Review

| Project | Priority | Business value | Learning value | Local fit | Risk notes | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| agentevals | 5 | Strong quality-control feature for client automations | High: traces, deterministic evals, evidence lineage | High for static design; integration unreviewed | Sensitive traces, dependencies, optional cloud graders | `ready_for_review` |
| Raspberry Pi AI HAT+ 2 | 4 | Strong kiosk, field-manual, and private edge-demo potential | High: accelerators, thermals, model limits | Good category fit; inventory unknown | Supply chain, privacy, compatibility, budget | `needs_more_info` |
| PlotJuggler | 4 | Strong passive maintenance/inspection dashboard story | High: time series and flight logs | Good; macOS arm64 metadata visible | Native binary, beta, plugins, telemetry, log trust | `ready_for_review` |
| SigMF capture catalog | 4 | Reusable sensor/dataset catalog pattern | High: schemas, provenance, privacy | Excellent for stdlib design | Location metadata and future radio-law scope | `ready_for_review` |

## Project Cost Estimates

| Project | Cost scope | Cost as of | Source checked | Price valid until | Incremental cost | From-scratch prototype | Portfolio build | DIY effort | Recurring cost | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentevals | Static trace fixture and evaluator storyboard | 2026-07-19 | 2026-07-19 | 2026-08-18 | $0-$25 | $0-$25 with general-purpose host | $0-$75 | 10-16h | $0/month | High cash, Medium effort |
| Raspberry Pi AI HAT+ 2 | Eventual Pi 5 document/camera edge demo; first week design-only | 2026-07-19 | 2026-07-19 | 2026-08-18 | $200-$230 if Pi stack owned | $290-$350 | $360-$500 | 12-20h after approval; 6-10h design | $1-$4/month | Medium |
| PlotJuggler | Static passive log-dashboard storyboard | 2026-07-19 | 2026-07-19 | 2026-08-18 | $0-$20 | $0-$25 with general-purpose host | $0-$75 | 8-14h | $0/month | High cash, Medium effort |
| SigMF capture catalog | Synthetic metadata validator/catalog; optional receiver later | 2026-07-19 | 2026-07-19 | 2026-07-26 | $0-$15 | $0-$25 | $40-$100 with optional passive receiver | 6-10h; 12-20h with capture review | $0-$2/month | High metadata MVP, Low receiver price |

Cost assumptions and exclusions:

- Software/design MVPs reuse confirmed lab compute and exclude direct package
  installation, dedicated hosts, paid support, and cloud services.
- AI HAT+ 2 assumes the official $200 board, a low-memory Pi 5, basic power,
  cooling, and storage. Tax, shipping, displays, batteries, and replacement parts
  are excluded.
- SigMF starts with synthetic metadata. The optional receiver range uses an old
  public vendor observation and must be refreshed before hardware approval.

Price sources:

- agentevals: https://github.com/agentevals-dev/agentevals, checked 2026-07-19.
- AI HAT+ 2 and Pi 5: https://www.raspberrypi.com/products/ai-hat-plus-2/ and https://www.raspberrypi.com/products/raspberry-pi-5/, checked 2026-07-19.
- Raspberry Pi price context: https://www.raspberrypi.com/news/a-new-3gb-raspberry-pi-4-for-83-75-and-more-memory-driven-price-increases/, checked 2026-07-19.
- PlotJuggler: https://github.com/PlotJuggler/PlotJuggler, checked 2026-07-19.
- SigMF and optional RTL-SDR: https://github.com/sigmf/SigMF and https://www.rtl-sdr.com/rtl-sdr-blog-v4-dongle-initial-release/, checked 2026-07-19.

Refresh notes:

- Refresh the AI HAT+ 2 range within 30 days or sooner for stock, Pi tier, or
  inventory changes.
- Refresh the optional receiver within seven days because the vendor price/stock
  post is old.
- Refresh software projects on material release, license, telemetry, or local-first
  behavior changes; an unchanged source check is not a daily delta.

## Effort-Versus-Value View

### Weekend Projects

| Project | Cash | DIY hours | Learning value | Business value | Risk |
| --- | --- | --- | --- | --- | --- |
| SigMF capture catalog | $0-$15 | 6-10h | High | Medium | Low in synthetic scope; privacy/legal review before capture |
| PlotJuggler storyboard | $0-$20 | 8-14h | High | High | Medium native/log review burden |
| agentevals mapping | $0-$25 | 10-16h | High | High | Medium schema/privacy burden |

### Sub-$300 Builds

| Project | Cash | DIY hours | Learning value | Business value | Risk |
| --- | --- | --- | --- | --- | --- |
| SigMF metadata MVP | $0-$25 | 6-10h | High | Medium | Low with synthetic data |
| PlotJuggler design MVP | $0-$25 | 8-14h | High | High | Medium |
| agentevals design MVP | $0-$25 | 10-16h | High | High | Medium |
| AI HAT+ 2 incremental only | $200-$230 if Pi 5 stack is owned | 12-20h | High | High | Inventory unconfirmed; from scratch exceeds tier |

### Larger Portfolio Investments

| Project | Cash | DIY hours | Learning value | Business value | Risk |
| --- | --- | --- | --- | --- | --- |
| Raspberry Pi AI HAT+ 2 finished demo | $360-$500 | 12-20h | High | High | Hardware, model, thermal, privacy, and supply-chain review |

## MVP Action Cards

### agentevals

| Field | Value |
| --- | --- |
| One-week deliverable | Sanitized trace schema map, three deterministic evaluator definitions, and an evidence-flow storyboard. |
| Success criteria | Every proposed check maps to a fixture field, human confirmation is explicit, and no score or model run is implied. |
| Expected demo artifact | Markdown design note, sanitized JSON fixtures, and static UI mockup. |
| Prerequisites | Approval for a design-only spike and one sanitized benchmark artifact shape. |
| First three tasks | 1. Select and sanitize one artifact shape. 2. Map it to a minimal trace and expected-action schema. 3. Draft three checks and a review storyboard. |
| Blockers | Current artifacts may not contain compatible events; score and import boundaries need review. |
| Stop conditions | Stop if useful checks require private prompts, package execution, cloud judges, or changed confirmed-score semantics. |
| Safety notes | Keep traces and paths local and sanitized; no package, model, cloud API, score import, or dashboard decision is approved. |

### Raspberry Pi AI HAT+ 2

| Field | Value |
| --- | --- |
| One-week deliverable | Compatibility matrix, sourced bill of materials, two-screen demo storyboard, and go/no-go note. |
| Success criteria | Review identifies a supported model path, full cost assumptions, privacy boundaries, and stop conditions without purchasing or installing anything. |
| Expected demo artifact | Architecture diagram, bill of materials, interaction storyboard, and risk checklist. |
| Prerequisites | Confirm Raspberry Pi 5/accessory inventory and choose document Q&A or camera scene summaries as primary. |
| First three tasks | 1. Confirm inventory and preferred use case. 2. Compare official model/runtime support with the task. 3. Finalize costs, storyboard, and approval gates. |
| Blockers | Inventory, over-$300 budget, artifact support, thermals, camera scope, and Hailo software review. |
| Stop conditions | Stop for unsupported model, mandatory cloud account, hidden telemetry, budget breach, or unsafe camera collection. |
| Safety notes | No purchase, download, installation, camera deployment, biometric identification, covert monitoring, or cloud connection is approved. |

### PlotJuggler

| Field | Value |
| --- | --- |
| One-week deliverable | Three-panel flight-log storyboard, synthetic data dictionary, and file-handling threat checklist. |
| Success criteria | Three signals align in time, each chart answers a clear question, and no live control or private flight data is used. |
| Expected demo artifact | Static dashboard mockup, synthetic CSV/ULog field map, and review checklist. |
| Prerequisites | Approval of passive recorded-data scope and selection of PX4 ULog or generic CSV. |
| First three tasks | 1. Choose format and three questions. 2. Define synthetic fields and chart layouts. 3. Draft the threat checklist and narrated storyboard. |
| Blockers | Real-log provenance, macOS binary review, plugin needs, and telemetry behavior. |
| Stop conditions | Stop for live vehicle connection, flight commands, private logs, unsafe binaries, or cloud upload. |
| Safety notes | Passive offline review only; no flight/control, tracking, upload, download, or installation is approved. |

### SigMF capture catalog

| Field | Value |
| --- | --- |
| One-week deliverable | Minimal metadata schema, six synthetic validation cases, and searchable catalog storyboard. |
| Success criteria | Fixtures cover valid, missing, malformed, and privacy-sensitive metadata without raw recordings or network use. |
| Expected demo artifact | Markdown specification, sanitized JSON fixtures, validation matrix, and static catalog mockup. |
| Prerequisites | Approval of synthetic-only receive-side scope and no private location/equipment metadata in tracked files. |
| First three tasks | 1. Select minimal fields and privacy rules. 2. Draft six synthetic fixtures. 3. Design the local catalog and review flow. |
| Blockers | Capture hardware, local radio rules, storage policy, and private metadata handling are unconfirmed. |
| Stop conditions | Stop for live interception, transmission, private coordinates, unapproved recordings, or package installation. |
| Safety notes | Synthetic metadata and passive educational scope only; no transmission, private interception, live capture, decoding, or purchase is approved. |

## Ready For Eval

No model is ready for evaluation from this metadata-only scan.

## Watchlist

| Candidate | Reason | Retest or revisit trigger |
| --- | --- | --- |
| Ornith-1.0-9B-GGUF | Practical coding size, but parser/template and artifact review are incomplete. | Exact Q4/Q5 artifact, hash, license/provenance, runner, and coding fixture approved. |
| MiniCPM5-1B-Agentic-Tooluse-GGUF | Very small tool-use model with explicit weaknesses worth testing safely. | License chain, exact artifact/hash, bounded parser, and fake-tool fixture approved. |

## Skips

No normalized item was marked `skip`; lower-signal source-set items were not
promoted into candidate records.

## Import Or Task Notes

- Registry updates: none; explicit approval is required for each candidate or project.
- Benchmark follow-ups: Ornith needs a coding-agent lane; MiniCPM needs a deterministic non-executing tool-call fixture.
- Dashboard follow-ups: none; the dashboard and import paths were not changed.
- Open questions: confirm Raspberry Pi/SDR inventory, maximum DIY hours, and portfolio budget.

## Safety Posture

- Metadata-only boundaries: public pages and repo-local planning artifacts only.
- Registry changes: none to model or project CSV files.
- Downloads, installs, execution, APIs, and secrets: none. No model, package, or
  repository was downloaded or run; no cloud/model API, key, secret, purchase,
  radio capture/transmission, or flight/control action occurred.

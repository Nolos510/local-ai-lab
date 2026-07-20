# AI Lab Radar Report

Date: 2026-07-20
Reviewer: Codex automation
Source packet: `automations/ai-lab-radar/inputs/2026-07-20-daily-external-radar.md`
Approved for radar review: no
Safe to commit: no
Dashboard: [Radar candidates](http://127.0.0.1:8765/radar) after starting the
local dashboard.

## Summary

- Candidates reviewed: 5 high-signal deltas from 39 public metadata items.
- Ready for evaluation: 0.
- Watchlist or needs more information: 1 model candidate and 2 projects.
- Ready for design review: 2 projects.
- Best immediate review task: a static `llama-swap` provider-boundary and
  threat-model spike.
- Strongest portfolio opportunity: an offline WebODM mapping case study using
  pre-approved imagery and no live flight.

## Delta Summary

| Item | Type | Status | First seen | Last seen | Change summary |
| --- | --- | --- | --- | --- | --- |
| Lemma 8B GGUF and MLX | model_candidate | `new` | 2026-07-20 | 2026-07-20 | First radar appearance of this exact compact multimodal artifact family with explicit Apple Silicon metadata. |
| llama-swap local model router | project_opportunity | `new` | 2026-07-20 | 2026-07-20 | First local model-router opportunity in radar. |
| Docling ingestion compatibility spike | project_opportunity | `new` | 2026-07-20 | 2026-07-20 | First structured document-normalization opportunity in radar. |
| WebODM offline aerial mapping portfolio | project_opportunity | `new` | 2026-07-20 | 2026-07-20 | First offline photogrammetry opportunity, with a source release dated 2026-07-19. |
| SatDump offline satellite-data learning | project_opportunity | `new` | 2026-07-20 | 2026-07-20 | First satellite signal-processing opportunity, limited to synthetic or approved offline data. |

## Candidate Review

| Candidate | Source | Why interesting | Risk notes | Recommended next step |
| --- | --- | --- | --- | --- |
| Lemma 8B GGUF and MLX | [Hugging Face](https://huggingface.co/lthn/lemma) | Explicit 5.34-15.1 GB artifacts, 128K context claim, and Apple Silicon runtime metadata. | Third-party merged fine-tune, EUPL/base-license chain, model-card scripts, template, and multimodal benchmark gaps. | `needs_more_info`: exact-artifact and license review. |
| llama-swap local model router | [GitHub](https://github.com/mostlygeek/llama-swap) | One stable local endpoint could coordinate model servers and idle-memory use. | Configuration can launch commands and hooks; logs and remote binding need strict boundaries. | `ready_for_review`: static architecture and threat model only. |
| Docling ingestion compatibility spike | [GitHub](https://github.com/docling-project/docling) | Structured document conversion could improve RAG citations, tables, and format consistency. | Broad dependency, parser, optional-model, URL, service, and private-document surface. | `needs_more_info`: static schema and dependency review. |
| WebODM offline aerial mapping portfolio | [GitHub](https://github.com/WebODM/WebODM) | Produces understandable maps and three-dimensional outputs from approved existing imagery. | AGPL, processing-engine terms, container stack, precise locations, privacy, and accuracy claims. | `ready_for_review`: offline provenance and storyboard only. |
| SatDump offline satellite-data learning | [GitHub](https://github.com/SatDump/SatDump) | A tangible receive-side learning path from saved radio samples to satellite products. | Latest visible tag is from 2024; hardware, recording provenance, radio law, storage, and binary review are unresolved. | `needs_more_info`: offline provenance, release, and legal review. |

## Model Practicality

| Candidate | Artifact size | Disk requirement | Memory range | Compatible local runtimes | Benchmark gap |
| --- | --- | --- | --- | --- | --- |
| Lemma 8B GGUF and MLX | Source-declared 5.34 GB Q4_K_M, 5.76 GB Q5_K_M, 6.22 GB Q6_K, 8.03 GB Q8_0, or 15.1 GB BF16 | Inferred 8-12 GB for one Q4-Q6 artifact and evidence | Inferred 8-18 GB at modest text context; image, audio, and long context can require more | Source lists Ollama, llama.cpp, GPT4All, LM Studio, and separate MLX builds; versions unverified | Exact artifact/hash, EUPL and base-license review, merged-weight provenance, template, runtime version, context cap, and separate multimodal fixtures. |

Lemma is not `ready_for_eval`. A later approval must select one exact artifact
and connect only an approved text lane to `evals/local-llm-benchmark/SPEC.md`
and `skills/local-llm-eval`. Image and audio claims need separate fixtures and
are not scores.

## Project Explainers

### llama-swap local model router

| Question | Plain-language answer |
| --- | --- |
| What is it? | A traffic controller for local AI models. It directs a request to the named model and can swap models in and out as memory is needed. |
| What problem does it solve? | A lab may own many models but cannot keep all of them loaded or make every application understand every model server. |
| Who is it for? | Local AI developers, small teams sharing one inference machine, and builders who want one stable local endpoint. |
| What is it commonly used for? | Switching between chat and coding models, routing embeddings separately, unloading idle models, and hiding runtime differences from applications. |
| How does it work in practice? | An application names a model in its request. The router selects or starts the matching local server, forwards the request, and manages idle processes. |
| What would AI Lab build? | A static compatibility map for two existing provider shapes, model roles, failure states, resource use, and logging boundaries. |
| What are the limitations? | It does not provide or approve models, and its command and hook features create a sensitive execution boundary. |

### Docling ingestion compatibility spike

| Question | Plain-language answer |
| --- | --- |
| What is it? | A document converter that tries to preserve headings, tables, formulas, reading order, and other structure across many file types. |
| What problem does it solve? | Search and retrieval systems work poorly when a PDF, slide deck, spreadsheet, or scan becomes an unstructured block of text. |
| Who is it for? | Teams building document search, research assistants, compliance archives, and internal knowledge tools. |
| What is it commonly used for? | Converting PDFs to Markdown, extracting tables, normalizing office files, preparing scans for retrieval, and producing structured JSON. |
| How does it work in practice? | A file enters a format-specific pipeline, optional recognition steps identify layout and content, and the result is exported in one consistent structure. |
| What would AI Lab build? | A no-install mapping from five sanitized document shapes to current ingestion metadata, citation needs, chunking rules, and failure cases. |
| What are the limitations? | Complex pages can still be wrong, optional models add downloads and licenses, and direct adoption would add a substantial dependency surface. |

### WebODM offline aerial mapping portfolio

| Question | Plain-language answer |
| --- | --- |
| What is it? | Software that turns many overlapping aerial photographs into a joined map, elevation view, point cloud, or three-dimensional scene. |
| What problem does it solve? | A folder of aerial photos is difficult to measure or understand until the images are aligned into one consistent view. |
| Who is it for? | Mapping learners, construction and agriculture teams, environmental researchers, drone photographers, and portfolio builders. |
| What is it commonly used for? | Site maps, terrain comparison, area measurements, three-dimensional scenes, and construction or land-change documentation. |
| How does it work in practice? | Approved overlapping images are processed to estimate camera positions, match common features, and create map and three-dimensional outputs. |
| What would AI Lab build? | An offline workflow and client-style storyboard using a sanitized, pre-approved image set, with no live flight. |
| What are the limitations? | Quality depends on image overlap and metadata, it is not licensed surveying, and current WebODM is no longer the same project as OpenDroneMap. |

### SatDump offline satellite-data learning

| Question | Plain-language answer |
| --- | --- |
| What is it? | Software that converts certain saved satellite radio recordings into understandable products such as images and measurement files. |
| What problem does it solve? | Raw radio recordings are large streams of numbers until a matching decoder checks and organizes the signal. |
| Who is it for? | Radio and space learners, weather-satellite hobbyists, educators, and researchers using authorized public broadcasts or recordings. |
| What is it commonly used for? | Processing weather-satellite recordings, viewing decoded imagery, checking signal quality, and learning satellite data pipelines. |
| How does it work in practice? | A user chooses a saved recording and matching satellite pipeline; the software decodes it and writes images, telemetry, or other products for review. |
| What would AI Lab build? | A synthetic and approved-recording storyboard for one weather-satellite pipeline, storage worksheet, metadata model, and legal boundaries. |
| What are the limitations? | Recordings can be large, support varies by satellite, and live reception depends on hardware, location, antenna, timing, and local rules. |

## Project Priority Review

| Project | Priority | Business value | Learning value | Local fit | Risk notes | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| llama-swap local model router | 5 | High private-AI operations value | High | High at design level | Commands, hooks, logs, process and port exposure | `ready_for_review` |
| Docling ingestion compatibility spike | 4 | High document-workflow value | High | Strong functional fit; dependency fit unreviewed | Parsers, models, URLs, dependencies, private documents | `needs_more_info` |
| WebODM offline aerial mapping portfolio | 4 | High visual portfolio and client-story value | High | Good compute fit; architecture unverified | Location privacy, AGPL, containers, data rights, accuracy | `ready_for_review` |
| SatDump offline satellite-data learning | 3 | Niche direct value; useful field-data pattern | High | Offline macOS path declared but unverified | Stale release, binaries, radio law, storage, hardware | `needs_more_info` |

## Project Cost Estimates

| Project | Cost scope | Cost as of | Source checked | Price valid until | Incremental cost | From-scratch prototype | Portfolio build | DIY effort | Recurring cost | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| llama-swap local model router | Static compatibility and threat-model spike | 2026-07-20 | 2026-07-20 | 2026-08-19 | $0-$25 | $0-$25 with general-purpose host | $0-$75 | 8-14h | $0/month | High cash, Medium effort |
| Docling ingestion compatibility spike | Five-format schema and dependency review | 2026-07-20 | 2026-07-20 | 2026-08-19 | $0-$25 | $0-$25 with host and safe sample shapes | $0-$100 | 10-18h | $0/month | High cash, Medium effort |
| WebODM offline aerial mapping portfolio | Dataset provenance, architecture, and output storyboard | 2026-07-20 | 2026-07-20 | 2026-08-19 | $0-$25 | $0-$50 with host and approved images | $50-$200 | 12-20h | $0/month | High software baseline, Medium presentation, Low processing effort |
| SatDump offline satellite-data learning | Offline pipeline design; optional receiver later | 2026-07-20 | 2026-07-20 | 2026-07-27 | $0-$25 | $0-$25 with host and approved recording | $60-$180 optional receive-only kit | 8-14h design; 16-30h hardware path | $0-$3/month | High design cash, Medium effort, Low hardware |

Cost assumptions and exclusions:

- Software/design MVPs reuse confirmed lab compute and exclude installation,
  execution, model files, dedicated hosts, cloud services, and paid support.
- WebODM assumes an existing, sanitized image set and excludes drones, cameras,
  flight, surveying, travel, cloud processing, taxes, and vendor print quotes.
- SatDump starts with synthetic metadata or an explicitly approved recording.
  The optional receiver range is low confidence and excludes specialist
  antennas, mounting, weatherproofing, tax, and shipping.

Price sources:

- llama-swap: https://github.com/mostlygeek/llama-swap, checked 2026-07-20.
- Docling: https://github.com/docling-project/docling, checked 2026-07-20.
- WebODM: https://github.com/WebODM/WebODM, checked 2026-07-20.
- SatDump: https://github.com/SatDump/SatDump, checked 2026-07-20.
- Optional RTL-SDR receiver: https://www.rtl-sdr.com/rtl-sdr-blog-v4-dongle-initial-release/, checked 2026-07-20; old observation requiring refresh.

Refresh notes:

- Refresh software estimates after a material license, release, dependency,
  telemetry, or execution-boundary change.
- Refresh SatDump hardware by 2026-07-27 because its price source is old.
- An unchanged price refresh alone does not qualify an item for another daily
  delta report.

## Effort-Versus-Value View

### Weekend Projects

| Project | Cash | DIY hours | Learning value | Business value | Risk |
| --- | --- | --- | --- | --- | --- |
| llama-swap architecture spike | $0-$25 | 8-14h | High | High | Medium command, log, and process-boundary risk |
| SatDump offline explainer | $0-$25 | 8-14h | High | Medium | Medium legal, provenance, and binary-review burden |

### Sub-$300 Builds

| Project | Cash | DIY hours | Learning value | Business value | Risk |
| --- | --- | --- | --- | --- | --- |
| Docling compatibility spike | $0-$25 | 10-18h | High | High | Medium-high dependency and document risk |
| WebODM design and case-study plan | $0-$50 | 12-20h | High | High | Medium-high privacy, license, and accuracy risk |
| SatDump optional receive-only portfolio path | $60-$180 | 16-30h | High | Medium | High until hardware, law, and release status are reviewed |

### Larger Portfolio Investments

No new item requires more than $300 for its smallest credible planning MVP.
Actual WebODM field capture, licensed survey work, or a permanent satellite
station would be separate projects with new approvals and fresh pricing.

## MVP Action Cards

### llama-swap local model router

| Field | Value |
| --- | --- |
| One-week deliverable | Provider compatibility matrix, lifecycle diagram, failure-state storyboard, and command/logging threat model. |
| Success criteria | Two provider shapes, process start/stop behavior, logging, failure handling, and approval boundaries are explicit. |
| Expected demo artifact | Markdown architecture note, sanitized configuration sketch, and static dashboard flow. |
| Prerequisites | Approval for design-only work and selection of two existing provider shapes. |
| First three tasks | 1. Map existing provider and model-role boundaries. 2. Diagram process, port, timeout, and failure behavior. 3. Draft a sanitized configuration sketch and threat checklist. |
| Blockers | Provider lifecycle behavior, loopback port policy, logging requirements, and overlap with existing CLI orchestration. |
| Stop conditions | Stop for non-loopback exposure, unreviewed hooks, prompt leakage, or an architecture change without an architecture decision record. |
| Safety notes | No binary, package, model, command, hook, server, network listener, or benchmark execution is approved. |

### Docling ingestion compatibility spike

| Field | Value |
| --- | --- |
| One-week deliverable | Five-format compatibility matrix, metadata map, ten parser failure cases, and dependency/model checklist. |
| Success criteria | Each format has expected structure, citation metadata, failure handling, and explicit model, network, and dependency gates. |
| Expected demo artifact | Markdown design note, sanitized input/output examples, fixture inventory, and static ingestion flow. |
| Prerequisites | Approval for design-only work and confirmation that sample shapes are safe to describe. |
| First three tasks | 1. Select five sanitized document shapes and desired outputs. 2. Map proposed fields to current ingestion and citation metadata. 3. Draft failure fixtures and dependency, model, and network gates. |
| Blockers | Optional-model behavior, cache paths, dependency size, parser sandboxing, and chunking compatibility. |
| Stop conditions | Stop for private-file processing, URL fetching, model downloads, dependencies, or architecture expansion without approval. |
| Safety notes | No document, URL, package, model, parser, service, or MCP execution is approved. |

### WebODM offline aerial mapping portfolio

| Field | Value |
| --- | --- |
| One-week deliverable | Dataset provenance checklist, offline processing diagram, four-output storyboard, and client-style case-study outline. |
| Success criteria | The design identifies an approved image source, useful outputs, privacy redactions, compute assumptions, and a no-flight boundary. |
| Expected demo artifact | Markdown case-study plan, static output mockups, data lineage sheet, and risk checklist. |
| Prerequisites | Approval for design-only work and a sanitized image source with local-processing and portfolio rights. |
| First three tasks | 1. Define the mapping question and image provenance. 2. Diagram local processing, storage, and four output types. 3. Draft privacy controls and the narrated storyboard. |
| Blockers | Approved imagery, architecture support, storage, engine behavior, AGPL obligations, and output accuracy. |
| Stop conditions | Stop for live flight, restricted-site imagery, private coordinates, cloud processing, unapproved containers, or survey-grade claims. |
| Safety notes | No drone purchase, flight, control, telemetry, surveillance, installation, execution, or publication is approved. |

### SatDump offline satellite-data learning

| Field | Value |
| --- | --- |
| One-week deliverable | Plain-language weather-satellite pipeline explainer, storage worksheet, provenance schema, six safety cases, and output storyboard. |
| Success criteria | Recording-to-output stages, storage, approved provenance, and boundaries against transmission and private interception are explicit. |
| Expected demo artifact | Markdown explainer, synthetic metadata fixtures, storage table, and static decoded-output mockups. |
| Prerequisites | Confirm jurisdiction, receive-only intent, SDR inventory, and an approved public or synthetic recording source. |
| First three tasks | 1. Select one public weather-satellite pipeline at a metadata level. 2. Map recording, storage, decoding, and outputs. 3. Draft provenance, legal, privacy, and hardware review gates. |
| Blockers | Release freshness, binary provenance, Mac architecture, SDR inventory, approved recordings, local rules, antenna scope, and storage. |
| Stop conditions | Stop for private or encrypted signals, transmission, unsafe antenna work, unapproved recordings, unclear law, or unverified binaries. |
| Safety notes | No reception, transmission, interception, antenna work, bias power, package, binary, or repository execution is approved. |

## Ready For Eval

No model is ready for evaluation from this metadata-only scan.

## Watchlist

| Candidate | Reason | Retest or revisit trigger |
| --- | --- | --- |
| Lemma 8B GGUF and MLX | Practical local size and explicit Apple Silicon metadata, but artifact, license, provenance, and benchmark lanes are incomplete. | Exact artifact/hash, license chain, runtime, text context cap, and approved text or multimodal fixture. |
| Docling ingestion compatibility spike | Strong RAG relevance, but parser, model, network, and dependency scope require static review. | Dependency/model inventory and five-format schema map approved. |
| SatDump offline satellite-data learning | Strong learning value, but tagged release freshness, data provenance, law, hardware, and binary review are unresolved. | Current artifact review, approved recording, jurisdiction, storage, and inventory confirmed. |

## Skips

No normalized item was marked `skip`; 34 lower-signal, overlapping, or
impractical source-set items were not promoted into candidate records.

## Import Or Task Notes

- Registry updates: none; each model or project requires separate approval.
- Benchmark follow-ups: Lemma needs exact-artifact security review and separate
  text and multimodal fixture decisions before any local run.
- Dashboard follow-ups: none; dashboard and registry import paths were not
  changed.
- Open questions: confirm SDR and drone inventory, maximum DIY hours,
  portfolio budget, preferred document formats, and whether local model routing
  is a higher priority than ingestion review.

## Safety Posture

- Metadata-only boundaries: public pages and repo-local planning artifacts only.
- Registry changes: none to model or project CSV files.
- Downloads, installs, execution, APIs, and secrets: none. No model, package,
  binary, repository, document, aerial imagery, or radio recording was
  downloaded or run; no API, key, secret, purchase, reception, transmission,
  flight, control, or dashboard decision occurred.

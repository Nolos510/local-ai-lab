# AI Lab Radar Report

Date: 2026-06-05
Reviewer: Codex
Source packet: `automations/ai-lab-radar/inputs/2026-06-05-github-project-radar.md`

## Summary

- Projects reviewed: 10
- Ready for review: 8
- Watchlist: 2
- Skipped: 0
- Needs more information: 0

This report creates a GitHub Project Radar lane for popular AI and business
workflow repositories. It is based on public GitHub metadata only. It does not
clone repositories, install packages, run software, add dependencies, create
API keys, create model scores, or create model decisions.

## Project Review

| Project | Source signal | Why interesting | Risk notes | Recommended next step |
| --- | --- | --- | --- | --- |
| n8n | 191k observed stars; native AI workflow automation metadata | Best business-automation tie-in for turning lab outputs into operations. | Fair-code/Sustainable Use licensing needs review. | `ready_for_review` |
| Dify | 144k observed stars; agentic workflow/RAG/app platform metadata | Strong product reference for AI app workflow and observability. | Large footprint and extra license conditions. | `ready_for_review` |
| Open WebUI | 140k observed stars; self-hosted local LLM UI metadata | Strong companion UI for Ollama/local model winners. | Branding/license history needs review. | `ready_for_review` |
| ComfyUI | 116k observed stars; diffusion graph GUI/backend metadata | Adds a creative/business media lane opportunity. | GPL and media-model operational footprint need review. | `ready_for_review` |
| llama.cpp | 115k observed stars; local inference, Apple Silicon, quantization metadata | Directly strengthens large local-model benchmarking, especially with 256 GB RAM. | Install/download work must remain an explicit follow-up. | `ready_for_review` |
| browser-use | 97.4k observed stars; AI browser automation metadata | Useful for research, lead gen, competitive scans, and browser QA. | Browser automation needs sandboxing and data controls. | `ready_for_review` |
| RAGFlow | 82k observed stars; RAG plus agent context engine metadata | Useful reference for document-heavy business knowledge workflows. | Heavier service footprint than the current dashboard. | `ready_for_review` |
| OpenHands | 75.9k observed stars; AI-driven development metadata | Reference product for coding-agent workflows and repo automation. | Full app stack and enterprise boundaries need review. | `ready_for_review` |
| AutoGen | 58.7k observed stars; multi-agent framework metadata | Historically useful multi-agent reference. | Source page says it is in maintenance mode. | `watchlist` |
| CrewAI | 52.9k observed stars; multi-agent orchestration metadata | Useful for business-process agent simulations. | Telemetry/provider assumptions need review. | `watchlist` |

## Ready For Review

| Project | Review focus | Dashboard notes |
| --- | --- | --- |
| n8n | Workflow automation handoffs and business process integration. | Project-only. Do not add dependency or webhook behavior yet. |
| Dify | Product UX and workflow-builder reference. | Project-only. Do not turn into dashboard dependency. |
| Open WebUI | Local model UI and Ollama companion path. | Project-only. Could link benchmark winners to local UI launch tasks later. |
| ComfyUI | Creative/media workflow lane. | Project-only. Separate from LLM scoring. |
| llama.cpp | Large GGUF runtime path and local benchmark runner hardening. | Project-only. Strong first runtime review target. |
| browser-use | Browser automation benchmark and business task lane. | Project-only. Needs sandbox and auth rules. |
| RAGFlow | RAG architecture and source-grounded business workflows. | Project-only. Consider tiny local RAG benchmark first. |
| OpenHands | Coding-agent competitor/reference workflow. | Project-only. Useful for future coding-agent benchmark design. |

## Watchlist

| Project | Reason | Revisit trigger |
| --- | --- | --- |
| AutoGen | Maintenance-mode notice makes it less attractive for new integration work. | Revisit after reviewing Microsoft Agent Framework as successor. |
| CrewAI | Popular, but provider and telemetry assumptions need local-first review. | Revisit after checking local-provider support and telemetry controls. |

## Import Or Task Notes

- Registry updates: add the 10 project-only rows to
  `data/project_registry/github_repos.csv`.
- Dashboard follow-up: add `/projects` and a Lab Dashboard `GitHub Project
  Radar` section.
- Model-size update: the 256 GB RAM machine should make 24B/30B and some larger
  GGUF/MLX candidates legitimate evaluation targets once runtime/artifact paths
  are selected. Size alone should not demote a model; unclear artifact/runtime
  should.
- Boundary: project radar does not create model benchmark scores, final labels,
  or model decisions.

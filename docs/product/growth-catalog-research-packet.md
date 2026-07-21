# Growth / Skills Lab — Catalog Research Packet (Claude)

Source-backed curation for Codex to translate into `skills.json`, `extensions.json`,
`learning.json`. Ranking is deterministic: **Now / Next / Later / Watch / Blocked**.
Review states: **unreviewed / metadata_reviewed / trial_approved / blocked / retired**.
Career lenses: **AIA** (AI application eng), **AUT** (automation builder), **MLD** (ML/data eng).
Nothing here is an install approval; `metadata_reviewed` means the *facts* were checked, not that the tool is trusted.

Provenance verified 2026-07-20. URLs marked `⚠verify` need Codex to confirm the canonical link before catalog promotion.

---

## SKILLS (7)

Repo-owned skills live in `skills/`; treat as `installed`. `evidenced` only where a repo artifact proves use.

| id | type | status | lens | practical value | marketability | proof project | review |
|---|---|---|---|---|---|---|---|
| `skill-code-review` | skill | Now (evidenced) | AIA | Already used to gate diffs here | "Rigorous AI-assisted review" | Publish a review checklist + before/after | metadata_reviewed |
| `skill-local-llm-eval` | skill | Now (evidenced) | MLD | Drives the benchmark harness | "LLM evaluation engineer" | The v0.2 eval report | metadata_reviewed |
| `skill-local-provider-troubleshooting` | skill (candidate) | Now | AUT | Codifies the LM Studio/Ollama/401 pain you hit repeatedly | "Local inference ops" | A runbook skill + fixture | unreviewed |
| `skill-plugin-security-review` | skill (candidate) | Next | AIA/AUT | Powers *this feature's* "safe?" review — dogfood it | "AI supply-chain security" | A skill that emits the risk-facts for one MCP | unreviewed |
| `skill-rag-eval-design` | skill (candidate) | Next | MLD | You have the RAG+eval infra; formalize the method | "RAG evaluation" | v0.2 recall/MRR writeup | unreviewed |
| `skill-mcp-server-authoring` | skill (candidate) | Next | AIA | **Blind-spot add:** building your own MCP beats installing others'; you'll expose `ai-lab` anyway | "MCP/tool integration" | An MCP server wrapping `ai-lab` commands | unreviewed |
| `skill-bounded-automation-review` | skill (candidate) | Later | AUT | Reviews loop/automation safety (your integrator pattern) | "Safe agent orchestration" | SOP doc for the pilot-and-verify loop | unreviewed |

*Dropped from Codex's list:* `skill-quality-audit` folds into `skill-code-review` scoped to skills — not a separate skill yet. `seo-audit` stays in the repo but is **Later/low-priority** (least AI-lab-relevant).

---

## EXTENSIONS — plugins / MCP / connectors (11)

**Critical framing:** this lab's identity is *local-first*. I rank by **local-lab fit first**, market-signal second. A large slice of the proposed list (Temporal, Sentry, PostHog, Cloudflare, Vercel, Atlassian) is cloud/ops/enterprise tooling that levels up *general SWE*, not a local AI lab — those are **Later/Watch**, not front-loaded.

### Strong local-lab fit — Now / Next
| id | kind | official? | status | lens | value | key risk facts | proof | review |
|---|---|---|---|---|---|---|---|---|
| `ext-semgrep-mcp` | mcp | official ([semgrep/mcp](https://github.com/semgrep/mcp)) | **Now** | AIA/MLD | Security-first lab; scan before ship | local scan; low network; read-only | Add as a pre-ship gate | metadata_reviewed |
| `ext-context7` | mcp | OSS ([upstash/context7](https://github.com/upstash/context7)) | **Now** | AIA | Live version-correct docs = fewer wrong-API loops | network (doc fetch); no creds; read-only | dev accelerant | metadata_reviewed |
| `ext-chrome-devtools-mcp` | mcp | official ([ChromeDevTools](https://github.com/ChromeDevTools/chrome-devtools-mcp)) | **Now** | AIA | Real-browser dashboard verification | local browser control; page data exposure | Automate a dashboard visual check | metadata_reviewed |
| `ext-hf-mcp` | mcp | official, **beta** ([hf.co/mcp](https://huggingface.co/settings/mcp) ⚠verify) | **Next** | MLD | Model/dataset discovery — core to a model lab | network; HF token scope; rate limits | Wire HF discovery into the model radar | metadata_reviewed |
| `ext-playwright-mcp` | mcp | official ([microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp)) | **Next** | AIA | Scripted E2E dashboard tests | local browser; can navigate anywhere | E2E smoke suite | metadata_reviewed |
| `ext-github-mcp` | mcp | official ([github/github-mcp-server](https://github.com/github/github-mcp-server)) | **Next** | AUT | Release/issue ops for the now-public repo | **network + writes**; PAT scope critical | Automate a release | unreviewed |

### Weak local-lab fit — challenge / relegate (Later / Watch)
| id | kind | official? | status | why relegated |
|---|---|---|---|---|
| `ext-supabase-mcp` | mcp | official | Later | Only if the dashboard outgrows SQLite; adds a cloud DB + write scope. Not now. |
| `ext-cloudflare-mcp` / `ext-vercel-mcp` | mcp | official | Later | Deployment tooling; the lab runs locally. Revisit only when publishing the dashboard. |
| `ext-sentry-mcp` / `ext-posthog-mcp` | mcp | official | Later | Ops/analytics; tangential to a local lab. General-SWE marketability only. |
| `ext-temporal` | mcp | **community only** | Watch | Durable workflows = heavy infra for marginal local-lab benefit; unofficial MCP = higher supply-chain risk. Challenge including it at all. |
| `ext-atlassian-rovo` | connector | official | Watch | Enterprise Jira/Confluence; low personal-lab fit. |
| `ext-gdrive` / `ext-zotero` / `ext-scite` | connector | mixed | Watch | Research/RAG-ingestion *maybe* useful, but pull **private data** into agent reach — review-only with explicit data-scope. |

### High-risk lane — Blocked (review-only, per plan)
`ext-email`, `ext-calendar`, `ext-sharepoint`, `ext-box`, `ext-teams`, `ext-finance`, `ext-trading`, any **write-capable** MCP → **Blocked**: broad private-data + write + credential risk. Graduate only via a dedicated threat-review patch pinning exact version+scope, then two-step + typed-ID confirm.

---

## LEARNING (13) — proof-project-first; certs are supporting evidence

| id | type | platform | status | cost | proof artifact | url |
|---|---|---|---|---|---|---|
| `ln-anthropic-academy` | course | Anthropic | **Now** | free | Apply one Claude/MCP technique in the lab | [skilljar](https://anthropic.skilljar.com/) ⚠verify |
| `ln-dlai-eval-agents` | lesson | DeepLearning.AI | **Now** | free | Offline agent-eval fixture (you have the infra) | [dlai](https://www.deeplearning.ai/short-courses/) ⚠verify exact course |
| `ln-hf-mcp-course` | course | Hugging Face | **Now** | free | Build an MCP server exposing `ai-lab` | [hf mcp-course](https://huggingface.co/learn/mcp-course/unit0/introduction) |
| `ln-anthropic-agents` | reading | Anthropic | **Now** | free | Informs your loop design | [building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| `ln-hf-agents-course` | course | Hugging Face | Next | free | Rebuild one loop in a framework | [agents-course](https://huggingface.co/agents-course) |
| `ln-ibm-rag-agentic` | cert | Coursera/IBM | Next | sub | RAG eval report | [coursera](https://www.coursera.org/professional-certificates/ibm-rag-and-agentic-ai) |
| `ln-datacamp-assoc-aieng` | track | DataCamp | Next | sub | Portfolio project | [datacamp](https://www.datacamp.com/tracks/associate-ai-engineer-for-developers) |
| `ln-google-genai-intro` | track | Google | Next | free | Cloud GenAI demo | [skills.google/118](https://www.skills.google/paths/118) ⚠verify |
| `ln-openai-academy` | course | OpenAI | Next | free | Cross-vendor agent fluency | [academy.openai.com](https://academy.openai.com/pages/courses) |
| `ln-lf-mcpa` | cert | Linux Foundation | Watch | paid | MCP server + threat model | [MCPA](https://training.linuxfoundation.org/certification/model-context-protocol-associate-mcpa/) — availability pending |
| `ln-github-copilot-cert` | cert | GitHub | Later | paid | Narrow; supporting only | ⚠verify |
| `ln-jhu-agentic` | cert | Johns Hopkins | Later | paid$$ | Deep but expensive; supporting | [jhu](https://online.lifelonglearning.jhu.edu/jhu-certificate-program-agentic-ai) |
| `ln-aws-google-ml-eng` | cert | AWS / Google | Later | paid | Only after cloud hands-on evidence exists | ⚠verify |

*Dropped/down-ranked:* NVIDIA NCP-AAI → Later (vendor cert, low signal vs free hands-on). JHU/AWS/Google-Pro certs → Later per the plan's own proof-first rule.

---

## Challenges & blind spots (my critical read)

1. **The extension list leans cloud/ops.** ~6 of the proposed connectors (Temporal, Sentry, PostHog, Cloudflare, Vercel, Atlassian) don't serve a *local* AI lab — front-loading them dilutes the local-first identity. Relegated to Later/Watch above. The Now/Next set is deliberately model-lab-shaped (HF, Semgrep, Chrome/Playwright, Context7, GitHub).
2. **Certs are over-weighted as "credentials."** The plan's own proof-project-first principle should push pure certs (JHU, NVIDIA, AWS, GitHub) *below* free hands-on courses that emit artifacts. Applied above.
3. **Missing: MCP-server authoring as a first-class skill.** Building your own MCP (to expose `ai-lab`) is higher marketability than installing others' and is the natural next step. Added.
4. **"Evidenced" must require an artifact path, not self-attestation** — for skills, a commit using it; for learning, the committed proof project. Otherwise the whole "installed ≠ used" rigor collapses.
5. **The private-data connectors (Google Drive, Zotero, email/docs) are the risk sleepers** — "useful" but they pull private content into agent reach. Keep review-only with an explicit data-scope acknowledgement, never auto-enabled.

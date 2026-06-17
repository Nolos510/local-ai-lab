# AI Lab OS Learning Roadmap

This roadmap turns the repo into a study plan. Each module maps directly to a
working part of the project, so learning produces portfolio evidence.

## Track 1: Local AI Runtime Fundamentals

Goal: understand how local models are discovered, loaded, and called.

- Learn LM Studio CLI and OpenAI-compatible local server behavior.
- Learn Ollama inventory, model naming, and endpoint behavior.
- Learn GGUF, MLX, Safetensors, quantization, context windows, and model IDs.
- Compare LM Studio, Ollama, llama.cpp, and MLX-LM as runtime choices.

Portfolio evidence:

- Inventory screenshots.
- Runtime notes.
- One successful benchmark artifact per runtime, when available.

## Track 2: Benchmarking And Evaluation

Goal: evaluate models with evidence instead of vibes.

- Study the prompt suite in `evals/local-llm-benchmark/prompts`.
- Preserve raw responses before scoring.
- Separate draft score suggestions from confirmed human scores.
- Learn how final labels map to daily-driver, specialist, watchlist, retest,
  or skip decisions.

Portfolio evidence:

- Two confirmed model benchmark artifacts.
- Compare page screenshot.
- Written evaluation summary explaining strengths and weaknesses.

## Track 3: RAG And Retrieval Quality

Goal: build a useful private document assistant lane.

- Run ingestion and chunking on sample documents.
- Understand embedding model choice and vector size.
- Measure retrieval failures before adding reranking.
- Improve citation and source metadata.

Portfolio evidence:

- Retrieval evaluation fixture.
- Before/after answer comparison.
- Citation quality notes.

## Track 4: Model Security And Due Diligence

Goal: safely decide what is worth downloading or running.

- Review provenance, license, artifact format, and publisher chain.
- Record checksum/hash status where available.
- Avoid model-card code, notebooks, install scripts, and custom loaders unless
  explicitly reviewed.
- Separate external radar leads from approved local candidates.

Portfolio evidence:

- Formal security review for Dolphin-Mistral 24B.
- One approved model artifact review.
- One blocked/watchlist model with clear rationale.

## Track 5: Dashboard And Product UX

Goal: make technical evidence legible to future users, employers, and yourself.

- Explain demo data versus real benchmark imports.
- Make candidate -> artifact -> imported run -> decision links obvious.
- Keep write actions disabled by default unless explicitly enabled.
- Turn reports into plain-English interpretation.

Portfolio evidence:

- Screenshots in `docs/assets/screenshots`.
- Case study in `docs/portfolio-case-study.md`.
- Architecture diagram in `docs/architecture.md`.

## Track 6: Business And Automation Tie-Ins

Goal: connect the lab to useful real-world workflows.

- Review GitHub project radar entries by priority and local fit.
- Study n8n, Open WebUI, llama.cpp, RAGFlow, browser-use, and OpenHands as
  possible references or integrations.
- Decide which projects support business workflows, learning, or product
  differentiation.

Portfolio evidence:

- Project radar review note.
- One small prototype or runbook that uses benchmark decisions.
- Resume bullets that explain product/business impact.

## 30-Day Push

Week 1:

- Finish second benchmark or document why it is blocked.
- Add v1 screenshots and case study.
- Push and tag only when the release definition is explicit.

Week 2:

- Add retrieval evaluation fixtures.
- Improve citation/source metadata.
- Write one RAG quality report.

Week 3:

- Complete a model security review and approve or block one large model.
- Try one new runtime path only after approval.

Week 4:

- Package portfolio story.
- Record a short demo script.
- Convert the strongest work into resume bullets and interview talking points.

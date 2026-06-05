# Summary

Describe what changed and why.

## Scope

- [ ] I read `AGENTS.md`
- [ ] I kept the change task-scoped
- [ ] I did not add forbidden v0 features

## Architecture Impact

Describe any impact on runtime boundaries, provider abstractions, Qdrant, Docker, local model runtimes, or v0 scope.

- [ ] No architecture direction changed
- [ ] Architecture change is documented in an ADR, if applicable

## Files Changed

List the most important files or directories changed.

## Tests Run

List tests run and results.

## Commands Run

List commands run and results.

- [ ] `uv sync`
- [ ] `docker compose config`
- [ ] `uv run ruff check .`
- [ ] `uv run pytest`
- [ ] `uv run local-ai-lab doctor`
- [ ] `uv run local-ai-lab ingest --path data/sample_docs`
- [ ] `uv run local-ai-lab ask "What is this lab for?"`
- [ ] I documented commands that could not be run

## Privacy/Security Review

- [ ] I did not introduce hidden cloud dependencies
- [ ] I did not commit secrets
- [ ] `.env.example` contains only safe placeholder values
- [ ] Logs do not dump private documents, prompts, retrieved chunks, API keys, or private paths by default

## Documentation Updated

- [ ] I updated docs if behavior changed
- [ ] I updated `.env.example` if config changed

## Test Coverage

- [ ] I added/updated tests where appropriate
- [ ] I explained why tests were not needed, if applicable

## Known Limitations

Describe what was not implemented, not tested, or intentionally deferred.

## Screenshots/Logs

Add screenshots or short logs if relevant. Do not paste secrets, private documents, full prompts, or sensitive local paths.

# Future Cloud Portability

The local lab should not be cloud-first, but it should avoid trapping itself.

## Stable Boundaries

- API layer: FastAPI.
- Vector store: Qdrant.
- Model provider: provider interface with Ollama and OpenAI-compatible clients.
- Data pipeline: source documents, chunk metadata, and dataset hashes.

## Future Portability Work

- [ ] Add production Dockerfile for the FastAPI harness.
- [ ] Add cloud Qdrant profile.
- [ ] Add hosted OpenAI-compatible provider profile.
- [ ] Add secrets handling and deployment notes.
- [ ] Add observability profile.

Cloud portability should be added only after the local loop is useful and measured.

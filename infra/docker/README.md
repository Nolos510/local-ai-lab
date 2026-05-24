# Docker Infrastructure

Docker is used for local infrastructure services only in v0.

## Services

- Qdrant: vector search at `http://localhost:6333`
- Open WebUI: browser UI at `http://localhost:8080`

## Commands

```bash
docker compose up -d qdrant open-webui
docker compose logs -f qdrant
docker compose down
```

Model runtimes stay native on macOS by default.

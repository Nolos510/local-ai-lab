.PHONY: sync test lint format compose-config services-up services-down api ingest ask

sync:
	uv sync

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

compose-config:
	docker compose config

services-up:
	docker compose up -d qdrant open-webui

services-down:
	docker compose down

api:
	uv run uvicorn local_ai_lab.api.app:create_app --factory --reload

ingest:
	uv run local-ai-lab ingest --path data/sample_docs

ask:
	uv run local-ai-lab ask "What is this lab for?"

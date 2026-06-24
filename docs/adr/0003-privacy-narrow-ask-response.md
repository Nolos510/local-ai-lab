# ADR 0003: Privacy-Narrow `/ask` Response Shape

Status: accepted

Date: 2026-06-16

## Context

AI Lab OS is local-first, and AGENTS.md requires that logs and default outputs do
not dump user documents, prompts, retrieved chunks, API keys, or private paths.
The `/ask` API originally exposed enough retrieval detail for debugging, but
that shape also made raw retrieved text, source paths, and previews part of the
normal response surface.

That default is too broad for a private RAG lane. Consumers should receive the
answer and stable citation identifiers, while raw chunk inspection remains a
separate explicit diagnostic workflow.

## Decision

The `/ask` API response returns:

- `answer`
- `citations`

Each citation includes:

- `source_name`
- `chunk_index`

The response no longer returns `retrieved_chunks`. Citation objects no longer
include `chunk_id`, `score`, `source_path`, or `preview`.

`top_k` is capped at 20 at the API and settings boundaries to keep retrieval
scope explicit.

RAG Quality R4 added explicit local retrieval inspection via
`inspect_retrieval` / `--inspect-retrieval`. That inspection path can include
retrieved chunk text, scores, and chunk IDs for local debugging. It is opt-in
and remains outside the default `/ask` response.

## Consequences

This is a breaking privacy change for clients that depended on raw retrieval
payloads or source paths from `/ask`.

The default API surface is safer for private local documents because answers can
cite stable chunk/source names without echoing raw retrieved content or private
filesystem paths.

Retrieval inspection is now an explicit local diagnostic workflow with separate
tests proving the default response remains privacy-narrow.

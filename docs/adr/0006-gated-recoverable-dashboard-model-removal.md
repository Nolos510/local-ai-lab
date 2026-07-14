# ADR 0006: Gated Recoverable Dashboard Model Removal

Status: accepted

Date: 2026-06-18

## Context

The dashboard has been read-only by default, with explicit exceptions for local
run-test and artifact-import actions that are disabled unless the server is
started with action flags. The Installed Models page now exposes local runtime
inventory, including filesystem-only LM Studio folders that may be stale
leftovers. Removing those folders from the dashboard is useful, but it crosses a
safety boundary because it mutates local runtime state.

## Decision

Add model removal as an explicitly gated dashboard action:

- disabled by default and enabled only with `--enable-delete-actions`;
- available only through the existing localhost-bound dashboard server and
  action-token POST gate;
- two-step confirmed: the first POST renders a confirmation page, and only the
  second confirmed POST performs removal;
- resolved server-side from the current inventory cache by a generated row key,
  never from a client-supplied absolute path;
- path-contained to `~/.lmstudio/models` for LM Studio and the Hugging Face hub
  cache root for MLX-LM snapshots before any subprocess runs;
- LM Studio folders are moved to macOS Trash through Finder via `osascript`;
- MLX-LM snapshot folders are moved to macOS Trash through the same guarded
  path;
- Ollama models are removed through `ollama rm <model_id>` using the validated
  exact inventory id and do not require a manifest path;
- no direct recursive delete or `rm -rf` is used.

The scanner also skips LM Studio filesystem-only folders that contain no real
weight file, such as `.DS_Store`-only or metadata-only leftovers.

## Consequences

The dashboard remains safe-by-default. Operators must opt in at server start,
refresh inventory manually, review an exact confirmation page, and then confirm
the removal. LM Studio and MLX-LM removal is recoverable through Trash. Ollama
removal is delegated to the runtime CLI so its index and shared blob store
remain consistent.

This action does not download models, run benchmarks, call cloud APIs, use
secrets, or add dependencies. Tests fake all subprocesses and do not remove real
local files.

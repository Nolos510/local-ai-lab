# Unified AI Lab CLI Decision

The `ai-lab` console script is a thin stdlib-only coordinator over existing
boundaries. Status and radar commands read local CSV, SQLite, and artifact
state. Benchmark preparation delegates to the existing harness, while import,
report, and dashboard commands dispatch to the existing dashboard entry point.

The command does not download a model, contact a model or cloud API, add a
secret, or execute inference implicitly. It supplies one teachable operating
surface without becoming a replacement benchmark engine, dashboard, or RAG
runtime.

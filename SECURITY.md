# Security

## Local-First Rules

- Do not require API keys for the MVP.
- Do not call cloud services from the dashboard.
- Do not download models automatically.
- Do not run models automatically.
- Keep generated SQLite databases and CSV exports local.
- Treat benchmark outputs and local notes as user data.

## Secrets

No secrets are needed for the current dashboard. Future integrations must keep credentials out of Git and use local environment files or OS keychain-style storage where appropriate.

## Model and Tool Caution

Open-weight model links, benchmark scripts, MCP tools, and automation jobs should be treated as untrusted until reviewed. Future radar automation should record candidates for review rather than installing or executing them.

## Future MCP Guidance

Before adding MCP servers or broader agent permissions:

- Document the tool purpose and data it can access.
- Prefer read-only access first.
- Keep write permissions scoped to the minimum path needed.
- Record new permissions in this file and in `DECISIONS.md`.
- Review any tool that can access browsers, shells, files outside the repo, or private accounts.

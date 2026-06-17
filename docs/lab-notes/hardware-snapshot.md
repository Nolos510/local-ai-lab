# Hardware Snapshot

`ai-lab hardware snapshot` records sanitized local machine/runtime context for
benchmark evidence.

The command is read-only and does not start servers, call models, inspect model
inventory, download artifacts, or read environment variables. It reports stable
system facts such as OS, Python version, machine/processor, CPU count, optional
macOS `sysctl` chip and memory values, and optional runtime version strings for
local commands when present.

Use:

```bash
uv run ai-lab hardware snapshot
uv run ai-lab hardware snapshot --out docs/lab-notes/hardware-snapshot-local.json
```

`--out` must stay inside the repository. The JSON intentionally excludes
usernames, home directories, private paths, tokens, prompts, documents, and
model inventory.

# Runtime Profiles

Runtime profiles document how local model runtimes should be configured for v0. Docker remains limited to infrastructure services such as Qdrant and optional Open WebUI; model runtimes stay native on macOS.

## LM Studio

Use LM Studio when you want a desktop-managed local model exposed through an OpenAI-compatible API. LM Studio may run MLX models under the hood, but `local-ai-lab` communicates with it through HTTP.

Setup:

1. Start LM Studio.
2. Load the Qwen Coder model, or any other desired local model.
3. Start the LM Studio local server.
4. Inspect available model IDs:

```bash
curl -s http://localhost:1234/v1/models | uv run python -m json.tool
```

`python3 -m json.tool` also works on macOS when you are outside the `uv` workflow.

5. Copy one returned `id` value.
6. Set `.env`:

```bash
LOCAL_AI_LAB_LLM_PROVIDER=lm_studio
LOCAL_AI_LAB_LM_STUDIO_BASE_URL=http://localhost:1234/v1
LOCAL_AI_LAB_LM_STUDIO_MODEL="paste-model-id-here"
```

Do not include angle bracket characters in shell commands or `.env` values.

7. Verify:

```bash
uv run local-ai-lab doctor
uv run local-ai-lab ask "What is this lab for?"
```

## Ollama

Ollama remains supported as the default local runtime profile.

```bash
ollama list
ollama pull qwen3:14b
uv run local-ai-lab doctor
```

If `doctor` reports that `qwen3:14b` is missing, either pull it with Ollama or switch `LOCAL_AI_LAB_LLM_PROVIDER` to `lm_studio` and set `LOCAL_AI_LAB_LM_STUDIO_MODEL` to an ID returned by LM Studio.

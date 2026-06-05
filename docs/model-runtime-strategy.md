# Model Runtime Strategy

Use more than one runtime, but give each runtime a clear job.

## Native macOS Defaults

- Ollama: compatibility API and ergonomic model management.
- LM Studio: desktop model exploration and OpenAI-compatible local server.
- MLX / MLX-LM: Apple-native inference and fine-tuning experiments.
- llama.cpp: GGUF portability and low-level compatibility.

## v0 Policy

Docker does not own model runtimes in v0. Qdrant and Open WebUI run in Docker; model execution stays native so Apple Silicon acceleration paths remain straightforward.

## Future Serving Experiments

- Add vllm-metal only when concurrency or serving behavior requires it.
- Keep provider abstractions stable so cloud or hosted OpenAI-compatible endpoints can be tested later.

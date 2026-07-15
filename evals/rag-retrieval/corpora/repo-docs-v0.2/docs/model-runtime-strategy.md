# Model Runtime Strategy

Each native runtime has a distinct job. Ollama provides ergonomic model
management and a compatibility API. LM Studio supports desktop exploration and
a local OpenAI-compatible server. MLX/MLX-LM targets Apple-native inference and
experiments, while llama.cpp provides GGUF portability and low-level control.

Docker does not own inference in v0. It hosts Qdrant and optional Open WebUI,
leaving model execution native so Apple Silicon acceleration remains direct.
Serving experiments such as vllm-metal wait until concurrency requirements
justify them.

# Local AI Lab Sample Corpus

This local AI lab is a private Apple Silicon engineering workspace for building AI systems on a Mac Studio. It focuses on local inference, local retrieval, model benchmarking, MLX-LM fine-tuning experiments, Qdrant, Open WebUI, Ollama compatibility, LM Studio compatibility, evaluation harnesses, experiment tracking, and documentation.

The v0 architecture keeps infrastructure services in Docker and model runtimes native on macOS. Qdrant stores vectors for retrieval. Open WebUI provides a local browser chat surface. Ollama and LM Studio provide native local model endpoints. The FastAPI RAG harness runs through uv and exposes a small `/ask` endpoint.

The lab is privacy-first. Source documents, embeddings, retrieved chunks, prompts, and experiment outputs should stay on the workstation unless a future cloud portability profile explicitly says otherwise. Every serious experiment should record the model, runtime, dataset hash, prompt version, retrieved context, latency, and evaluation results.

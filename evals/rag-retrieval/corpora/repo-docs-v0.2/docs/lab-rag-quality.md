# RAG Quality Sprint Evidence

The first retrieval loop established an offline scorer for recall at k and MRR,
a deterministic fixture, local BGE-M3 embeddings, identity and optional
cross-encoder rerankers, opt-in hybrid retrieval, and privacy-narrow citations.
The committed repo-docs v0.1 corpus contained four queries.

That BGE-M3 run recorded recall@5 and MRR of 1.0. The result verifies the
collection and scoring path, but the tiny source-aware set is only a regression
baseline. It cannot establish whether lexical fusion or a second-stage ranker
improves difficult retrieval.

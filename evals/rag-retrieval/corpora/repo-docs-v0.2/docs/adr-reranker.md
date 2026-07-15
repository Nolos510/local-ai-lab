# Optional Local Reranker Decision

Reranking occurs after vector retrieval and before prompt assembly. Identity is
the default and preserves the first-pass order without dependencies. A local
cross-encoder is an explicit optional backend that requires the `[rerank]`
extra and a path to an already-present model artifact.

The backend lazy-imports its heavy transformer stack and requests local files
only. It must not resolve a remote model ID or download weights. This boundary
is removable: deleting the optional extra and cross-encoder implementation
must leave identity ranking, retrieval, and offline tests intact.

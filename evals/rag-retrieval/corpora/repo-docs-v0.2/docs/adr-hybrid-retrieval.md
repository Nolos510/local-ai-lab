# Hybrid Retrieval Decision

Dense Qdrant search remains the default. The opt-in hybrid mode combines dense
vector candidates with a local stdlib BM25-style lexical ranking over chunk
text, then joins the ranked lists with reciprocal-rank fusion. Qdrant remains
the vector database and source of stored chunks.

The lexical signal helps short exact terms, identifiers, and project-specific
vocabulary that vector similarity may miss. Hybrid retrieval selects and fuses
candidates first; the configured reranker is a separate later stage. No sparse
service, cloud call, model download, or new ranking dependency is introduced.

# RAG Reindexing And Inspection

Qdrant fixes vector dimensionality when a collection is created. Changing the
embedding provider, embedding model, or vector size requires recreating the
collection and ingesting the documents again. A dimension error means current
vectors do not match the existing index; use a new collection name when the
old experiment must be preserved.

Ordinary answers expose narrow citations only. An operator who needs to audit
retrieval can explicitly request local inspection to see chunk IDs, scores, and
text. That diagnostic output is private and must not enter default logs,
reports, or shared artifacts.

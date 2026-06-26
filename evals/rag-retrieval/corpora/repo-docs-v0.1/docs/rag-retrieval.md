# RAG Retrieval

The RAG backbone ingests Markdown and text files, chunks documents with source
metadata, embeds chunk text, stores vectors in Qdrant, retrieves top chunks, and
assembles a prompt with citations. Default citations expose `source_name` and
`chunk_index`.

Raw chunk text, retrieved scores, and chunk identifiers are exposed only through
an explicit local inspection flag for debugging. They are not part of the
default answer response.

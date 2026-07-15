# Privacy-Narrow Ask Response Decision

The default `/ask` response returns only the answer and citations. Each
citation contains `source_name` and `chunk_index`; it excludes chunk text,
previews, scores, chunk IDs, source paths, prompts, and keys. Retrieval breadth
is capped so the default surface remains explicit and narrow.

Local debugging has a separate `inspect_retrieval` or `--inspect-retrieval`
path. That deliberate opt-in can reveal retrieved text, scores, and chunk IDs,
but those details never become part of the ordinary API response.

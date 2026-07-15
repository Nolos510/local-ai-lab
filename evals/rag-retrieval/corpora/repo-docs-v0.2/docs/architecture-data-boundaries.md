# Architecture Data Boundaries

Radar creates leads, not scores. A security review can approve or block a
download or run decision. Benchmark artifacts preserve raw responses and
evidence notes before scoring, and confirmed scores remain separate from draft
local-judge suggestions. Demo rows are examples and stay hidden from real
views by default.

Dashboard SQLite files are local runtime state, not source truth. The durable
trail is the candidate registry, security review, benchmark artifacts,
dashboard CSV exports, and explicit keep, watchlist, retest, or skip decision.

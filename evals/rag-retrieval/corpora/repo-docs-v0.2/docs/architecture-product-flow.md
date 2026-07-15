# Dashboard And Benchmark Product Flow

A user-approved source packet becomes a candidate registry row. The security
review gate then asks whether an exact local runtime is approved. Unapproved
records stay queued or on a watchlist without benchmark scores. Approved
records can enter the benchmark harness, producing raw responses and evidence
before human-confirmed scores and decisions.

Confirmed artifacts are exported to dashboard CSVs and imported into SQLite
for lab, run, model, comparison, and report views. The workflow ends with an
explicit keep, watchlist, retest, or skip decision. Project opportunities live
in a separate project registry and never become model eval scores.

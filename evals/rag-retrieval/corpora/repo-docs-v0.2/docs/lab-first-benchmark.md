# First Local Benchmark Attempt

The first Qwen3 Coder artifact was a failed-runtime attempt, not a scored model
evaluation. LM Studio did not expose its local server, so no prompt ran and no
response was captured. The raw artifact recorded the runtime failure, while
the score export stayed empty.

No final capability label followed from missing evidence. The decision was
`retest`: start the local runtime successfully and capture the full prompt set
before judging the model. A prepared artifact, dashboard row, or installed
model never substitutes for observed responses.

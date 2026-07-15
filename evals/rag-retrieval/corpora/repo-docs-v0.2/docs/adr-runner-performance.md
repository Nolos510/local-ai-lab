# Local Runner And Performance Decision

All local runner lanes stay behind the same approval wrapper. The harness
records total latency around prompt captures, throughput only from clean
runtime statistics or reliable observed output-token counts, and RAM high-water
from local macOS sampling. Time to first token remains empty until a streaming
path measures it directly.

Values stay sparse when a runner cannot expose them honestly. The harness must
not infer memory pressure, swap behavior, token counts, throughput, or TTFT from
model size or marketing claims. It remains stdlib-only and never installs a
runtime, downloads a model, contacts a cloud model API, or adds a profiler.

# Approval-Gated Benchmark Execution Decision

Local inference is a material side effect: it can allocate memory, load a large
model, write raw responses, and import dashboard state. The sanctioned wrapper
therefore requires an explicit candidate, exact local model ID, runner, run ID,
and approval flag (or interactive `yes`).

Before any subprocess, endpoint request, score export, or dashboard import, the
preflight prints the complete execution identity and artifact targets. Missing
approval exits before work begins. Registry metadata may initialize a plan,
but it cannot prove runnable identity and never authorizes execution by itself.

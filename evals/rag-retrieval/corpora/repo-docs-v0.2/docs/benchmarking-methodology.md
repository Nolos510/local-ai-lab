# Local Benchmark Methodology

Comparable runs keep the same prompt set, exact model ID, quantization,
runtime, context and sampling settings, output limit, and hardware state.
Operators confirm the installed local artifact before execution and choose a
stable run ID. Planning never resolves or downloads a model.

Raw responses remain local evidence. A response is scored only against its
declared rubric dimensions; incomplete judge output is skipped rather than
replaced. Local-judge scores are drafts until human review confirms them.
Missing token, memory, or timing fields remain null, and run notes record
runtime versions or limitations that affect comparison.

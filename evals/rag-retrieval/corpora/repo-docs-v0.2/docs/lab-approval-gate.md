# Approval Gate Implementation Note

The execution command refuses to run unless the operator provides a candidate,
exact local model ID, runner, run ID, and explicit approval. Its preflight
enumerates the identity, prompt set, capture shape, artifact directory,
dashboard target, and CSV directory before local inference begins.

Without approval it exits before every harness subprocess, local endpoint,
dashboard import, and score export. Fake runners and endpoints cover that
negative guarantee. The machinery does not install runtimes, download models,
call cloud APIs, read secrets, or infer an executable identity from registry
metadata.

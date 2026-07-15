# Privacy-First Workflow Policy

Keep raw data, model artifacts, and generated reports in their designated local
areas. Run Qdrant and the optional chat UI locally while model processes remain
native on macOS. Logs may retain operational identifiers, template versions,
token counts, latency, and evaluation labels, but must not send secrets or
private raw documents to external services.

The normal ask API contains answer text and citation identifiers only. Raw
retrieved passages, previews, and private filesystem locations are excluded by
default and belong only in an explicitly requested local diagnostic view.

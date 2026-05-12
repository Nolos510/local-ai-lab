# Local Model Performance Report

Generated: 2026-05-12T15:00:32-07:00

## Summary

- Models tracked: 4
- Runs tracked: 4
- Eval score rows: 4
- Decisions logged: 4

## Ranked Models

| Model | Backend | Quant | Score | Label | Decision | Best use case |
| --- | --- | --- | ---: | --- | --- | --- |
| Qwen2.5-Coder 14B Instruct | llama.cpp | Q4_K_M | 81.36 | CODING_SPECIALIST | keep | Local coding and debugging |
| ResearchLite Local 7B | llama.cpp | Q5_K_M | 78.45 | RESEARCH_SPECIALIST | watchlist | Research synthesis and planning |
| Llama 3.1 Local 8B Instruct | llama.cpp | Q4_K_M | 77.09 | LOCAL_AI_ASSISTANT | keep | General local assistant tasks |
| TinyCoder Local 1.1B | llama.cpp | Q4_K_M | 70.27 | CODING_SPECIALIST | keep | Quick local coding checks |

## Install Decisions

| Model | Keep installed | Weakness | Retest condition |
| --- | --- | --- | --- |
| Llama 3.1 Local 8B Instruct | yes | Less specialized for coding than Qwen fixture | Retest after new local eval batch |
| Qwen2.5-Coder 14B Instruct | yes | Higher RAM use than smaller coding model | Retest after quantization refresh |
| ResearchLite Local 7B | yes | Slower than small coding model | Retest on larger local hardware |
| TinyCoder Local 1.1B | yes | Weak long-context synthesis | Retest after next TinyCoder quant refresh |

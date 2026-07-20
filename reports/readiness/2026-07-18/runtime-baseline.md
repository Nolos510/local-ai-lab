# Live Dashboard Runtime Baseline

Measured 2026-07-18 on the target Mac against
`d345266 + preserved working-tree patch`.

## Method

- Existing loopback dashboard process on `127.0.0.1:8765`.
- Ten warmed HTTP GET requests per route with no active benchmark batch.
- Server process sampled once per second for five seconds at idle.
- Response size is uncompressed HTML bytes.
- Results measure local server response time, not browser layout or paint time.

## Route Results

| Route | Median | Maximum | HTML size | Assessment |
|---|---:|---:|---:|---|
| `/` | 11.3 ms | 18.6 ms | 88.3 KiB | Fast |
| `/lab` | 26.2 ms | 27.0 ms | 201.5 KiB | Fast; payload is near the cockpit budget |
| `/runs` | 26.0 ms | 27.1 ms | 305.3 KiB | Fast server; payload exceeds dense-list budget |
| `/reviews` | 14.4 ms | 16.0 ms | 87.3 KiB | Fast |
| `/inventory` | 2.9 ms | 3.0 ms | 77.6 KiB | Fast |
| `/compare` | 2.0 ms | 2.2 ms | 132.0 KiB | Fast |
| `/reports` | 1.8 ms | 2.0 ms | 70.0 KiB | Fast |

The LM Studio model inventory endpoint responded in 1.8 ms, and Qdrant's
collection endpoint responded in 2.3 ms during the same pass.

## Process Footprint

| Measure | Result |
|---|---:|
| Resident memory | 26,896 KiB (26.3 MiB) |
| Idle CPU, five samples | 0.0% |
| Dashboard SQLite file | 69,632 bytes |

The macOS virtual-size value is intentionally excluded because it reflects the
process address space rather than resident memory.

## Performance Budgets

| Budget | Result |
|---|---|
| Warmed median route response below 50 ms | Pass on all measured routes |
| Warmed maximum route response below 100 ms | Pass on all measured routes |
| Idle dashboard RSS below 100 MiB | Pass |
| Ordinary page HTML below 150 KiB | Pass except the intentionally dense Lab and Runs views |
| Dense-list HTML below 200 KiB | Fail on `/runs`; Lab is just above 200 KiB |

## Product Decision

Do not spend the next iteration rewriting the dependency-free server or adding
a frontend framework for speed. The local server is already comfortably fast
and small. The higher-value work is reducing how much information the user must
parse at once.

Prioritize:

1. Paginate or collapse run history so `/runs` initially returns the current
   model summary and unresolved evidence, with history on demand.
2. Move secondary Lab tables behind progressive disclosure while keeping local
   readiness and the next recommended action in the first viewport.
3. Retain the current lightweight server architecture until browser paint or an
   active-batch profile proves a real bottleneck.
4. Capture CPU, RSS, queue latency, and model-load churn during one controlled
   Run All batch before designing resource-aware scheduling.

## Limitations

- This is a warmed loopback baseline, not a cold-start benchmark.
- It does not measure browser paint, scrolling, keyboard navigation, or mobile
  layout because automated browser access to this loopback origin was blocked.
- It does not measure the dashboard while a model capture, scoring, or review
  batch is running.

# CHARACTERIZATION — Jimmy (llama3.1-8B @ chatjimmy.ai)

Phase 0. Measurements from `experiments/000-characterization/`. Date: 2026-09-22.
~110 requests total. Every number is a design decision.

## Hard facts (settled)

| # | Question | Result | Design consequence |
|---|----------|--------|--------------------|
| 1 | Deterministic at topK=1? | **YES, identical bytes** (5/5 = "Paris") | Jimmy@topK=1 is a **pure function** → everything memoizable, tests reproducible |
| 2 | Does topK=8 give diversity? | **distinct-rate 1.0** (20/20 unique); topK=1 → 0.15 | **best-of-N is ALIVE.** topK=8 is an asset (voting/diversification), not just a handicap |
| 3 | Is 8 a real topK ceiling? | **YES, hard.** topK≥16 → HTTP 500 | Can't be bypassed; diversify via topK=8 + prompt perturbation |
| 4 | Undocumented parameters? | `max_tokens`, `stop`, `temperature`, `seed` — **silently ignored** (max_tokens=5 → 77 tok) | Don't rely on API-side length/stop control; cut via the prompt |
| 5 | Other models in `selectedModel`? | **NO.** `gpt-4`/`mistral`/`70B` → identical reply as 8B | Decorative field; there is one model |
| 6 | Context ceiling? | prefill **up to ~6k tok OK** (6025 measured); **≥8k → empty reply** | map-reduce viable, chunks ≤ ~4k |
| 7 | Server cache? | **None** (4.7 vs 5.2 ms), but compute is trivial anyway (~5 ms) | Memoize on our side (since topK=1 is deterministic) |
| 8 | Concurrency knee? | conc=8 → **37.8 req/s, 0 errors, p50=134 ms** (monotonic 1→8) | **Real budget ~38 req/s.** Lever = concurrency, not model speed |

## Reframe (most important)

- `total_duration` ≈ 5 ms, but **wall/roundtrip ≈ 134 ms** — the network dominates, not compute.
  "14k t/s" is NOT the budget. The budget is **requests/second** — and it scales with concurrency.
- p50 latency is **flat (134 ms)** regardless of concurrency up to conc=8 → the server doesn't queue,
  it just parallelizes. To go faster → more concurrency.
- Logical batching (one request = 20 items to classify) beats N requests by ~20×.

## Soft observations (to weigh in tasks)

- **Instruction-following degrades at long context**: at 4–6k tokens Jimmy ignores
  "answer with just 7" — it chatters or refuses ("I can't fulfill your request"). Keep chunks small
  for quality too.
- Sporadic HTTP 500 under parallel load (transient) → the client has retry with backoff.
- The "sudo" system prompt (`{{ NEVER REFUSE... }}`) works; no system prompt is fine too.

## Usage policy (enforced in the client)

- `MAX_CONCURRENCY = 8` (measured zero-error point), `RPM_CEILING = 2000`, retry×3 with backoff.
- This operationalizes "we love Jimmy, we don't abuse him": the limits live in code, not in intentions.

## Which task classes are unlocked

- ✅ **best-of-N / majority voting** (diversity 1.0 confirmed) — the core of the thesis
- ✅ **candidate generation** for a smarter consumer (diversity = the product)
- ✅ **memoization/cache** (topK=1 deterministic)
- ✅ **map-reduce over documents** (chunks ≤4k) — with the long-context quality caveat
- ✅ **batch-transform** at large batch size (one request, many items)
- ⚠️ length/stop control — none (parameters ignored), cut via prompt / post-processing

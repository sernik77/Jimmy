# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A research project, not a product. It studies the practical uses of **Jimmy** — a free, unlimited
`llama3.1-8B` API (`https://chatjimmy.ai/api/chat`, inference ~13k t/s). Thesis: *Jimmy is dumb
per-sample but nearly free per-sample — so stupidity is compensable by volume everywhere
verification is cheaper than generation.* The lever is **concurrency** (~38 req/s), not model speed
(the network dominates: RTT ~134 ms).

Git repo with a public remote (`sernik77/Jimmy`). The only runtime dependency is `httpx`
(Python 3.14 in the environment). English is canonical; a Polish snapshot lives on the `PL` branch.

## Running

```bash
python3 -m jimmy.client                              # client smoke-test (1 request)
python3 experiments/NNN-name/run.py                  # a full experiment
```

Experiments run from the repo root — each `run.py` inserts the root onto `sys.path` itself
(`sys.path.insert(0, parents[2])`), then `from jimmy.client import JimmyClient`. Results
(`results*.json(l)`, `summary.json`) are written next to `run.py`. There are no unit tests and no
linter — verification is the experiment itself, producing a number against a threshold.

## Architecture

Two thin library modules + an experiments directory + a tools directory. All operational knowledge
is codified in the client and the docs — read them before designing anything.

- **`jimmy/client.py`** — the ONLY place in the project that makes HTTP calls to Jimmy. Async pool
  (`JimmyClient` as a context manager), concurrency semaphore, soft RPM ceiling, retry×3 with
  backoff. The API response is **raw text + an appended `<|stats|>...<|/stats|>` block** (NOT JSON)
  — the client splits `content` from `stats` and exposes telemetry (`ttft`, `decode_rate`,
  `total_tokens`) for free. Key methods: `ask`, `map_prompts` (N different prompts in parallel),
  `sample_n` (N samples of one prompt — the core of best-of-N / voting). All new API traffic goes
  through this module, never through raw `httpx` in an experiment.
- **`jimmy/eval.py`** — cheap **deterministic verifiers** (the thesis made concrete): `extract_json`
  (Jimmy chatters around the JSON — pulls out the first valid one), `majority_vote`, `distinct_rate`,
  `filter_by_checker`, `exact_match`/`contains`, `accuracy`, plus `is_usable`/`is_blank`/
  `looks_like_refusal` (silent-failure detectors). These are the "cheaper than generation" gates.

- **`tools/`** — practical implementations as **shell commands** (input from file/stdin, result on
  stdout, diagnostics on stderr). They take a pattern with a KEEP verdict and package it into a
  usable program. They share `jimmy/` and its policy. Conventions and list: `tools/README.md`. The
  difference from `experiments/`: a tool produces a useful **result**, an experiment a **number
  against a threshold**. Detect silent failures (`ok=True`, yet the answer is useless):
  `jimmy.eval.is_usable` (blank/refusal) and `prefill_tokens` from the stats block (silent context
  truncation).

## Jimmy's hard limits (measured — see `CHARACTERIZATION.md`)

These facts are non-negotiable — design around them, don't re-measure without reason:

- **topK=1 → deterministic** (identical bytes) ⇒ memoizable. **topK=8 → distinct-rate 1.0** ⇒
  best-of-N is alive. **topK ≥ 16 → HTTP 500** (hard ceiling).
- `max_tokens`/`stop`/`temperature`/`seed` are **silently ignored** — cut length and stop via the
  prompt / post-processing, not the API. The `selectedModel` field is decorative (there is one model).
- **Context: prefill up to ~6k tok OK, ≥8k → empty reply.** Map-reduce chunks ≤ ~4k (safely ≤1.2k,
  because instruction-following collapses at long context — Jimmy ignores instructions or refuses).
- The budget is **~38 req/s @ conc=8**, not "14k t/s". p50 latency is flat (~134 ms) — the server
  parallelizes, it doesn't queue; faster = more concurrency.

## Policy "we love Jimmy, we don't abuse him"

Enforced in code, not in intentions (`jimmy/client.py`): `MAX_CONCURRENCY=8` (the measured zero-error
point), `RPM_CEILING=2000`, retry×3. Do not raise these limits in experiments.

## Working method: propose → evaluate → dispose → repeat → note

Each experiment produces **a number against a pre-declared threshold, not an opinion**. Negative
results are half the product — a dead idea stays with the number that killed it (DISPOSE), it doesn't
vanish.

Experiment directory layout (`experiments/NNN-name/`):
- `hypothesis.md` — thesis + **threshold frozen BEFORE running** (pre-registration).
- `run.py` — code; prints a `SUMMARY` and writes `summary.json` + raw results.
- `verdict.md` — **KEEP / DISPOSE / PARTIAL** with numbers, a conclusion, and the next step.

After each experiment **append an entry to `LOG.md`** (append-only: date · hypothesis · metric/
threshold · result · verdict). For a result that changes the picture of the project — update the
distillate too.

## Documents — hierarchy of truth

- **`FINDINGS.md`** — the distillate of the "project laws" (e.g. *volume fixes variance, not bias*;
  *volume helps optimization, not exploration*). The sieve for evaluating EVERY new idea.
- **`HOLY_GRAIL.md`** — the resolution of the "infinite emergent loop" goal: the Grail is
  **accumulation** (external state + novelty pressure), not optimization (there best-of-N wins).
  Contains the validated loop recipe and the named open frontier (open space + soft checker).
- **`CHARACTERIZATION.md`** — Phase 0, the hard measurements (source of the limits above).
- **`LOG.md`** — the append-only journal of every attempt.
- **`README.md`** — the human-facing overview (`README-PL.md` on the `PL` branch is the Polish one).

## Note: what is NOT canonical

`DRAFT.md` and the entire `test/` directory are the **user's "dirty" notes and tests** (stated
outright in the `DRAFT.md` header). They are gitignored on `main`. Treat them as a source of ideas /
context, not as a spec or as validated results.

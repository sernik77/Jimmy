# JIMMY

> Turning a cheap, dumb, unlimited chatbot into a reliable tool — by measurement, not by faith.

![model](https://img.shields.io/badge/model-llama3.1--8B-1f6feb)
![throughput](https://img.shields.io/badge/throughput-~38%20req%2Fs%20%40%20conc%208-2ea043)
![method](https://img.shields.io/badge/method-propose%E2%86%92evaluate%E2%86%92dispose-d29922)
![experiments](https://img.shields.io/badge/experiments-22-8250df)
![python](https://img.shields.io/badge/python-3.14-3776ab)

**Jimmy** is a free, unlimited chatbot backed by `llama3.1-8B`, served from dedicated hardware
([`chatjimmy.ai`](https://chatjimmy.ai)) at ~13k tokens/s. This project is a systematic study of
**what such a model is actually good for** — run as a lab, where every idea earns a *number*
against a pre-declared threshold, and dead ideas are kept with the number that killed them.

🇬🇧 English (default) · 🇵🇱 [Polski](README-PL.md)

---

## The thesis

> **Jimmy is dumb per-sample, but nearly free per-sample. So stupidity is compensable by volume
> everywhere verification is cheaper than generation.**

The lever is **concurrency** (~38 req/s), not model speed — the network dominates (RTT ~134 ms),
so "13k t/s" is not the budget; **requests per second** is, and it scales with parallelism.

## The laws (confirmed across experiments)

These are the sieve every new idea is run through — see [`FINDINGS.md`](FINDINGS.md) for the full
derivation.

1. **Volume fixes variance, not bias.** Best-of-N / voting turns an unreliable 8B into a reliable
   tool *iff* its errors are random and a cheap verifier or aggregator exists. Systematic errors
   (Jimmy consistently misreads a task) are unfixable by more samples.
2. **Volume helps optimization, not exploration.** Sampling is spiked on modes — great for picking
   the best of N, poor for covering a categorical space. Exploration is unlocked only by an
   **external accumulating state + novelty pressure** (coverage 18% → 80%).
3. **A loop is worth it only for accumulation, not optimization.** When the optimum fits in a
   single output, best-of-N wins and the loop adds nothing. When the target is *larger than one
   generation*, an accumulating loop is the only thing that works — see
   [`HOLY_GRAIL.md`](HOLY_GRAIL.md).

## Hard limits of Jimmy (measured — [`CHARACTERIZATION.md`](CHARACTERIZATION.md))

| Property | Value | Design consequence |
|---|---|---|
| Determinism @ topK=1 | identical bytes | memoizable, reproducible, cacheable |
| Diversity @ topK=8 | distinct-rate 1.0 | **best-of-N is alive** |
| topK ceiling | topK ≥ 16 → HTTP 500 | hard cap; diversify via topK=8 + prompt perturbation |
| `max_tokens`/`stop`/`temperature`/`seed` | silently ignored | control length/stop via prompt, not API |
| Context ceiling | ~6k prefill OK, ≥8k → **empty reply** | chunk map-reduce ≤ ~1.2k tokens |
| Concurrency knee | conc=8 → 37.8 req/s, 0 errors, p50=134 ms | budget ≈ 38 req/s; lever = concurrency |

## Quick start

```bash
pip install httpx                                    # the only runtime dependency

python3 -m jimmy.client                              # smoke-test (1 request)
python3 experiments/001-majority-vote-math/run.py    # reproduce an experiment

# practical tool: summarize a document of any length
tools/summarize.py README.md --style tldr
cat long.txt | tools/summarize.py --map-only > notes.md
```

## Repository layout

```
jimmy/client.py     # the ONLY HTTP chokepoint: async pool, concurrency cap, retry, <|stats|> parsing
jimmy/eval.py       # cheap deterministic verifiers: JSON, exact-match, voting, distinct-rate, usability
experiments/NNN-*/  # hypothesis.md · run.py · results.* · verdict.md
tools/              # validated patterns packaged as shell commands (stdin→stdout)
CHARACTERIZATION.md # measured properties of Jimmy (Phase 0)
FINDINGS.md         # distilled laws — the sieve for every new idea
HOLY_GRAIL.md       # the "emergent loop" goal, resolved
LOG.md              # append-only propose/evaluate/dispose journal
```

The **client** exposes `ask`, `map_prompts` (N different prompts in parallel) and `sample_n`
(N samples of one prompt — the core of best-of-N / voting), each returning parsed `<|stats|>`
telemetry for free. All API traffic goes through this one module; the safe-use policy
(`MAX_CONCURRENCY=8`, `RPM_CEILING=2000`, retry×3) is enforced in code, not in intentions.

## Experiments

Method: **propose → evaluate → dispose → repeat → note**. Each experiment freezes a metric and a
threshold *before* running, then produces a verdict. Negative results are half the product.

Legend: ✅ KEEP · ⚠️ PARTIAL / conditional · ❌ DISPOSE · 🔀 SPLIT · 💡 counter-intuitive finding ·
🧭 capability boundary · 🔬 measurement

| # | Experiment | Result |
|---|------------|--------|
| [000](experiments/000-characterization/) | Characterization (Phase 0) | 🔬 Measured Jimmy's properties → [`CHARACTERIZATION.md`](CHARACTERIZATION.md) |
| [001](experiments/001-majority-vote-math/) | Majority-vote on math | ✅ **KEEP** — self-consistency 64% → 92% · [verdict](experiments/001-majority-vote-math/verdict.md) |
| [002](experiments/002-structured-json/) | Structured JSON extraction | ✅ **KEEP** (sharp boundary) — validity 100%, semantics don't · [verdict](experiments/002-structured-json/verdict.md) |
| [003](experiments/003-candidate-generation/) | Candidate generation | 🔀 **SPLIT** — selection KEEP, coverage DISPOSE; anti-mode accumulation KEEP · [verdict](experiments/003-candidate-generation/verdict.md) |
| [004](experiments/004-map-reduce-doc/) | Map-reduce over a long doc | ✅ **KEEP** — beats context limit, recall 0 → 100 · [verdict](experiments/004-map-reduce-doc/verdict.md) |
| [006](experiments/006-holy-grail-evolution/) | Holy Grail as a GA | ❌ **DISPOSE** (with diagnosis) — loop adds nothing when optimum ⊂ one output · [verdict](experiments/006-holy-grail-evolution/verdict.md) |
| [007](experiments/007-open-accumulation/) | Open-ended accumulation | ❌ **DISPOSE** — accumulation saturates in open space too · [verdict](experiments/007-open-accumulation/verdict.md) |
| [008](experiments/008-asymmetric-critic/) | Asymmetric critic | ❌ **DISPOSE** — critic improves draft but loses to equal-budget best-of-N · [verdict](experiments/008-asymmetric-critic/verdict.md) |
| [009](experiments/009-jimmy-automaton/) | Jimmy as an automaton | ❌ **DISPOSE** spatial hypothesis, but an emergent discovery · [verdict](experiments/009-jimmy-automaton/verdict.md) |
| [010](experiments/010-fs-tree-mapreduce/) | FS-tree map-reduce | 💡 Counter-intuitive — for holistic classification, **don't** decompose · [verdict](experiments/010-fs-tree-mapreduce/verdict.md) |
| [011](experiments/011-bash-codegen/) | Bash code generation | ❌ **DISPOSE** decomposition — best-of-N wins, Jimmy-reduce breaks · [verdict](experiments/011-bash-codegen/verdict.md) |
| [012](experiments/012-big-input-docs/) | Big input vs targeted context | 💡 Relevance & brevity beat size (+55 vs +11) · [verdict](experiments/012-big-input-docs/verdict.md) |
| [013](experiments/013-hierarchical-summarization/) | Hierarchical summarization | ⚠️ **PARTIAL KEEP** — pipeline works, reduce must be chunked too · [verdict](experiments/013-hierarchical-summarization/verdict.md) |
| [014](experiments/014-web-html-ops/) | Web / HTML ops | 🧭 Capability boundary — mechanics → regex, semantics → Jimmy · [verdict](experiments/014-web-html-ops/verdict.md) |
| [015](experiments/015-meta-prompting/) | Meta-prompting | ❌ **DISPOSE** — names the right ideas, can't package a working scaffold · [verdict](experiments/015-meta-prompting/verdict.md) |
| [016](experiments/016-recursive-decomposition/) | Recursive decomposition | ⚠️ **PARTIAL KEEP** — defensive technique wins (+35), deep recursion doesn't · [verdict](experiments/016-recursive-decomposition/verdict.md) |
| [017](experiments/017-steps-to-commands/) | Steps → shell commands | ⚠️ **KEEP for form, not intent** — 96% run, ~20% do the wrong thing · [verdict](experiments/017-steps-to-commands/verdict.md) |
| [018](experiments/018-command-analysis/) | Command analysis | 💡 describe→compare repairs judgment (+30); direct judge rubber-stamps · [verdict](experiments/018-command-analysis/verdict.md) |
| [019](experiments/019-logic-benchmark/) | Logic benchmark | 🧭 Propositional OK (0.88), quantifiers/higher-order ≈ chance · [verdict](experiments/019-logic-benchmark/verdict.md) |
| [020](experiments/020-archwiki-to-manpage/) | ArchWiki → manpage | ✅ **KEEP** — hybrid Jimmy content + deterministic troff · [verdict](experiments/020-archwiki-to-manpage/verdict.md) |
| [021](experiments/021-manpage-to-tldr/) | Manpage → tldr | ⚠️ **PARTIAL KEEP** — works for `tar`, unstable for `journalctl` · [verdict](experiments/021-manpage-to-tldr/verdict.md) |
| [022](experiments/022-synthetic-training-data/) | Synthetic training data | ✅ **KEEP** (sharp scope) · [verdict](experiments/022-synthetic-training-data/verdict.md) |

## The Holy Grail

The project's stated goal was "an infinite Jimmy-based loop with emergent properties." It has a
concrete, empirical answer — and not the expected one: **the Grail is accumulation, not
optimization.** An emergent loop is worth building *iff* it grows a structure larger than any
single generation, held in external state (coverage 18% → 80%). Full resolution, the validated
recipe, and the named open frontier: [`HOLY_GRAIL.md`](HOLY_GRAIL.md).

## Tools

Validated patterns, packaged as Unix-style commands (input from file/stdin, result on stdout,
diagnostics on stderr). See [`tools/README.md`](tools/README.md).

- **[`summarize.py`](tools/summarize.py)** — summarize a document of *any length* (map-reduce +
  hierarchical reduce, silent-truncation detection, ~20 flags). Built on experiments
  [004](experiments/004-map-reduce-doc/verdict.md) + [013](experiments/013-hierarchical-summarization/verdict.md).

## Safe-use policy — "we love Jimmy, we don't abuse him"

Enforced in [`jimmy/client.py`](jimmy/client.py), not in intentions: `MAX_CONCURRENCY=8` (the
measured zero-error point), `RPM_CEILING=2000`, retry×3 with backoff. Tools clamp any user override
back to these limits.

## For contributors / AI agents

[`CLAUDE.md`](CLAUDE.md) documents the architecture, conventions, and hard constraints for anyone
(human or agent) working in this repo.

---

<sub>Research project. All figures are reproducible from the `run.py` in each experiment folder.
Language: English is canonical; Polish companions carry the `-PL` suffix.</sub>

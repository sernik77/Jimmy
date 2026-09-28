# FINDINGS — practical uses of Jimmy

As of 2026-09-22. Distilled from `CHARACTERIZATION.md` + experiments `001`, `002`.

## The project law (confirmed 2× independently)

> **Volume fixes variance, not bias.**

best-of-N / voting turns an unreliable 8B into a reliable tool **if and only if** Jimmy's errors are
random (scattered around the truth) and a cheap verifier/aggregator exists. When the error is
**systematic** (Jimmy consistently misreads), more samples only entrench the wrong answer.

This is the sieve for evaluating EVERY future Jimmy idea:
1. Is there a cheap deterministic verifier or a sensible aggregation? If not → reject.
2. Are the 8B errors here random or systematic? Systematic → best-of-N won't help.

### Second law (003): volume helps OPTIMIZATION, not EXPLORATION
Jimmy's sampling is **spiked on modes**. More samples:
- ✅ for **optimization** (pick the best by a scalar / voting) — 001, 002, 003B,
- ❌ for **exploration** (covering a categorical space) — 003A: saturation at ~18%.

**But (003b):** exploration is unlocked by an *external accumulating state + novelty pressure* — a
"already seen" memory injected into the prompt raises coverage from ~18% to **~80%** (3-4× at equal
budget). This is the validated anti-collapse mechanism for a loop (006).

### Third law (006): a loop is worth it only for ACCUMULATION, not OPTIMIZATION
When the optimum fits in a SINGLE Jimmy output → **best-of-N wins**, the evolutionary loop adds
nothing (006/006b: evolution = control). When the target EXCEEDS one output (a structure larger than a
generation) → a loop with accumulating state is the only thing that works (003b). The Holy Grail =
accumulation. Full resolution and open frontier: **`HOLY_GRAIL.md`**.

### Fourth law (004/010/011): when to DECOMPOSE work into steps
The intuition "break into as many simplest steps as possible, process independently, then reassemble"
is **usually wrong** for Jimmy. It wins only in a narrow case:

| Task type | winner | evidence |
|-----------|--------|----------|
| Extraction from **disjoint** fragments, **deterministic** reduce (union/sum) | **map-reduce** | 004: 0→100% |
| **Classification/gestalt** (topic, meaning of the whole) | **show Jimmy the WHOLE** (no map stage) | 010: 54% per-item → 100% holistic |
| **Synthesis of coupled parts** (code, text) | **best-of-N of the whole + verifier** | 011: decomposition 17% < best-of-N 47% |

Rule: decompose ONLY when the units are genuinely independent AND recombination is arithmetic. When
the task benefits from the whole context → don't split. When it needs intelligent gluing → best-of-N
of the whole + a deterministic checker (NOT reduce-by-Jimmy).
Bonus (010): a dumb model is BETTER on the aggregate than on the part — classify groups, not single
entities.

**Extension (013): when reduce MUST be by Jimmy (summarization), the reduce itself must be chunked.**
A holistic reduce over many sections breaks the quantitative constraints (instruction-following
collapses on large input). **Hierarchical reduce** (batches → mini-summaries → final, each level =
SMALL input) holds format (adherence 1.0) and compression (42×). Single-shot on a large document
SILENTLY truncates (prefill 110 of 15k) — map-reduce is required. Hard constraints in the system
prompt govern format (0.92-1.0 vs 0.0 for a loose one).

### Fifth law (012): context — RELEVANCE beats SIZE
"Big input → small output" (dump the whole documentation) is the **inverse** of what works:
- dumping all of `man bash` (~98k tok, 16× the limit) or even 10k tok → **0%** (over the limit
  destroys the output),
- a generic dump within budget (4k tok) → barely +11 pts (dilutes the signal),
- **a small TARGETED cheatsheet (~160 tok) → +55 pts (39%→94%)**.

Jimmy's errors are often **knowledge gaps**, not a lack of reasoning — injecting EXACTLY the right
small fragment buries them. Rule: **minimal relevant input**, not big input. Invest in retrieving the
right snippet (high S/N, well under ~6k), not in context size.

### Sixth law (014): mechanics → deterministic code, semantics → Jimmy
For HTML/data tasks that are **mechanically specifiable** (link extraction, tag stripping,
keyword-grep, structure parsing) → use a **regex/parser/grep**: perfect, instant, free. Jimmy is
strictly WORSE here (014: links F=0.64, strip F1=0.68, keyword F=0.69 vs 1.0). Jimmy adds value ONLY
for **semantics with no deterministic equivalent** (topic filter F=0.94, content description,
tagging). **Pipeline pattern:** the parser does the mechanics, Jimmy gets only the semantic subtasks
on already-cleaned text. Don't make Jimmy do what a regex does better.

### Ninth law (019): logical ability is layered + judge by balanced accuracy
Jimmy: propositional logic (L0) solid (bal_acc 0.88), but from quantifiers/higher orders (L1-L5) it
collapses to near-chance (0.62-0.75) with a persistent TRUE bias. Voting doesn't rescue it (bias, not
variance). **Methodology:** for EVERY binary task report balanced accuracy + class-balance +
answer-rate — otherwise gold imbalance + model bias masquerade as competence (first 019 run: L4 gold
6T/0F → constant TRUE "=1.00"). Practice: trust Jimmy on simple boolean logic (with verification), not
on quantifier reasoning.

### Eighth law (018): mediate judgment through a faithful DESCRIPTION — don't ask "does it match?" directly
A direct Jimmy-judge "does the command match the task?" RUBBER-STAMPS (018 T2: mismatch-recall 0.08,
calls everything a MATCH — positive bias, voting doesn't help). BUT the same judgment passed through a
faithful DESCRIPTION (018 T3: "describe what the command does" → "compare the task with the
description") detects 100% of mismatches (acc 0.54→0.83, +30 pts). Because describing is knowledge
recall, which Jimmy does FAITHFULLY (T1 faithful 1.0), and comparing two descriptions sidesteps the
judge's bias. Technique: **describe→compare instead of direct-judge**. It nuances Law 7: Jimmy is a
bad DIRECT judge but a good DESCRIPTION comparator.

### Seventh law (015): Jimmy = PROPOSER, never EVALUATOR/DISPOSER/architect
Jimmy cannot design a working problem-solving loop (meta-prompting). Generated scaffolds: structural
rate 60%, functionally fitness 0 vs a deterministic ceiling of 8.88. Root cause: (a) the proposer
breaks its own constraints (a 14-word example at a 12-word limit), (b) the evaluator is written like a
baked-in ANSWER, not a general INSTRUCTION, and grades "vibes" not a real criterion. Even a HUMAN
scaffold (2.38) ≪ deterministic selection (8.88) — **the bottleneck is the evaluator; a soft
evaluator (Jimmy or human) doesn't track truth**. Rule: in a propose/evaluate/dispose loop Jimmy plays
ONLY the PROPOSER role (diversity generator); the EVALUATOR and DISPOSER must be deterministic. Again
the canonical recipe: best-of-N (Jimmy proposes) + deterministic verifier (Jimmy doesn't judge).

### Tenth law (022): Jimmy generates useful training data; two deficits bind — coverage AND label fidelity
Downstream (AG News 4-class, the same classifier on data from different sources, macro-F1 on the real
gold test, N=400 matched). **KEEP as a training-data generator** for these students:
- **Student NB (bag-of-words), floor=majority:** Jimmy-IID closes the floor→REAL gap by **0.74**.
- **Student ICL, floor=ZERO-SHOT** (an honest floor — Jimmy already knows how to classify news,
  zero-shot F1 0.517; majority would inflate G): Jimmy exemplars genuinely help (all >zero-shot by
  >3 SE, G IID 0.70 / NOVELTY 0.93), BUT the three sources (REAL/IID/NOVELTY) are **mutually
  indistinguishable** (SE≈0.033/160 items; IID vs NOVELTY = 1.4 SE). The help is largest on the
  hardest class Sci/Tech (zero-shot recall 0.0).

Four nuances:
- **Two real deficits of the Jimmy pool vs REAL at equal N:** (a) **lexical coverage** — vocab REAL
  4583 vs IID 2142 vs NOVELTY 1998 (<½ the vocabulary; NB ignores OOV → this directly feeds the gap);
  (b) **label fidelity** — self-check forced-4way 0.83/0.74, style-gap agreement 0.94/0.83. Both bind.
- **`distinct_rate` is a bad instrument for collapse** on generated prose (≈1.0 by construction; the
  0.90 threshold could never fire). Document-level collapse didn't occur, but VOCABULARY-level did.
- **Novelty pressure (003b) HURTS here and loses on ITS OWN goal:** on NB 0.617→0.429; NOVELTY worse
  on BOTH axes — it didn't even buy coverage (vocab 1998 < IID 2142) and lost fidelity. 003b works for
  an ENUMERABLE space with a HARD checker; a semantic class is not one. Confounded mechanism: novelty
  implemented via memory injection → label drift + long-context degradation (truncated samples).
- **The value of the intervention depends on the student:** bag-of-words is sensitive to label noise
  and coverage; ICL (k=8) tolerates it. Same set, different verdict. A cheap quality proxy:
  model-REAL→Jimmy-pool (style-gap agreement) predicted the ranking without a Jimmy judge.
Recipe: IID + dedup (n-gram Jaccard) + optional forced-4-way filter; separately increase lexical
coverage. **OPEN:** SFT data for a fine-tuned LM (untested; torch available).

## Applications portfolio

### ✅ Confirmed (KEEP) — reliably working
| Application | Evidence | Pattern |
|-------------|----------|---------|
| **Self-consistency on verifiable tasks** (arithmetic, numbers, facts with aggregation) | 001: 64%→92% @ vote-21..31 | `sample_n(15-21) → majority_vote` |
| **Bulletproof schema-conformant JSON emission** (text→structure) | 002: 100% validity @ best-of-8, **repeated 2×** | `sample_n(8) → filter(validate) → first valid` |
| **Classification on disjoint, well-defined categories** | 002: 91.7% / 100% (2 runs), unambiguous subset | `sample_n(8) → majority_vote(intent)` |
| **Candidate generation + scalar selector** (optimization) | 003B: −26.9% of the objective, best-of-20 | `sample_n(N) → scorer → argmin/argmax` |
| **Space exploration with external memory** (anti-mode, enumerable space) | 003b: 18%→~80% coverage, 3-4× | loop: `seen` + prompt "not: [seen]" |
| **Long-document processing via map-reduce** (APPLICATION) | 004: recall 0.00→**1.00** on a doc 2.6× the limit | `chunk(≤1.2k) → map extraction → reduce union` |
| **Jimmy as a CA rule → emergent global order** | 009b: antiferromagnetic checkerboard, strictly topological | grid + voter/consensus rule, synchronous update |
| **Writing code (bash): targeted cheatsheet + best-of-N + execution** | 011: best-of-N 47%; 012: **+cheatsheet → 94%** | `RAG(small snippet) + sample_n(k) → run → pass` |
| **Filling knowledge gaps with a targeted mini-context** (RAG) | 012: +55 pts from ~160 relevant tok | inject the EXACT fragment, well under 6k |
| **Holistic classification of groups** (folder/set, not a single entity) | 010: 54% per-file → **100%** per-folder | show Jimmy the whole group at once |
| **Hierarchical summarization of a huge document** | 013: adherence 1.0, compression 42×, faith 0.9 | `chunk → map(hard prompt) → HIERARCHICAL reduce` |
| **Document → format transformation** (ArchWiki→manpage) | 020: renders 0-warnings, faith 0.86, man-compatible | Jimmy=content, Python=troff; strip→chunk→map→reduce |
| **manpage → tldr** (rich manpages + a precise prompt) | 021: tar renders in real tldr, faith 1.0 | Jimmy=content (prompt: "most common real uses"), Python=format; UNSTABLE per-command |
| **Semantic operations on HTML/text** (topic filter, description, tagging) | 014: topic-filter F=0.94 | parser→mechanics, Jimmy→semantics only |
| **Defensive step planning** ("assume nothing, verify preconds/success") | 016: defensive-ratio 0.90 vs 0.54 plain (+35 pts) | defensive system prompt + shallow bounded decomposition |
| **Generating shell commands per step** (form) | 017: best-of-N valid 1.0, real 1.0, runnable 0.96 | `sample_n → filter: bash -n ∧ real ∧ exec(read-only)` |
| **Propositional logic L0** (tautologies, evaluation, entailment) | 019: balanced acc 0.88, no bias | best-of-N + voting |
| **Describing/explaining commands** (knowledge recall) | 018 T1: faithful 1.0, recall 0.68 | one sentence, best-of-N |
| **Match verification via description** (describe→compare) | 018 T3: acc 0.83, mismatch-recall 1.0 | describe the command → compare with the task |
| **Generating alternative commands** (diversity) | 018 T4: diverse 1.0, valid 1.0, equiv 0.58 | best-of-N + check output equivalence |
| **Generating training data** (topic classification) | 022: IID closes gap G=0.74 (NB, floor=majority) / 0.70 (ICL, floor=zero-shot) on gold AG News | IID per-class + dedup + forced-4-way filter; NOT novelty pressure |
| **Deterministic, cacheable function** (topK=1) | Phase 0: identical bytes | local memoization |
| **Massive parallel transformation** (~38 req/s, conc=8; sustained 57 rps/0 errors) | Phase 0 + sustained.py | async pool from the client |

### ❌ Rejected / limited (DISPOSE)
| Idea | Reason | Number |
|------|--------|--------|
| Jimmy as **arbiter** on an overlapping/contested taxonomy | there even the human gold is contested; voting entrenches one of the reasonable choices | 002: 37.5% on the debatable subset (stable 2×) |
| **Naive** space coverage by volume alone (no memory) | mode-collapse: samples spike on a few favorites | 003A: saturation ~18% (fixed in 003b with memory → ~80%) |
| Length/stop control via the API (`max_tokens`, `stop`) | parameters ignored | Phase 0 |
| Selecting a stronger model (`70B`, etc.) | `selectedModel` ignored, there is one 8B | Phase 0 |
| Long context (>6-8k tok) / big map without chunking | empty reply + instruction-following drop | Phase 0 |
| **Open-ended accumulation / open invention** with a soft checker | saturates (phonotactic modes + window echo + gate hole) | 007: accept-rate 0.22→0.06 |
| **Critic loop** (generator↔critic) as optimization | the critic shares the bias, sometimes breaks things; best-of-N at equal budget wins | 008: 4.01 vs 4.58 |
| **Decomposition into steps + reduce-by-Jimmy** (codegen) | the reducer can't glue coupled/inconsistent snippets; planning not to blame (C1=C2) | 011: 17% vs best-of-N 47% |
| **Decomposing classification into per-item map + reduce** | the map stage throws away context and injects noise | 010: 54% vs 100% holistic |
| **"Big input": dump all the documentation into the prompt** | over the limit → 0%; a generic in-budget dump dilutes (barely +11) | 012: over-limit 0%, man4k +11 vs cheatsheet +55 |
| **Mechanical HTML extraction** (links, strip, keyword) via Jimmy | regex/parser/grep perfect+free; Jimmy worse | 014: F 0.64-0.69 vs 1.0 |
| **Jimmy as a scaffold architect / soft-evaluator** (meta-prompting) | confuses instruction with example, grades vibes; fitness 0 vs det 8.88 | 015: structural 60%, exec 0 |
| **Deep recursion to an "atomic layer"** | Jimmy doesn't judge atomicity (never says ATOMIC), explosion + cross-branch redundancy | 016: 299 leaves, cap, ~20% dup |
| **Unattended execution of Jimmy's commands** | ~20% works-but-wrong; emits destruction (`init 6` reboot) | 017: semantics 0.79, exec 0.96 |
| **Jimmy as a direct judge "does X match Y?"** | rubber-stamp / positive bias; calls everything a MATCH | 018 T2: mismatch-recall 0.08 (use describe→compare) |
| **Quantifier / higher-order reasoning** (L1+) | near-chance, TRUE bias; voting doesn't rescue | 019: bal_acc 0.62-0.75 (vs L0 0.88) |
| **Jimmy-CA → spatial domains** (ferromagnetic clusters) | an averaging rule diffuses; voter gives anti-order not domains | 009: Δsim≈−0.1 |
| **Novelty pressure (003b, memory injection) for training-data generation** | no hard class checker → label drift + long-context degradation; loses on ITS OWN goal (vocab 1998 < IID 2142 — didn't buy coverage) | 022: NB 0.617→0.429 (G 0.74→0.47) |

> **Correction to 002:** the global "70% intent-acc" was misleading — the denominator included my own
> contested labels. After splitting: unambiguous ≈92-100%, contested 37.5%. The right conclusion isn't
> "bias" but "Jimmy handles clean categories; the boundary is taxonomy underspecification".

## Roadmap (next hypotheses to test)
- ✅ **003 — candidate generation** (DONE): B (selection) KEEP, A (coverage) DISPOSE,
  003b (anti-mode with memory) KEEP — the anti-collapse mechanism is validated.
- ✅ **006 + 006b — the Holy Grail as a GA** (DONE): **DISPOSE** of emergence-as-optimization.
  best-of-N at equal budget can't be beaten by evolution (A=D). Resolution: **Grail = accumulation,
  not optimization** — see `HOLY_GRAIL.md`. Open frontier: open space + soft checker.
- ✅ **004 — map-reduce over a document** (DONE): **KEEP**, recall 0.00→1.00 on a doc 2.6× the limit.
- ✅ **007 — open accumulation, soft checker** (DONE): **DISPOSE** — saturates (accept 0.22→0.06);
  answers the Grail frontier: accumulation = enumerable recall, not open invention.
- ✅ **008 — asymmetric agents (generator↔critic)** (DONE): **DISPOSE** — best-of-N wins (4.58 vs 4.01).
- ✅ **009 + 009b — Jimmy as a CA rule** (DONE): **EMERGENCE** (009b: antiferromagnetic checkerboard,
  topology-dependent); 009 (blend) → self-referential semantic collapse.
- ✅ **011 — bash codegen (decomposition vs monolith)** (DONE): **DISPOSE** of decomposition;
  best-of-N + execution wins (47% vs 17%). Planning not to blame (C1=C2).
- ✅ **010 — FS-tree map-reduce** (DONE): finding — for holistic classification DON'T decompose
  (54% per-item → 100% whole). Completes the fourth law.
- **005 — a composite pipeline:** Jimmy (JSON extraction, 100%) → deterministic logic → Jimmy
  (render). *(not done)*
- **Next open threads:** 009c (reaction-diffusion rule with inhibition → Turing patterns?);
  007b (a harder checker: embeddings + degeneration filter — will open accumulation move?);
  008b (asymmetric agents on a NON-optimization task: dialogue/negotiation as an artifact).
- **The Holy Grail:** a loop with anti-collapse. The building blocks are ready: scalar selector
  (003B), **external memory + novelty pressure as anti-collapse (003b, empirically validated)**.
  Three permitted sources of emergence: (a) selection+fitness (Jimmy = mutation operator, 14k t/s =
  thousands of generations), (b) accumulating external state (a world: file/graph/grid), (c)
  asymmetric agents (different system prompts + interaction rules). Requirement: an explicit
  anti-collapse mechanism + a reported diversity-over-time metric, not just transcripts.
  - ✅ **Precondition (sustained load) MET:** 800 sustained requests at conc=8 = **0 errors**,
    57.5 rps, stable latency (drift −8%). `sustained.py`. conc=8 is safe for a persistent loop.

## How to add an experiment
`experiments/NNN-slug/` with `hypothesis.md` (hypothesis + metric + **threshold** before running),
`run.py` (produces a number), `verdict.md` (KEEP/DISPOSE + the number that decided it). Add an entry
to `LOG.md`.

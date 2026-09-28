# LOG — propose / evaluate / dispose / repeat

An append-only journal. Each entry: date · hypothesis · metric · threshold · **KEEP/DISPOSE**.
Negative results are half the product — dead ideas stay with the number that killed them.

---

## 2026-09-22 — Phase 0: characterization
- **Hypothesis:** Jimmy fits the abstraction "fast, dumb, free per-sample".
- **Metric/threshold:** 8 probes, each with a concrete number (see CHARACTERIZATION.md).
- **Result:** determinism@topK1 ✓, diversity@topK8=1.0 ✓, topK=8 ceiling hard, parameters ignored,
  one model, context ~6k, budget ~38 req/s@conc8.
- **Verdict:** **KEEP.** Operational thesis confirmed: *lever = concurrency*, *best-of-N alive*.

---
## 2026-09-22 — 001: majority voting (self-consistency) on math
- **Hypothesis:** voting over k samples compensates per-sample stupidity (when verification is cheap).
- **Metric/threshold:** vote-31 ≥ +15 pts vs single AND ≥70%. 24 tasks × 31 samples.
- **Result:** single 64.7% → vote-21 **93.0%** (plateau), lift **+27 pts**, 744 req/0 errors.
- **Verdict:** **KEEP.** Note: fixes variance, not bias (2/24 tasks with a systematic error are
  unrepairable). Sweet-spot k≈15-21.

## 2026-09-22 — 002: structured JSON extraction (best-of-N + validator)
- **Hypothesis:** a hard validator + best-of-N gives reliable JSON in a pipeline.
- **Metric/threshold:** validity@best-of-8 ≥95% AND intent-accuracy(vote) ≥80%. 20 inputs × 8.
- **Result:** validity@best-of-8 **100%** ✅, intent-accuracy **70%** ❌. 160 req/0 errors.
- **Verdict:** **PARTIAL KEEP.** JSON format solved (100%); semantic classification not
  (bias + label ambiguity). Confirms the law: *volume fixes variance, not bias.*

## 2026-09-22 — 003: Jimmy as a candidate generator (SPLIT)
- **Hypothesis:** diversity=1.0 → Jimmy generates candidates, a selector picks; diversity=the product.
- **A (coverage):** threshold ≥40% of the space. Result 17.5%/18.1% (mode-collapse) → **DISPOSE**
  (lift 7-9× but saturation).
- **B (selection):** threshold ≥25% reduction. Result **26.9%** → **KEEP**. best-of-N + a scalar
  scorer works.
- **Meta:** volume helps OPTIMIZATION, not EXPLORATION. Sampling spiked on modes.

## 2026-09-22 — 003b: anti-mode with external memory (KEEP, breakthrough)
- **Hypothesis:** external "seen" state + novelty pressure breaks mode-collapse.
- **Threshold:** ≥60% of the space AND ≥2× the control (equal budget without feedback). 480 req/0 errors.
- **Result:** Europe **77.3%** (3.1×), US states **80.0%** (4.4×). **KEEP.**
- **Significance:** the first working building block of the Holy Grail — anti-collapse empirically
  validated.

## 2026-09-22 — 006 + 006b: the Holy Grail as a GA (DISPOSE of optimization-emergence)
- **Hypothesis:** Jimmy as a mutation operator in a GA — evolution beats best-of-N at equal budget.
- **Threshold:** A_best ≥ D+2/3 and ≥1.25D. 4 arms (GA / random-selection / collapse / control).
  2×1024 req.
- **006 (alliteration):** target saturated in the seed (A=D=12) → DISPOSE-with-diagnosis, redesigned.
- **006b (conjunction, harder):** A=D=**20**, emergence **False**. Confound: seed ceiling, untouched by
  anyone (24 constructible, unreached) → binds per-output capability, not search.
- **Verdict:** **DISPOSE** of the optimization variant. Selection only MAINTAINS quality (B→0 without it).
- **Resolution (HOLY_GRAIL.md):** Grail = **accumulation** (003b: 18→80%), not optimization (best-of-N
  wins when optimum ⊂ one output). Open frontier: open space + soft checker.

## 2026-09-22 — 004: map-reduce over a long document (APPLICATION, KEEP)
- **Hypothesis:** parallel chunking beats the context limit for extraction from long documents.
- **Threshold:** MR recall ≥0.9 and lift ≥30 pts. Doc ~15.8k tok (2.6× the limit), 24 gold, 34 req.
- **Result:** single-shot **0.00** (empty reply over the limit) → map-reduce **1.00**, lift **+100 pts**.
- **Verdict:** **KEEP.** Canonical pattern: chunk(≤1.2k) → map extraction → reduce union.

## 2026-09-22 — 007: open accumulation with a soft checker (DISPOSE of openness)
- **Hypothesis:** accumulation stays open in an unbounded space with a soft novelty gate.
- **Threshold:** accept-rate over the last 1/3 ≥0.5. 20 rounds × 16, inventing creatures, Jaccard gate.
- **Result:** accept-rate 0.22→**0.06** (saturation), in-window dups 272 vs out-of-window 15.
- **Verdict:** **DISPOSE.** Mechanism: (1) instruction-following collapses (echoes the window),
  (2) phonotactic/semantic collapse, (3) a hole in the soft gate. Accumulation = enumerable recall
  (003b), NOT open invention. Answers the named Grail frontier.

## 2026-09-22 — 008: asymmetric agents Generator↔Critic (DISPOSE, hidden scorer)
- **Hypothesis:** a soft critic-in-the-loop beats best-of-N at equal budget.
- **Threshold:** refine-final ≥ +10% vs best-of-N (budget 7 req/item). 16 items, 224 req.
- **Result:** refine 3.14→4.01 (+28% vs gen0), but best-of-N=**4.58 > 4.01** → **DISPOSE.**
- **Significance:** confirms laws 1+3 on an asymmetric architecture. The critic shares the bias,
  sometimes breaks things; if you have any scorer at all → best-of-N wins.

## 2026-09-22 — 009 + 009b: Jimmy as a cellular-automaton rule (EMERGENCE)
- **Hypothesis:** a global spatial structure emerges from Jimmy's local rule.
- **Threshold:** neighbor_sim − random_sim ≥ +0.10, topology-dependent. 6×6 grid, 25 steps, 2×1800 req.
- **009 "blend the neighbors":** Δsim=−0.10 → DISPOSE of domains, but a DISCOVERY: global semantic
  collapse, self-reference (words about mixing), a liquid phase.
- **009b "pick among the neighbors" (voter/Ising):** Δsim=**−0.354**, **CHECKERBOARD** antiferromagnetic
  (period-2 blinker); CTRL (random neighbors) → uniform fixation (mean-field). **Emergence confirmed**
  — global order strictly topology-dependent. A project highlight.

## 2026-09-22 — 011: teaching Jimmy to write bash (decomposition vs monolith)
- **Hypothesis (user's):** breaking into irreducible steps + reduce beats a monolith.
- **Arms:** A single, B best-of-N, C1 decomposition with a given plan, C2 with a Jimmy plan.
  Validation = EXECUTION on tests; the harness validated on references. 448 req.
- **Result:** B **46.7%** > A 30% > C1=C2 **16.7%**. Decomposition HURTS; C1=C2 → not planning,
  the decomposition itself. C2 had more budget than B and lost.
- **Verdict:** **DISPOSE of decomposition for codegen.** Recommendation: best-of-N of the whole +
  execution.

## 2026-09-22 — 010: FS-tree analysis (map file → reduce folder → reduce tree)
- **Hypothesis:** does Jimmy-reduce degrade multi-level (the open question from 011)?
- **Result (INVERSE):** L0 map per-file **54%**, L1 deterministic **50%**, L1 **Jimmy-holistic 100%**,
  L2 tree recall **1.0**. Jimmy-reduce > deterministic by +50 pts. 125 req.
- **Discovery:** for classification/gestalt the aggregate is EASIER than the parts — per-item
  decomposition throws away context and injects noise. Do NOT decompose holistic judgments; show Jimmy
  the whole.
- **Unified decomposition taxonomy (004/010/011)** — see FINDINGS "Fourth law".

## 2026-09-22 — 012: "big input → small output" (bash docs into the generator)
- **Hypothesis (user's):** adding the bash documentation to the prompt helps the generator.
- **Setup:** the same 6 tasks, best-of-N fixed, context varied: NONE / cheatsheet(160 tok) /
  man bash 4k / man bash 10k(over-limit). 324 req.
- **Result:** NONE 38.9% → **CHEATSHEET 94.4% (+55 pts)** → MANBASH_4K 50% (+11) → MANBASH_OVER **0%**.
- **Verdict:** "big input" LOSES (whole dump=0%, generic 4k barely +11). **A small TARGETED cheatsheet
  wins (+55).** Refinement: not size, but RELEVANCE at minimal size. The winning recipe for code:
  RAG(targeted) + best-of-N + execution = 94%.

## 2026-09-22 — 013: hierarchical summarization of a huge article (Wikipedia ML, ~15k tok)
- **Hypothesis (user's):** chunk by section + hard constraints in the system prompt = a good summary.
- **Arms:** NAIVE (single-shot), MR_HARD (holistic reduce), MR_LOOSE (loose), MR_HIER (2-level reduce).
  173 req.
- **Result:** NAIVE silently truncates (prefill=110 of 15k, recall 7%). Map reliable (faith ~0.9). The
  holistic reduce breaks the limits (498-962 words); **MR_HIER fixes it: adherence 1.0, 269 words,
  compression 42×**. HARD ≫ LOOSE on format (0.92-1.0 vs 0.0). Compression↔coverage tradeoff (recall
  ~1/3 of the main topics).
- **Verdict:** **PARTIAL KEEP.** Pipeline works; hard constraints govern format (confirms the user's
  idea); but REDUCE must also be chunked (hierarchically). Extends the fourth law.

## 2026-09-22 — 014: web-adjacent tasks on raw HTML (curl → chunks → operations)
- **Hypothesis:** Jimmy on HTML chunks does link/text/keyword extraction + topic filter + description.
- **Axis:** mechanical (a deterministic baseline exists) vs semantic (none). HN page. 31 req.
- **Result:** mechanical — Jimmy LOSES to regex/parser/grep (links F=0.64, strip F1=0.68, keyword
  F=0.69 vs deterministic 1.0). Semantic — Jimmy ADDS VALUE (topic_filter P/R/F=1.0/0.89/**0.94**,
  correct description) — no deterministic equivalent.
- **Verdict:** a capability boundary → **mechanics: deterministic code; semantics: Jimmy.** In a
  pipeline the parser does the mechanics, Jimmy only the semantic subtasks. (Sixth law.)

## 2026-09-22 — 015: meta-prompting / problem-solving (Jimmy generates a propose/dispose/evaluate scaffold)
- **Hypothesis:** Jimmy is given a problem example, generates 3 prompts; FUNCTIONAL evaluation (run the
  scaffold).
- **Setup:** PTASK (discriminating, deterministic fitness) + MATH (null). Arms: JIMMY_BEST/WORST, HUMAN,
  BESTOFN_DET. Structural vs execution separated. 552 req.
- **Result:** structural_rate 0.60; PTASK fitness JIMMY=0, HUMAN=2.38, **BESTOFN_DET=8.88** (prediction
  Jimmy≤HUMAN≤DET confirmed). MATH 100%=100% (null). eval-parse 1.0.
- **Diagnosis (artifacts):** Jimmy's proposer gives a 14-word example at a 12-word limit; the evaluator
  is written like a baked-in ANSWER, not a general INSTRUCTION, grading vibes not fitness. Glimmer: the
  worst-evaluator named a mechanical criterion, but as an example not a prompt.
- **Verdict:** **DISPOSE.** Jimmy articulates ideas, doesn't package them into a working scaffold. The
  bottleneck = the evaluator; a soft-evaluator is useless for selection. Recommendation: Jimmy=proposer,
  evaluator/disposer deterministic. (Seventh law.)

## 2026-09-22 — 016: recursive defensive task decomposition (deterministically orchestrated)
- **Hypothesis (user's):** recursively decompose to the atomic layer + defensive steps (verify
  preconditions) = a bulletproof plan.
- **Setup:** a Python orchestrator (tree/cap/dedup), Jimmy 1 step/node. Arms: RECURSIVE_DEFENSIVE/PLAIN,
  SINGLESHOT, bounded depth-2. ~200 req.
- **Result:** the defensive technique WORKS: defensive-ratio **0.90 (DEFENSIVE) vs 0.54 (PLAIN)**,
  +35 pts. BUT recursion explodes (299 leaves, hits the cap), Jimmy NEVER says ATOMIC (no
  self-termination), cross-branch redundancy ~20%. Depth-2 (49 leaves, 0.78) = a useful sweet-spot.
- **Verdict:** **PARTIAL KEEP.** Defensive steps: KEEP (strongly). Deep recursion to an "atomic layer":
  DISPOSE (Jimmy doesn't know the bottom → the orchestrator sets it). Recipe:
  shallow+defensive+deterministic dedup.

## 2026-09-22 — 017: generating real commands for the steps from 016 (planner→executor)
- **Hypothesis:** Jimmy generates real shell commands for ~34 defensive steps (depth-2).
- **Setup:** read-only executed in a sandbox (allowlist+blocklist), mutating ones checked statically.
  SINGLE vs BEST-of-N. 246 req.
- **Result:** BEST-of-N: bash -n **1.0**, real-command **1.0**, exec-ok **0.96** (SINGLE: 1.0/0.85/0.65).
  BUT semantic match only **0.79** — ~20% works-but-wrong (echo-cheat, wrong pkg-manager rpm/apt).
  Jimmy emitted `init 6` (REBOOT) for a "verify" step — the allowlist did NOT run it (the sandbox held).
- **Verdict:** **KEEP for FORM (valid/real/runnable), not for INTENT** (0.79). best-of-N+exec-filter
  wins again. Output = a reviewable draft-automation; never unattended (Jimmy inserts destruction).

## 2026-09-22 — 018: four meta-analytical tests on commands (describe/judge/compare/regenerate)
- **Setup:** a bank of 12 known read-only commands with hard gold (purpose, correct/incorrect task).
  216 req.
- **T1 describe:** recall 0.68, faithful **1.0** — KEEP (knowledge recall).
- **T2 match-judge (direct):** acc 0.54, mismatch-recall **0.08** — RUBBER-STAMP (positive bias, voting
  doesn't help). DISPOSE, confirms Law 7.
- **T3 "describe→compare descriptions":** acc **0.83**, differs-recall **1.0** — a REPAIR +30 pts;
  mediating judgment through a faithful description sidesteps the rubber-stamp bias. KEEP (technique).
- **T4 regenerate:** diverse 1.0, valid+real 1.0, output-equiv 0.58 — strong form, moderate intent.
- **Highlight:** T2 vs T3 — the same judgment, +30 pts from reframing "match?" → "describe then compare".

## 2026-09-22 — 019: logic benchmark L0-L5 (read/evaluate/validate/analyze)
- **Setup:** programmatically generated instances, GOLD brute-forced in Python. Balanced accuracy
  (chance=0.5), gold balanced 8T+8F/level. Voting-5. 720 req (2 runs).
- **Curve (bal_acc):** L0 **0.88** → L1 0.62, L2 0.75, L3 0.69, L4 0.62, L5 0.75 (n=8). READ 0.75.
- **Result:** propositional logic (L0) solid, no bias; from quantifiers (L1+) it collapses to
  near-chance (0.6-0.75) with a persistent TRUE bias (recall_False<recall_True). Voting doesn't rescue
  (bias, Law 1).
- **Self-correction:** the first run gave an apparent L3=1.0/L4=0.83 — an ARTIFACT of gold imbalance
  (L4=6T/0F → constant TRUE=1.0). Balanced accuracy + class-balance + true_rate corrected it.
  (Ninth law.)
- **Verdict:** trust Jimmy on simple boolean logic, NOT on quantifier/higher-order logic.

## 2026-09-23 — 020: ArchWiki → man-compatible manpage (APPLICATION)
- **Task:** systemd ArchWiki (~12k tok stripped) → a man page. Arms: A (Jimmy emits troff), B
  (Jimmy-content + deterministic troff). Validation: groff/man renders. 11 req.
- **Result:** ARM B: renders ✅, **0 warnings**, NAME/DESC/SEE ALSO sections, NAME valid, faithfulness
  0.86, 20 commands, 12 SEE ALSO (regex). `man ./systemd.1` opens correctly. ARM A: renders but 15
  warnings + broken NAME format.
- **Verdict:** **KEEP** — a working tool. Laws 6+7 architecture: Jimmy=content, Python=troff/formatting;
  chunk→map→hierarchical reduce (013). Artifact: experiments/020.../systemd.1. Jimmy-direct-troff a
  worse fallback.

## 2026-09-23 — 021: manpage → tldr documentation (compatible with `tldr --render`)
- **Task:** man tar / journalctl → a tldr page (Client Spec 2.3). Arms: A (Jimmy direct md), B (Jimmy
  content + Python format). Validation: tldr --render, format checker, faithfulness, coverage vs the
  canonical page.
- **Result:** tar ARM B: renders in REAL tldr, compliant, faithful 1.0, idiomatic examples.
  journalctl ARM B: 0 examples (unstable) → non-compliant. ARM A: always non-compliant (wrong
  structure).
- **Key point:** quality is STRONGLY prompt-dependent — "extract examples" → a shallow option
  enumeration; "most common real uses, imperative, short flags" → a good tldr. The coverage metric
  failed (it caught paths). Even the det-URL was wrong for journalctl.
- **Verdict:** **PARTIAL KEEP** — a draft-generator for rich manpages (tar) + a precise prompt + hybrid;
  unstable per-command, needs human review. Form OK, curation/intent weak and prompt-dependent.

## 2026-09-28 — 022: Jimmy as a synthetic training-data generator (downstream proof)
- **Task:** AG News 4-class. The same classifier trained on data from different sources, measured by
  macro-F1 on the REAL gold test. Two students: A=Multinomial NB (numpy, deterministic bag-of-words,
  gold 2000), B=ICL (Jimmy few-shot, gold 160). N=400 (100/class) matched. Arms: FLOOR / REAL /
  JIMMY-IID / JIMMY-NOVELTY (003b: memory+novelty pressure).
- **Threshold (pre-registered):** gap closure G=(F1_j−F1_floor)/(F1_real−F1_floor) ≥0.50 ok, ≥0.75
  good; mode collapse when distinct<0.90.
- **Result:** NB (floor=majority 0.10) — REAL 0.796, IID 0.617 (**G=0.74**), NOVELTY 0.429 (G=0.47).
  ICL (floor=ZERO-SHOT 0.517, because Jimmy already knows how to classify news) — REAL 0.729, IID 0.665
  (**G=0.70**), NOVELTY 0.713 (G=0.93); the three sources mutually indistinguishable (SE≈0.033, IID vs
  NOVELTY 1.4 SE), but all >zero-shot by >3 SE (exemplars carry signal, mostly on Sci/Tech: zero-shot
  recall 0.0). NOVELTY splits the students: worse on NB (delta 0.188 ≫ std 0.018), ≈IID on ICL. Two
  real deficits of the Jimmy pool vs REAL @N: coverage (vocab 2142/1998 vs 4583) AND label fidelity
  (self-check 0.83/0.74, style-gap 0.94/0.83) — NOVELTY worse on BOTH (didn't buy coverage).
  distinct_rate=1.0 = a bad instrument.
- **Verdict:** **KEEP** (Jimmy = a useful training-data generator for bag-of-words/ICL students on
  topic classification) + **DISPOSE of novelty pressure without a hard checker** (label drift +
  degradation under long memory context). Recipe: IID + deterministic dedup + optional forced-4-way
  filter. **OPEN:** SFT data for a fine-tuned LM (untested; torch available).

<!-- next entries below -->

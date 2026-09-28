# THE HOLY GRAIL — resolved

> Project goal: "an infinite Jimmy-based loop with emergent properties."

After experiments 003b, 006, 006b the Grail has a concrete, empirical answer — and NOT the one we
expected.

## Resolution: the Grail is ACCUMULATION, not OPTIMIZATION

The only dimension on which our results actually differ is whether the **optimum fits inside a single
Jimmy output**:

| | regime | control (best-of-N, equal budget) | loop | verdict |
|---|--------|-----------------------------------|------|---------|
| **006 / 006b** | optimum ⊂ one output (GA over a scalar) | finds the optimum immediately (A=D=20/12) | adds nothing | loop is POINTLESS |
| **003b** | target > one output (coverage of 44 countries) | **18-25%** (mode-collapse) | **77-80%** (accumulation) | loop is the ONLY thing that works |

**Conclusion:** an emergent loop makes sense if and only if it builds a structure **larger than a
single generation**, in external state. No single Jimmy output contains 34 countries — that structure
arose through accumulation across rounds + novelty pressure. That is the "emergent property": an
artifact the model would not produce on its own.

When the solution does fit in one output, **best-of-N wins** — because Jimmy is so fast and diverse
that hundreds of samples find the optimum without any evolutionary machinery. Selection in the loop
only MAINTAINS quality (without it: collapse to invalidity, 006b arm B: 20→0), it doesn't exceed it.

## Important caveat on the confound (006/006b)

In both runs the fitness ceiling was set **in the seed** and untouched by any arm (control included):
the constructible 24 was not reached by anyone. So 006/006b prove "evolution doesn't beat sampling",
but the binding constraint was **Jimmy's per-output capability**, not the search strategy. We do NOT
claim that sampling "densely covers the space" — it doesn't (24 exists, unfound). This strengthens the
contrast with 003b, where the target PROVABLY exceeds one output.

## Recipe for a working emergent loop (validated core)
1. **External state** accumulating the result (set / graph / file / world).
2. **Jimmy as the operator** generating candidate extensions of the state (topK=8, diversity 1.0).
3. **Novelty pressure**: inject into the prompt "you already have: [sample of state], give me
   SOMETHING DIFFERENT".
4. **Deterministic filter** for candidate validity (checker/validator) before adding to the state.
5. **A diversity/growth-over-time metric** as the report (not transcripts).
→ This is exactly the 003b loop (coverage 18% → 80%).

## Open frontier (named, UNEXPLORED — the next experiment for a successor)
003b accumulates over a **finite, externally-enumerable** space (44 countries) with a **hard checker
I hardcoded**. An "infinite loop" implies an **open** space, where valid states cannot be
pre-enumerated and the checker is soft. Does accumulation still work when:
- the space is unbounded (no "tail of weights" to saturate — 003b saturated at ~80% because it hit the
  boundary of 8B's representation; an open space has no such boundary),
- candidate validity is judged by a soft judge (e.g. Jimmy itself or a stronger model), not a set?

This is the real next question of the Grail — e.g. open-ended knowledge-graph building / world-map /
a growing corpus, where novelty is judged by embedding distance, not set membership.
**Status: unresolved.** "Grail = accumulation" is proven for a finite space with a hard checker; for
an open one — a hypothesis.

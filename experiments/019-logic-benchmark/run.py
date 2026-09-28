"""019 — benchmark logiczny: krzywa zdolności przez rzędy logiki L0..L5.

Instancje generowane programowo, GOLD liczony w Pythonie (brute-force po małych domenach).
Operacje: evaluate (wartość logiczna), validate (ważność/tautologia), analyze (równoważność/model),
read (pytanie strukturalne). Jimmy odpowiada z głosowaniem-5. Accuracy per poziom i per operacja.

Uruchom: python3 experiments/019-logic-benchmark/run.py
"""
from __future__ import annotations

import asyncio
import itertools
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402

HERE = Path(__file__).parent
VOTE = 5
SYS_TF = ("You are a precise logic engine. Determine whether the statement is TRUE or FALSE given the "
          "definitions. Reason carefully, then answer on the last line with exactly: ANSWER: TRUE or "
          "ANSWER: FALSE.")
SYS_NUM = ("You are a precise logic parser. Answer the question with a single integer on the last line "
           "as: ANSWER: <integer>.")


def parse_tf(text: str):
    m = re.search(r"ANSWER:\s*(TRUE|FALSE)", text, re.IGNORECASE)
    if m:
        return m.group(1).upper() == "TRUE"
    t = text.upper()
    # fallback: ostatnie wystąpienie
    it = list(re.finditer(r"\b(TRUE|FALSE)\b", t))
    return it[-1].group(1) == "TRUE" if it else None


def parse_num(text: str):
    m = re.search(r"ANSWER:\s*(-?\d+)", text)
    if m:
        return int(m.group(1))
    nums = re.findall(r"-?\d+", text)
    return int(nums[-1]) if nums else None


# ==================== GENERATORY (render, gold, op) ====================
def gen_L0(rng):
    """Propositional: evaluate / validate(tautology)."""
    tpls = [
        ("({p} AND {q}) OR (NOT {r})", lambda v: (v['p'] and v['q']) or (not v['r'])),
        ("({p} IMPLIES {q}) AND ({q} IMPLIES {r})", lambda v: ((not v['p']) or v['q']) and ((not v['q']) or v['r'])),
        ("NOT ({p} AND {q}) OR {r}", lambda v: (not (v['p'] and v['q'])) or v['r']),
        ("({p} XOR {q}) AND {r}", lambda v: (v['p'] != v['q']) and v['r']),
        ("({p} OR {q}) IMPLIES ({q} AND {r})", lambda v: (not (v['p'] or v['q'])) or (v['q'] and v['r'])),
    ]
    text, fn = rng.choice(tpls)
    text = text.format(p="P", q="Q", r="R")
    if rng.random() < 0.5:  # evaluate
        v = {'p': rng.random() < 0.5, 'q': rng.random() < 0.5, 'r': rng.random() < 0.5}
        gold = bool(fn({'p': v['p'], 'q': v['q'], 'r': v['r']}))
        asg = ", ".join(f"{k.upper()}={'true' if val else 'false'}" for k, val in v.items())
        return (f"Propositional logic. Given {asg}. Is the statement TRUE?\n  Statement: {text}",
                gold, "evaluate")
    else:  # validate: tautology?
        allv = [dict(zip("pqr", c)) for c in itertools.product([False, True], repeat=3)]
        gold = all(fn(v) for v in allv)
        return (f"Propositional logic. Is the following a TAUTOLOGY (true under ALL assignments of P,Q,R)?"
                f"\n  Statement: {text}", gold, "validate")


def rand_model(rng, dsize=3):
    D = list(range(1, dsize + 1))
    P = set(x for x in D if rng.random() < 0.5)
    Q = set(x for x in D if rng.random() < 0.5)
    R = set((a, b) for a in D for b in D if rng.random() < 0.4)
    return D, P, Q, R


def model_str(D, P, Q, R):
    return (f"Domain D = {{{', '.join(map(str, D))}}}. "
            f"P = {{{', '.join(map(str, sorted(P)))}}} (elements where P holds). "
            f"Q = {{{', '.join(map(str, sorted(Q)))}}}. "
            f"R = {{{', '.join(f'({a},{b})' for a, b in sorted(R))}}} (pairs where R holds).")


def gen_L1(rng):
    """First-order over finite model."""
    D, P, Q, R = rand_model(rng)
    tpls = [
        ("∀x (P(x) → Q(x))", lambda: all((x not in P) or (x in Q) for x in D), "validate"),
        ("∃x (P(x) ∧ Q(x))", lambda: any((x in P) and (x in Q) for x in D), "evaluate"),
        ("∀x ∃y R(x,y)", lambda: all(any((x, y) in R for y in D) for x in D), "evaluate"),
        ("∃x ∀y R(x,y)", lambda: any(all((x, y) in R for y in D) for x in D), "evaluate"),
        ("∀x (P(x) → ∃y (R(x,y) ∧ Q(y)))",
         lambda: all((x not in P) or any(((x, y) in R and y in Q) for y in D) for x in D), "evaluate"),
    ]
    text, fn, op = rng.choice(tpls)
    return (f"First-order logic. {model_str(D,P,Q,R)}\n  Is this TRUE? Statement: {text}", bool(fn()), op)


def gen_L2(rng):
    """Second-order: quantify over SUBSETS of D."""
    D, P, Q, R = rand_model(rng, dsize=3)
    subsets = [set(c) for k in range(len(D)+1) for c in itertools.combinations(D, k)]
    tpls = [
        ("∃S⊆D ∀x (x∈S ↔ P(x))", lambda: any(all((x in S) == (x in P) for x in D) for S in subsets)),
        ("∀S⊆D ∃x (x∈S ∨ P(x))", lambda: all(any((x in S) or (x in P) for x in D) for S in subsets)),
        ("∃S⊆D (S≠∅ ∧ ∀x∈S P(x))", lambda: any(len(S) > 0 and all(x in P for x in S) for S in subsets)),
        ("∃S⊆D ∀x (P(x) → x∈S) ∧ ∀y (y∈S → Q(y))",
         lambda: any(all((x not in P) or (x in S) for x in D) and all((y not in S) or (y in Q) for y in D) for S in subsets)),
    ]
    text, fn = rng.choice(tpls)
    return (f"Second-order logic (S ranges over all SUBSETS of D). {model_str(D,P,Q,R)}\n"
            f"  Is this TRUE? Statement: {text}", bool(fn()), "evaluate")


def gen_L3(rng):
    """Third-order: quantify over FUNCTIONS f: D→D."""
    D, P, Q, R = rand_model(rng, dsize=2)
    funcs = [dict(zip(D, vals)) for vals in itertools.product(D, repeat=len(D))]
    tpls = [
        ("∃f:D→D ∀x R(x, f(x))", lambda: any(all((x, f[x]) in R for x in D) for f in funcs)),
        ("∀f:D→D ∃x P(f(x))", lambda: all(any(f[x] in P for x in D) for f in funcs)),
        ("∃f:D→D ∀x (P(x) → Q(f(x)))", lambda: any(all((x not in P) or (f[x] in Q) for x in D) for f in funcs)),
    ]
    text, fn = rng.choice(tpls)
    return (f"Third-order logic (f ranges over all FUNCTIONS from D to D). {model_str(D,P,Q,R)}\n"
            f"  Is this TRUE? Statement: {text}", bool(fn()), "evaluate")


def gen_L4(rng):
    """Fourth-order: quantify over PROPERTIES OF SUBSETS (functions: subset→bool) over |D|=2."""
    D = [1, 2]
    subsets = [frozenset(c) for k in range(len(D)+1) for c in itertools.combinations(D, k)]  # 4
    P = set(x for x in D if rng.random() < 0.5)
    # Φ ranges over all functions from subsets→bool (2^4=16)
    all_phi = [dict(zip(subsets, bits)) for bits in itertools.product([False, True], repeat=len(subsets))]
    tpls = [
        # prawdziwe
        ("∃Φ (Φ(∅)=false ∧ Φ(D)=true ∧ ∀S (Φ(S) → S≠∅))",
         lambda: any((not phi[frozenset()]) and phi[frozenset(D)] and all((not phi[S]) or len(S) > 0 for S in subsets) for phi in all_phi)),
        ("∀Φ (Φ(D)=true → ∃S (Φ(S) ∧ S⊆D))",
         lambda: all((not phi[frozenset(D)]) or any(phi[S] and S.issubset(frozenset(D)) for S in subsets) for phi in all_phi)),
        # fałszywe
        ("∀Φ (Φ(∅)=true)", lambda: all(phi[frozenset()] for phi in all_phi)),
        ("∀Φ (∃S Φ(S))", lambda: all(any(phi[S] for S in subsets) for phi in all_phi)),
        ("∃Φ ((∀S ¬Φ(S)) ∧ (∃S Φ(S)))",
         lambda: any(all(not phi[S] for S in subsets) and any(phi[S] for S in subsets) for phi in all_phi)),
    ]
    text, fn = rng.choice(tpls)
    return (f"Fourth-order logic (Φ ranges over all PROPERTIES of subsets of D, i.e. functions "
            f"subset→boolean). Domain D={{1,2}}, subsets are ∅,{{1}},{{2}},{{1,2}}.\n"
            f"  Is this TRUE? Statement: {text}", bool(fn()), "evaluate")


# L5 — ręcznie skonstruowane, gold zweryfikowany argumentem (zbalansowane 4T+4F, ilustracyjne)
L5_INSTANCES = [
    # TRUE
    ("Fifth-order logic. Let D={1}. 𝒬 ranges over all families of properties-of-subsets. "
     "Statement: ∃𝒬 such that 𝒬 is non-empty AND every member of 𝒬 assigns true to the subset {1}. "
     "Is this TRUE?", True, "evaluate"),
    ("Fifth-order logic over D={1,2}: 'There exists a set X of functions such that every function in X "
     "maps at least one input to itself, and X is non-empty.' Is this TRUE?", True, "evaluate"),
    ("Fifth-order logic over D={1,2}: 'There exists a non-empty family F of properties-of-subsets.' "
     "Is this TRUE?", True, "evaluate"),
    ("Fifth-order logic over D={1}: 'There exists a non-empty set of relations on D in which every "
     "relation is reflexive.' Is this TRUE?", True, "evaluate"),
    # FALSE
    ("Fifth-order logic. Let D={1}. 𝒬 ranges over families of properties-of-subsets. "
     "Statement: ∀𝒬 (𝒬 is empty). Is this TRUE?", False, "evaluate"),
    ("Fifth-order logic over D={1,2}: 'For every collection C of sets-of-subsets, C contains the empty "
     "collection.' Is this necessarily TRUE?", False, "evaluate"),
    ("Fifth-order logic over D={1,2}: 'For every family F of properties-of-subsets, F is non-empty.' "
     "Is this TRUE?", False, "evaluate"),
    ("Fifth-order logic over D={1,2}: 'There is NO set of functions from D to D that contains the "
     "identity function.' Is this TRUE?", False, "evaluate"),
]

# read (strukturalne) — parsowanie, nie rozumowanie
READ_INSTANCES = [
    ("How many quantifiers are in this formula? ∀x ∃y ∀z (R(x,y) → P(z))", 3, "read", "L1"),
    ("How many DISTINCT variables are bound in: ∀x ∃y (P(x) ∧ Q(y))", 2, "read", "L1"),
    ("What is the quantifier order (0=propositional, 1=first-order over elements, 2=quantifies over "
     "subsets)? Formula: ∃S⊆D ∀x∈S P(x). Answer the number.", 2, "read", "L2"),
    ("How many quantifiers: (P ∧ Q) ∨ ¬R", 0, "read", "L0"),
]


async def run_tf_batch(jc, items):
    """items: list of (text, gold, op). Zwraca listy predykcji @1 i @vote."""
    async def one(text):
        rs = await jc.sample_n(text, VOTE, system_prompt=SYS_TF, top_k=8)
        preds = [parse_tf(r.content) for r in rs if r.ok]
        preds = [p for p in preds if p is not None]
        at1 = preds[0] if preds else None
        vote = Counter(preds).most_common(1)[0][0] if preds else None
        return at1, vote
    return await asyncio.gather(*[one(t) for t, _, _ in items])


def balanced_pool(gen, rng, k_each):
    """Zbieraj instancje aż będzie k_each True i k_each False (zbalansowany zbiór)."""
    T, F = [], []
    for _ in range(4000):
        inst = gen(rng)
        (T if inst[1] else F).append(inst)
        if len(T) >= k_each and len(F) >= k_each:
            break
    return T[:k_each] + F[:k_each]


def bal_acc(preds, items):
    """balanced accuracy = średnia recall po klasach (stała odpowiedź → 0.5)."""
    tp = sum(1 for (_, v), (_, g, _) in zip(preds, items) if g and v == g)
    tn = sum(1 for (_, v), (_, g, _) in zip(preds, items) if (not g) and v == g)
    nT = sum(1 for _, g, _ in items if g)
    nF = len(items) - nT
    rec_t = tp / nT if nT else 0
    rec_f = tn / nF if nF else 0
    return round(0.5 * (rec_t + rec_f), 3), round(rec_t, 3), round(rec_f, 3)


async def main():
    rng = random.Random(0)
    K = 8  # k_each → 16 instancji/poziom (8T+8F)
    levels = {
        "L0": balanced_pool(gen_L0, rng, K),
        "L1": balanced_pool(gen_L1, rng, K),
        "L2": balanced_pool(gen_L2, rng, K),
        "L3": balanced_pool(gen_L3, rng, K),
        "L4": balanced_pool(gen_L4, rng, K),
        "L5": L5_INSTANCES,  # już zbalansowane 4T+4F
    }
    results = {}
    per_op = defaultdict(lambda: [0, 0])
    async with JimmyClient(max_concurrency=8) as jc:
        for lvl, items in levels.items():
            preds = await run_tf_batch(jc, items)
            ba, rt, rf = bal_acc(preds, items)
            raw = round(sum(1 for (_, v), (_, g, _) in zip(preds, items) if v == g)/len(items), 3)
            true_rate = round(sum(1 for _, v in preds if v is True)/len(preds), 3)
            for (_, v), (_, g, op) in zip(preds, items):
                per_op[op][1] += 1
                per_op[op][0] += int(v == g)
            results[lvl] = {"n": len(items), "balanced_acc": ba, "recall_True": rt, "recall_False": rf,
                            "raw_acc": raw, "jimmy_true_rate": true_rate}
            print(f"  {lvl}: n={len(items)} bal_acc={ba} (recT={rt} recF={rf}) raw={raw} true_rate={true_rate}")

        # READ (numeryczne)
        async def one_read(text):
            rs = await jc.sample_n(text, VOTE, system_prompt=SYS_NUM, top_k=8)
            preds = [parse_num(r.content) for r in rs if r.ok]
            preds = [p for p in preds if p is not None]
            return Counter(preds).most_common(1)[0][0] if preds else None
        read_preds = await asyncio.gather(*[one_read(t) for t, _, _, _ in READ_INSTANCES])
        read_c = sum(1 for p, (_, g, _, _) in zip(read_preds, READ_INSTANCES) if p == g)
        results["READ_structural"] = {"n": len(READ_INSTANCES), "acc_vote": round(read_c/len(READ_INSTANCES), 3),
                                      "detail": [(g, p) for (_, g, _, _), p in zip(READ_INSTANCES, read_preds)]}
        print(f"  READ (strukturalne): acc={results['READ_structural']['acc_vote']}")
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")

    results["per_operation_vote"] = {op: round(c/t, 3) for op, (c, t) in per_op.items()}
    (HERE / "summary.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print("\n===== KRZYWA LOGICZNA (balanced accuracy, chance/stała-odp = 0.50) =====")
    for lvl in ["L0", "L1", "L2", "L3", "L4", "L5"]:
        r = results[lvl]
        bar = "█" * int(r["balanced_acc"] * 20)
        print(f"  {lvl}: {r['balanced_acc']:.2f} {bar}  (recT={r['recall_True']} recF={r['recall_False']}, "
              f"true_rate={r['jimmy_true_rate']}, n={r['n']})")
    print(f"  READ (parsowanie strukturalne, dokładne): {results['READ_structural']['acc_vote']}")
    print(f"  per-operacja (raw): {results['per_operation_vote']}")


if __name__ == "__main__":
    asyncio.run(main())

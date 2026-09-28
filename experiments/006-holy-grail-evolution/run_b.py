"""006b — cel NIENASYCALNY: koniunkcja aliteracji 'p' + 3 narzucone rzadkie slowa.

fitness = (#slow na 'p') + 5*(liczba obecnych wymaganych slow),  0 jesli struktura niewalidna.
Wymagane slowa nie zaczynaja sie na 'p' -> single-shot musi pogodzic sprzeczne cele w <=12 slowach.
Krzyzowanie: polacz aliteracyjnego rodzica z tym, co ma wymagane slowa.

Prog KEEP (pre-rejestrowany): A_best >= D_best + 3 ORAZ A_best >= 1.25*D_best.  Raportuj wynik zawsze.

Uruchom: python3 experiments/006-holy-grail-evolution/run_b.py
"""
from __future__ import annotations

import asyncio
import json
import random
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402
from jimmy.eval import distinct_rate  # noqa: E402

HERE = Path(__file__).parent
T = "p"
REQUIRED = ("quantum", "velvet", "zebra")
P, G = 16, 15
SYS = "You write single natural English sentences. Output ONLY the sentence, nothing else."

OBJECTIVE = (
    f"Write ONE natural sentence, at most 12 words, all words different, that (1) contains the words "
    f"'{REQUIRED[0]}', '{REQUIRED[1]}' and '{REQUIRED[2]}', AND (2) has as many OTHER words as "
    f"possible starting with the letter '{T}'. Output only the sentence."
)
SEED_PROMPT = OBJECTIVE
CONTROL_PROMPT = OBJECTIVE


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


def structural_valid(text: str) -> bool:
    w = tokenize(text)
    return 3 <= len(w) <= 12 and len(set(w)) == len(w)


def fitness(text: str) -> int:
    if not structural_valid(text):
        return 0
    w = tokenize(text)
    req = sum(1 for r in REQUIRED if r in w)
    allit = sum(1 for x in w if x.startswith(T))
    return allit + 5 * req


def norm(text: str) -> str:
    return " ".join(tokenize(text))


def mutation_prompt(parent: str) -> str:
    return (f"Improve this sentence: keep the words '{REQUIRED[0]}', '{REQUIRED[1]}', '{REQUIRED[2]}' "
            f"in it, make MORE of the other words start with '{T}', stay ONE natural sentence of at "
            f"most 12 words, all different. Sentence: \"{parent}\". Output only the new sentence.")


def crossover_prompt(a: str, b: str) -> str:
    return (f"Combine these into ONE natural sentence (<=12 words, all different) that contains "
            f"'{REQUIRED[0]}', '{REQUIRED[1]}', '{REQUIRED[2]}' and has many words starting with "
            f"'{T}'. A: \"{a}\"  B: \"{b}\". Output only the sentence.")


async def gen_batch(jc, prompts):
    rs = await jc.map_prompts(prompts, system_prompt=SYS, top_k=8)
    return [r.content if r.ok else "" for r in rs]


def pop_metrics(pop):
    fits = [fitness(s) for s in pop]
    return {"best": max(fits), "mean": round(statistics.mean(fits), 2),
            "distinct_rate": round(distinct_rate([norm(s) for s in pop]), 3)}


async def run_arm(jc, arm, rng):
    pop = await gen_batch(jc, [SEED_PROMPT] * P)
    history = [pop_metrics(pop)]
    valid_rates = []
    for _ in range(G):
        if arm == "C":
            prompts = [mutation_prompt(s) for s in pop]
        else:
            if arm == "A":
                parents = sorted(pop, key=fitness, reverse=True)[: max(2, P // 2)]
            else:
                parents = list(pop)
            n_fresh = 4 if (arm == "A" and pop_metrics(pop)["distinct_rate"] < 0.6) else 0
            prompts = [SEED_PROMPT] * n_fresh
            while len(prompts) < P:
                if rng.random() < 0.5 and len(parents) >= 2:
                    a, b = rng.sample(parents, 2)
                    prompts.append(crossover_prompt(a, b))
                else:
                    prompts.append(mutation_prompt(rng.choice(parents)))
        offspring = await gen_batch(jc, prompts)
        valid_rates.append(round(sum(structural_valid(o) for o in offspring) / P, 3))
        if arm == "A":
            seen, uniq = set(), []
            for s in sorted(pop + offspring, key=fitness, reverse=True):
                k = norm(s)
                if k not in seen:
                    seen.add(k); uniq.append(s)
            pop = uniq[:P]
            while len(pop) < P:
                pop.append(rng.choice(uniq) if uniq else "")
        elif arm == "B":
            pop = rng.sample(pop + offspring, P)
        else:
            pop = offspring
        history.append(pop_metrics(pop))
    champions = sorted(set(pop), key=fitness, reverse=True)[:5]
    return {"history": history, "valid_rates": valid_rates,
            "final_best": max(fitness(s) for s in pop),
            "champions": [(s, fitness(s)) for s in champions]}


async def run_control(jc):
    budget = P + G * P
    rs = await jc.sample_n(CONTROL_PROMPT, budget, system_prompt=SYS, top_k=8)
    fits = sorted(((fitness(r.content), r.content) for r in rs if r.ok), reverse=True)
    return {"budget": budget, "best": fits[0][0], "best_text": fits[0][1], "top5": fits[:5]}


async def main():
    rng = random.Random(42)
    out = {}
    async with JimmyClient(max_concurrency=8) as jc:
        for arm in ("A", "B", "C"):
            print(f"\n=== RAMIĘ {arm} ===")
            res = await run_arm(jc, arm, rng)
            out[arm] = res
            print(f"  best/gen:      {[h['best'] for h in res['history']]}")
            print(f"  mean/gen:      {[h['mean'] for h in res['history']]}")
            print(f"  distinct/gen:  {[h['distinct_rate'] for h in res['history']]}")
            print(f"  final_best={res['final_best']}")
        print("\n=== KONTROLA D ===")
        out["D"] = await run_control(jc)
        print(f"  best={out['D']['best']}  text={out['D']['best_text']!r}")
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")
    (HERE / "results_b.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    A, B, D = out["A"]["final_best"], out["B"]["final_best"], out["D"]["best"]
    emergence = (A >= D + 3) and (A >= 1.25 * D)
    print("\n===== WERDYKT 006b (pre-rejestrowane) =====")
    print(f"  A_best={A}  B_best={B}  C_best={out['C']['final_best']}  D_best(control)={D}")
    print(f"  1. Emergencja (A>=D+3 i A>=1.25D): {emergence}")
    print(f"  2. Selekcja (A>B): {A > B}")
    print(f"  CHAMPIONI A:")
    for s, f in out["A"]["champions"]:
        print(f"    [{f}] {s!r}")
    print(f"  KONTROLA D top-5:")
    for f, s in out["D"]["top5"]:
        print(f"    [{f}] {s!r}")
    (HERE / "summary_b.json").write_text(json.dumps(
        {"A_best": A, "B_best": B, "C_best": out["C"]["final_best"], "D_best": D,
         "emergence": emergence, "selection_matters": A > B,
         "champions_A": out["A"]["champions"], "control_top5": out["D"]["top5"]},
        ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

"""006 — ŚWIĘTY GRAAL: Jimmy jako operator mutacji w GA. Cztery ramiona, równy budżet.

Uruchom: python3 experiments/006-holy-grail-evolution/run.py
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
T = "p"           # litera docelowa
P = 16            # rozmiar populacji
G = 15            # generacje
SYS = "You write single natural English sentences. Output ONLY the sentence, nothing else."

SEED_PROMPT = (
    f"Write a single natural sentence of at most 12 words, all words different, with as many "
    f"words as possible starting with the letter '{T}'. Output only the sentence."
)
# Kontrola D uzywa DOKLADNIE tego samego, jasno postawionego celu.
CONTROL_PROMPT = SEED_PROMPT


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


def structural_valid(text: str) -> bool:
    w = tokenize(text)
    return 3 <= len(w) <= 12 and len(set(w)) == len(w)


def fitness(text: str) -> int:
    if not structural_valid(text):
        return 0
    return sum(1 for w in tokenize(text) if w.startswith(T))


def norm(text: str) -> str:
    return " ".join(tokenize(text))


def mutation_prompt(parent: str) -> str:
    return (f"Rewrite this sentence so MORE words start with the letter '{T}'. Keep it ONE natural "
            f"sentence, at most 12 words, all words different. Sentence: \"{parent}\". "
            f"Output only the new sentence.")


def crossover_prompt(a: str, b: str) -> str:
    return (f"Combine these two sentences into ONE natural sentence (at most 12 words, all words "
            f"different) with as many words as possible starting with '{T}'. "
            f"A: \"{a}\"  B: \"{b}\". Output only the sentence.")


async def gen_batch(jc: JimmyClient, prompts: list[str]) -> list[str]:
    rs = await jc.map_prompts(prompts, system_prompt=SYS, top_k=8)
    return [r.content if r.ok else "" for r in rs]


def pop_metrics(pop: list[str]) -> dict:
    fits = [fitness(s) for s in pop]
    return {
        "best": max(fits),
        "mean": round(statistics.mean(fits), 2),
        "distinct_rate": round(distinct_rate([norm(s) for s in pop]), 3),
    }


async def seed_pop(jc: JimmyClient) -> list[str]:
    return await gen_batch(jc, [SEED_PROMPT] * P)


async def run_arm(jc: JimmyClient, arm: str, rng: random.Random) -> dict:
    pop = await seed_pop(jc)
    history = [pop_metrics(pop)]
    valid_rates = []
    for _ in range(G):
        # --- generacja potomstwa (dokladnie P requestow) ---
        if arm == "C":
            # czyste iterowane przepisywanie 1:1, bez selekcji
            prompts = [mutation_prompt(s) for s in pop]
        else:
            # A/B: wybor rodzicow do rozmnazania
            if arm == "A":
                ranked = sorted(pop, key=fitness, reverse=True)
                parents = ranked[: max(2, P // 2)]
            else:  # B: rodzice losowi
                parents = list(pop)
            # ile swiezych seedow (tylko A, gdy roznorodnosc spada) — LICZONE W BUDZECIE P
            n_fresh = 0
            if arm == "A" and pop_metrics(pop)["distinct_rate"] < 0.6:
                n_fresh = 4
            prompts = [SEED_PROMPT] * n_fresh
            while len(prompts) < P:
                if rng.random() < 0.5 and len(parents) >= 2:
                    a, b = rng.sample(parents, 2)
                    prompts.append(crossover_prompt(a, b))
                else:
                    prompts.append(mutation_prompt(rng.choice(parents)))
        offspring = await gen_batch(jc, prompts)
        valid_rates.append(round(sum(structural_valid(o) for o in offspring) / P, 3))

        # --- przezywalnosc ---
        if arm == "A":
            combined = pop + offspring
            seen, uniq = set(), []
            for s in sorted(combined, key=fitness, reverse=True):
                k = norm(s)
                if k not in seen:
                    seen.add(k)
                    uniq.append(s)
            pop = uniq[:P]
            while len(pop) < P:  # dopelnij gdyby dedup zredukowal ponizej P
                pop.append(rng.choice(uniq) if uniq else "")
        elif arm == "B":
            combined = pop + offspring
            pop = rng.sample(combined, P)
        else:  # C
            pop = offspring
        history.append(pop_metrics(pop))

    champions = sorted(set(pop), key=fitness, reverse=True)[:5]
    return {"history": history, "valid_rates": valid_rates,
            "final_best": max(fitness(s) for s in pop),
            "champions": [(s, fitness(s)) for s in champions]}


async def run_control(jc: JimmyClient) -> dict:
    budget = P + G * P  # rowny budzet jak jedno ramie
    rs = await jc.sample_n(CONTROL_PROMPT, budget, system_prompt=SYS, top_k=8)
    cands = [r.content for r in rs if r.ok]
    fits = [(fitness(c), c) for c in cands]
    fits.sort(key=lambda x: x[0], reverse=True)
    return {"budget": budget, "best": fits[0][0], "best_text": fits[0][1],
            "top5": [(f, c) for f, c in fits[:5]]}


async def main():
    rng = random.Random(42)
    out = {}
    async with JimmyClient(max_concurrency=8) as jc:
        for arm in ("A", "B", "C"):
            print(f"\n=== RAMIĘ {arm} ===")
            res = await run_arm(jc, arm, rng)
            out[arm] = res
            curve = [h["best"] for h in res["history"]]
            dist = [h["distinct_rate"] for h in res["history"]]
            print(f"  best-fitness/gen: {curve}")
            print(f"  distinct_rate/gen: {dist}")
            print(f"  final_best={res['final_best']}  valid_rates={res['valid_rates']}")
        print("\n=== KONTROLA D (best-of-N, równy budżet) ===")
        out["D"] = await run_control(jc)
        print(f"  best={out['D']['best']}  text={out['D']['best_text']!r}")
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")

    (HERE / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    # --- werdykt wg pre-rejestrowanych progow ---
    A, B, C, D = out["A"]["final_best"], out["B"]["final_best"], out["C"]["final_best"], out["D"]["best"]
    A_dist_min = min(h["distinct_rate"] for h in out["A"]["history"])
    C_dist_end = out["C"]["history"][-1]["distinct_rate"]
    emergence = (A >= D + 2) and (A >= 1.25 * D)
    selection_matters = A > B
    anticollapse = (C_dist_end < 0.3) and (A_dist_min >= 0.6)
    print("\n===== WERDYKT (progi pre-rejestrowane) =====")
    print(f"  A_best={A} B_best={B} C_best={C} D_best(control)={D}")
    print(f"  1. Emergencja (A>=D+2 i A>=1.25D): {emergence}")
    print(f"  2. Selekcja ma znaczenie (A>B): {selection_matters}")
    print(f"  3. Anti-collapse (C_dist_end<0.3={C_dist_end}, A_dist_min>=0.6={A_dist_min}): {anticollapse}")
    print(f"\n  CHAMPIONI A (top-5): ")
    for s, f in out["A"]["champions"]:
        print(f"    [{f}] {s!r}")
    summary = {"A_best": A, "B_best": B, "C_best": C, "D_best": D,
               "A_distinct_min": A_dist_min, "C_distinct_end": C_dist_end,
               "emergence": emergence, "selection_matters": selection_matters,
               "anticollapse": anticollapse, "champions_A": out["A"]["champions"]}
    (HERE / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

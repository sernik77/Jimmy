"""Bootstrap krzywej accuracy@vote-k z zapisanych 31 probek/zadanie (bez nowych requestow).

Dla kazdego k losujemy (B razy) podzbior k probek z zadania, glosujemy, liczymy accuracy.
Usredniamy po B losowaniach -> gladka, uczciwa krzywa + odchylenie.
"""
from __future__ import annotations

import json
import random
import statistics
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
B = 300  # losowania bootstrap
K_POINTS = [1, 3, 5, 7, 11, 15, 21, 31]


def gold_match(pred, gold) -> bool:
    if pred is None:
        return False
    try:
        return abs(float(pred) - float(gold)) < 1e-6
    except (TypeError, ValueError):
        return False


def vote(sub: list):
    sub = [a for a in sub if a is not None]
    if not sub:
        return None
    return Counter(sub).most_common(1)[0][0]


def main():
    tasks = [json.loads(l) for l in (HERE / "results.jsonl").open()]
    rng = random.Random(1)
    curve = {}
    for k in K_POINTS:
        accs = []
        for _ in range(B):
            hits = 0
            for t in tasks:
                ans = [a for a in t["answers"] if a is not None]
                if not ans:
                    continue
                # losowanie ZE ZWRACANIEM: kazde k to prawdziwy estymator bootstrap
                # (bez tego k=31 zwracaloby cala liste -> std=0, artefakt)
                sub = rng.choices(ans, k=k)
                if gold_match(vote(sub), t["gold"]):
                    hits += 1
            accs.append(100 * hits / len(tasks))
        curve[k] = {"mean": round(statistics.mean(accs), 1),
                    "std": round(statistics.pstdev(accs), 1)}

    # per-zadanie: ktore sa "beznadziejne" (nawet vote nie ratuje)
    hard = []
    for t in tasks:
        maj = vote(t["answers"])
        if not gold_match(maj, t["gold"]):
            c = Counter(a for a in t["answers"] if a is not None)
            hard.append({"gold": t["gold"], "majority": maj,
                         "top3": c.most_common(3), "q": t["q"][:60]})

    out = {"bootstrap_B": B, "curve_accuracy_at_vote_k": curve,
           "n_tasks": len(tasks), "tasks_where_vote_fails": hard}
    (HERE / "bootstrap.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print("accuracy@vote-k (bootstrap, mean±std):")
    for k in K_POINTS:
        print(f"  k={k:2}: {curve[k]['mean']:5.1f}% ± {curve[k]['std']:.1f}")
    print(f"\nzadania gdzie glosowanie zawodzi ({len(hard)}/{len(tasks)}):")
    for h in hard:
        print(f"  gold={h['gold']} maj={h['majority']} top3={h['top3']} :: {h['q']}")


if __name__ == "__main__":
    main()

"""Analiza 003: krzywa pokrycia vs N (bootstrap) + dominacja modow + redukcja w czesci B."""
from __future__ import annotations

import json
import random
import statistics
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
import re


def norm_word(s: str) -> str:
    return re.sub(r"[^a-z\s]", "", s.strip().lower())


def main():
    data = json.loads((HERE / "results.json").read_text())
    rng = random.Random(0)
    out = {}

    # --- Czesc A: coverage vs N (bootstrap ze zwracaniem z puli matched) ---
    print("== CZESC A: coverage vs N ==")
    a_out = {}
    for key, d in data["part_a"].items():
        matched = d["matched"]
        canon = d["canon"]
        curve = {}
        for N in (1, 2, 5, 10, 20, 40):
            covs = []
            for _ in range(300):
                sub = rng.choices(matched, k=N)
                covs.append(len(set(sub)))
            curve[N] = round(statistics.mean(covs), 2)
        top = Counter(matched).most_common(5)
        a_out[key] = {"coverage_vs_N": curve, "canon": canon,
                      "total_unique": len(set(matched)),
                      "pct_space_at_N40": round(100 * curve[40] / canon, 1),
                      "lift_N40_vs_N1": round(curve[40] / curve[1], 2),
                      "top5_modes": top}
        print(f"  {key}: coverage {curve}  | unikalnych={len(set(matched))}/{canon} "
              f"({a_out[key]['pct_space_at_N40']}% @N40)")
        print(f"    dominujace mody: {top}")
    out["part_a"] = a_out

    # --- Czesc B: redukcja best-of-N vs mean single ---
    print("\n== CZESC B: redukcja objektywu ==")
    reductions = []
    all_valid = True
    for t in data["part_b"]:
        if t["best_of_n_len"] and t["mean_single_len"]:
            red = 100 * (t["mean_single_len"] - t["best_of_n_len"]) / t["mean_single_len"]
            reductions.append(red)
        if t["n_valid"] == 0:
            all_valid = False
    b_out = {
        "mean_reduction_pct": round(statistics.mean(reductions), 1),
        "per_task_reduction_pct": [round(r, 1) for r in reductions],
        "all_tasks_have_valid": all_valid,
        "min_valid_count": min(t["n_valid"] for t in data["part_b"]),
    }
    out["part_b"] = b_out
    print(f"  srednia redukcja best-of-20 vs mean-single: {b_out['mean_reduction_pct']}%")
    print(f"  wszystkie zadania maja walidny kandydat: {all_valid} "
          f"(min walidnych={b_out['min_valid_count']})")

    (HERE / "analysis.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

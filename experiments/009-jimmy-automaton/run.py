"""009 — Jimmy jako reguła przejścia automatu komórkowego. Ramiona REAL vs CTRL(losowi sąsiedzi).

Uruchom: python3 experiments/009-jimmy-automaton/run.py
"""
from __future__ import annotations

import asyncio
import json
import math
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402

HERE = Path(__file__).parent
R, C = 6, 6
STEPS = 25
SYS = ("You are a single cell in a word automaton. Given your neighbors' words, output ONE single "
       "English word (lowercase, no punctuation) that best represents their shared theme or blend. "
       "Output only that one word.")

SEED_NOUNS = [
    "river", "mountain", "engine", "whisper", "garden", "thunder", "planet", "market",
    "candle", "ocean", "mirror", "forest", "bread", "letter", "orange", "clock",
    "shadow", "spoon", "ticket", "pillow", "button", "velvet", "copper", "signal",
    "harbor", "meadow", "furnace", "lantern", "compass", "glacier", "orchard", "temple",
    "circuit", "feather", "marble", "nebula",
]


def extract_word(text: str) -> str | None:
    m = re.search(r"[a-zA-Z]+", text)
    return m.group(0).lower() if m else None


def char3(w: str) -> set:
    w = f"  {w} "
    return {w[i:i+3] for i in range(len(w) - 2)}


def jaccard(a: str, b: str) -> float:
    A, B = char3(a), char3(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def entropy(grid: list[list[str]]) -> float:
    words = [w for row in grid for w in row]
    n = len(words)
    c = Counter(words)
    return round(-sum((k / n) * math.log2(k / n) for k in c.values()), 3)


def neighbors_real(grid, i, j):
    return [grid[(i-1) % R][j], grid[(i+1) % R][j],
            grid[i][(j-1) % C], grid[i][(j+1) % C]]


def spatial_correlation(grid, rng) -> dict:
    # pary sasiednie (poziome+pionowe na torusie)
    nb = []
    for i in range(R):
        for j in range(C):
            nb.append(jaccard(grid[i][j], grid[i][(j+1) % C]))
            nb.append(jaccard(grid[i][j], grid[(i+1) % R][j]))
    # pary losowe
    flat = [grid[i][j] for i in range(R) for j in range(C)]
    rnd = [jaccard(*rng.sample(flat, 2)) for _ in range(len(nb))]
    ns = sum(nb) / len(nb)
    rs = sum(rnd) / len(rnd)
    return {"neighbor_sim": round(ns, 4), "random_sim": round(rs, 4),
            "delta": round(ns - rs, 4)}


async def run_arm(jc, arm, rng):
    seeds = rng.sample(SEED_NOUNS, R * C)
    grid = [[seeds[i * C + j] for j in range(C)] for i in range(R)]
    history = []
    for step in range(STEPS):
        # zbuduj prompty
        coords = [(i, j) for i in range(R) for j in range(C)]
        prompts = []
        for (i, j) in coords:
            if arm == "REAL":
                nbrs = neighbors_real(grid, i, j)
            else:  # CTRL: 4 losowe komorki
                flat = [grid[a][b] for a in range(R) for b in range(C)]
                nbrs = rng.sample(flat, 4)
            prompts.append(f"Your neighbors' words: {', '.join(nbrs)}.")
        rs = await jc.map_prompts(prompts, system_prompt=SYS, top_k=8)
        # zastosuj
        new_grid = [row[:] for row in grid]
        changed = 0
        parse_fail = 0
        for idx, (i, j) in enumerate(coords):
            w = extract_word(rs[idx].content) if rs[idx].ok else None
            if w is None:
                parse_fail += 1
                continue  # zachowaj poprzedni
            if w != grid[i][j]:
                changed += 1
            new_grid[i][j] = w
        grid = new_grid
        sc = spatial_correlation(grid, rng)
        history.append({"step": step, "activity": round(changed / (R * C), 3),
                        "entropy": entropy(grid), "parse_fail": round(parse_fail / (R * C), 3),
                        **sc, "grid_hash": hash(tuple(tuple(r) for r in grid))})
    # detekcja cyklu
    hashes = [h["grid_hash"] for h in history]
    cycle = len(hashes) != len(set(hashes))
    return {"history": [{k: v for k, v in h.items() if k != "grid_hash"} for h in history],
            "cycle_detected": cycle, "final_grid": grid}


async def main():
    rng = random.Random(7)
    out = {}
    async with JimmyClient(max_concurrency=8) as jc:
        for arm in ("REAL", "CTRL"):
            print(f"\n=== RAMIĘ {arm} ===")
            res = await run_arm(jc, arm, rng)
            out[arm] = res
            for h in res["history"][::5]:
                print(f"  step {h['step']:2}: activity={h['activity']:.2f} entropy={h['entropy']:.2f} "
                      f"Δsim={h['delta']:+.3f} (nb={h['neighbor_sim']:.3f} rnd={h['random_sim']:.3f}) "
                      f"pf={h['parse_fail']:.2f}")
            print(f"  cykl wykryty: {res['cycle_detected']}")
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")

    # metryki 2. polowy
    def second_half_delta(arm):
        h = out[arm]["history"]
        sh = h[len(h)//2:]
        return round(sum(x["delta"] for x in sh) / len(sh), 4)
    def second_half(arm, key):
        h = out[arm]["history"]; sh = h[len(h)//2:]
        return round(sum(x[key] for x in sh) / len(sh), 3)

    real_delta = second_half_delta("REAL")
    ctrl_delta = second_half_delta("CTRL")
    real_valid = 1 - second_half("REAL", "parse_fail")
    struct = real_delta >= 0.10 and real_delta > ctrl_delta + 0.05
    activity_ok = 0.1 <= second_half("REAL", "activity") <= 0.9
    summary = {
        "REAL_delta_2ndhalf": real_delta, "CTRL_delta_2ndhalf": ctrl_delta,
        "REAL_activity_2ndhalf": second_half("REAL", "activity"),
        "REAL_entropy_2ndhalf": second_half("REAL", "entropy"),
        "REAL_valid_rate_2ndhalf": round(real_valid, 3),
        "REAL_cycle": out["REAL"]["cycle_detected"],
        "structure_emerged": struct, "activity_healthy": activity_ok,
        "final_grid_REAL": out["REAL"]["final_grid"],
    }
    (HERE / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    (HERE / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\n===== WERDYKT =====")
    print(f"  Δsim REAL(2.poł)={real_delta:+.3f}  vs CTRL={ctrl_delta:+.3f}")
    print(f"  struktura wyłoniła się (Δ≥0.10 i > CTRL+0.05): {struct}")
    print(f"  activity zdrowe (0.1-0.9): {activity_ok} ({summary['REAL_activity_2ndhalf']}), "
          f"walidność={real_valid:.2f}")
    print(f"  FINALNA SIATKA REAL:")
    for row in out["REAL"]["final_grid"]:
        print("    " + " ".join(f"{w:>10}" for w in row))


if __name__ == "__main__":
    asyncio.run(main())

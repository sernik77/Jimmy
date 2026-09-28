"""009b — reguła KONSENSUSU (model wyborcy/Ising): komórka WYBIERA słowo spośród sąsiadów
najlepiej pasujące do większości, zamiast wymyślać nowe. Predykcja: koalescencja domen (Δsim>0).

Uruchom: python3 experiments/009-jimmy-automaton/run_b.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).parent))
from jimmy.client import JimmyClient  # noqa: E402
import run as base  # reuzyj R,C,STEPS,extract_word,jaccard,entropy,neighbors_real,spatial_correlation  # noqa: E402

SYS_CONSENSUS = (
    "You are a cell in a word automaton. You will see your neighbors' words. Output EXACTLY ONE of "
    "THOSE neighbor words — the one that best fits the shared theme of the majority of them. "
    "Do not invent new words. Output only that single chosen word, lowercase."
)


async def run_arm(jc, arm, rng):
    seeds = rng.sample(base.SEED_NOUNS, base.R * base.C)
    grid = [[seeds[i * base.C + j] for j in range(base.C)] for i in range(base.R)]
    history = []
    for step in range(base.STEPS):
        coords = [(i, j) for i in range(base.R) for j in range(base.C)]
        prompts = []
        for (i, j) in coords:
            if arm == "REAL":
                nbrs = base.neighbors_real(grid, i, j)
            else:
                flat = [grid[a][b] for a in range(base.R) for b in range(base.C)]
                nbrs = rng.sample(flat, 4)
            prompts.append(f"Your neighbors' words: {', '.join(nbrs)}. Choose one of these.")
        rs = await jc.map_prompts(prompts, system_prompt=SYS_CONSENSUS, top_k=8)
        new_grid = [row[:] for row in grid]
        changed = parse_fail = off_menu = 0
        for idx, (i, j) in enumerate(coords):
            w = base.extract_word(rs[idx].content) if rs[idx].ok else None
            if w is None:
                parse_fail += 1
                continue
            # czy wybral z menu sasiadow? (miara przestrzegania reguly)
            nb_set = set(base.neighbors_real(grid, i, j)) if arm == "REAL" else None
            if arm == "REAL" and w not in nb_set:
                off_menu += 1
            if w != grid[i][j]:
                changed += 1
            new_grid[i][j] = w
        grid = new_grid
        sc = base.spatial_correlation(grid, rng)
        history.append({"step": step, "activity": round(changed / (base.R*base.C), 3),
                        "entropy": base.entropy(grid), "parse_fail": round(parse_fail/(base.R*base.C), 3),
                        "off_menu": round(off_menu/(base.R*base.C), 3), **sc,
                        "grid_hash": hash(tuple(tuple(r) for r in grid))})
    hashes = [h["grid_hash"] for h in history]
    return {"history": [{k: v for k, v in h.items() if k != "grid_hash"} for h in history],
            "cycle_detected": len(hashes) != len(set(hashes)), "final_grid": grid,
            "n_final_distinct": len(set(w for row in grid for w in row))}


async def main():
    import random
    rng = random.Random(7)
    out = {}
    async with JimmyClient(max_concurrency=8) as jc:
        for arm in ("REAL", "CTRL"):
            print(f"\n=== 009b RAMIĘ {arm} (konsensus) ===")
            res = await run_arm(jc, arm, rng)
            out[arm] = res
            for h in res["history"][::5]:
                print(f"  step {h['step']:2}: act={h['activity']:.2f} ent={h['entropy']:.2f} "
                      f"Δsim={h['delta']:+.3f} pf={h['parse_fail']:.2f} offmenu={h.get('off_menu',0):.2f}")
            print(f"  cykl={res['cycle_detected']} finalnych_slow={res['n_final_distinct']}")
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")

    def sh(arm, key):
        h = out[arm]["history"]; s = h[len(h)//2:]
        return round(sum(x[key] for x in s)/len(s), 4)
    real_d, ctrl_d = sh("REAL", "delta"), sh("CTRL", "delta")
    struct = real_d >= 0.10 and real_d > ctrl_d + 0.05
    summary = {"REAL_delta_2ndhalf": real_d, "CTRL_delta_2ndhalf": ctrl_d,
               "REAL_activity_2ndhalf": sh("REAL", "activity"),
               "REAL_entropy_2ndhalf": sh("REAL", "entropy"),
               "REAL_offmenu_2ndhalf": sh("REAL", "off_menu"),
               "structure_emerged": struct, "REAL_cycle": out["REAL"]["cycle_detected"],
               "final_grid_REAL": out["REAL"]["final_grid"],
               "n_final_distinct_REAL": out["REAL"]["n_final_distinct"]}
    (Path(__file__).parent / "results_b.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    (Path(__file__).parent / "summary_b.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\n===== WERDYKT 009b =====")
    print(f"  Δsim REAL={real_d:+.3f} vs CTRL={ctrl_d:+.3f} | struktura: {struct}")
    print(f"  finalnych słów={summary['n_final_distinct_REAL']} entropy={summary['REAL_entropy_2ndhalf']} "
          f"offmenu={summary['REAL_offmenu_2ndhalf']:.2f}")
    print("  FINALNA SIATKA REAL:")
    for row in out["REAL"]["final_grid"]:
        print("    " + " ".join(f"{w:>10}" for w in row))


if __name__ == "__main__":
    asyncio.run(main())

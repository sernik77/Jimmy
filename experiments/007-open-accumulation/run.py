"""007 — otwarta akumulacja z miękkim checkerem nowości. Metryka: acceptance-rate w czasie.

Uruchom: python3 experiments/007-open-accumulation/run.py
"""
from __future__ import annotations

import asyncio
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402

HERE = Path(__file__).parent
ROUNDS = 20
K = 16
WINDOW = 25
NOVELTY_THRESH = 0.5   # odrzuć jeśli max Jaccard char-3gram nazwy >= to

SYS = ("You invent fictional creatures. Output EXACTLY one line: 'Name: trait' where Name is a single "
       "invented word (a creature name) and trait is a 3-6 word description. Output only that line.")


def parse_item(text: str):
    line = text.strip().splitlines()[0] if text.strip() else ""
    if ":" in line:
        name, trait = line.split(":", 1)
    else:
        name, trait = line, ""
    name = re.sub(r"[^a-zA-Z]", "", name).lower()
    return (name, trait.strip()) if len(name) >= 3 else (None, None)


def char3(w: str) -> set:
    w = f"  {w} "
    return {w[i:i+3] for i in range(len(w)-2)}


def jaccard(a: str, b: str) -> float:
    A, B = char3(a), char3(b)
    return len(A & B) / len(A | B) if A and B else 0.0


def max_sim(name: str, names: list[str]) -> tuple[float, str]:
    best, arg = 0.0, ""
    for n in names:
        s = jaccard(name, n)
        if s > best:
            best, arg = s, n
    return best, arg


def content_words(trait: str) -> list[str]:
    stop = {"a", "an", "the", "of", "with", "that", "and", "is", "it", "its", "very", "in", "to", "for"}
    return [w for w in re.findall(r"[a-z]+", trait.lower()) if w not in stop and len(w) > 2]


async def main():
    rng = random.Random(3)
    accepted_names: list[str] = []
    accepted_items: list[tuple[str, str]] = []
    per_round = []
    async with JimmyClient(max_concurrency=8) as jc:
        for r in range(ROUNDS):
            window = rng.sample(accepted_names, min(len(accepted_names), WINDOW)) if accepted_names else []
            avoid = ", ".join(window)
            prompt = (f"Invent a brand-new creature UNLIKE these existing ones: [{avoid}]. "
                      f"Make the name sound different from all of them.")
            rs = await jc.map_prompts([prompt] * K, system_prompt=SYS, top_k=8)
            acc = dup_in = dup_out = malformed = 0
            window_set = set(window)
            for resp in rs:
                if not resp.ok:
                    malformed += 1; continue
                name, trait = parse_item(resp.content)
                if name is None:
                    malformed += 1; continue
                sim, arg = max_sim(name, accepted_names)
                if sim >= NOVELTY_THRESH or name in accepted_names:
                    # odrzucone jako nienowe — rozbij czy zrodlo bylo w oknie
                    if arg in window_set or name in window_set:
                        dup_in += 1
                    else:
                        dup_out += 1
                    continue
                accepted_names.append(name)
                accepted_items.append((name, trait))
                acc += 1
            per_round.append({"round": r, "accept_rate": round(acc / K, 3),
                              "dup_in_window": dup_in, "dup_out_window": dup_out,
                              "malformed": malformed, "total_unique": len(accepted_names)})
            print(f"  r{r:2}: accept={acc}/{K} ({acc/K:.2f})  dup_in={dup_in} dup_out={dup_out} "
                  f"malformed={malformed}  |Σ|={len(accepted_names)}")
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")

    # metryki
    last_third = per_round[-(ROUNDS // 3):]
    acc_last = round(sum(p["accept_rate"] for p in last_third) / len(last_third), 3)
    acc_first = round(sum(p["accept_rate"] for p in per_round[:ROUNDS // 3]) / (ROUNDS // 3), 3)
    # roznorodnosc opisow (os niezalezna od bramki): odsetek unikalnych slow-tresci / wszystkie
    all_cw = [w for _, t in accepted_items for w in content_words(t)]
    desc_diversity = round(len(set(all_cw)) / max(len(all_cw), 1), 3)
    cw_top = Counter(all_cw).most_common(8)
    open_ended = acc_last >= 0.5

    summary = {
        "accept_rate_first_third": acc_first, "accept_rate_last_third": acc_last,
        "total_unique": len(accepted_names),
        "desc_content_diversity": desc_diversity,
        "desc_top_words": cw_top,
        "open_ended": open_ended,
        "dup_in_total": sum(p["dup_in_window"] for p in per_round),
        "dup_out_total": sum(p["dup_out_window"] for p in per_round),
        "sample_20_items": accepted_items[:20],
    }
    (HERE / "results.json").write_text(json.dumps({"per_round": per_round, "items": accepted_items},
                                                  ensure_ascii=False, indent=2))
    (HERE / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\n===== WERDYKT 007 =====")
    print(f"  accept-rate: pierwsza 1/3={acc_first}  ostatnia 1/3={acc_last}")
    print(f"  OTWARTE (last≥0.5): {open_ended}")
    print(f"  odrzucenia: dup-w-oknie={summary['dup_in_total']} dup-poza-oknem={summary['dup_out_total']}")
    print(f"  różnorodność opisów (oś niezależna): {desc_diversity}  top={cw_top[:5]}")
    print(f"  |Σ| unikalnych stworzeń: {len(accepted_names)}")
    print("  PRÓBKA 18 stworzeń:")
    for name, trait in accepted_items[:18]:
        print(f"    {name}: {trait}")


if __name__ == "__main__":
    asyncio.run(main())

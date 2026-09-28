"""008 — agenci asymetryczni: Generator vs Krytyk, forma z UKRYTYM scorerem.

Krytyk dostaje tylko jakościowe wskazówki ("żywiej/konkretniej"); punktuję UKRYTĄ funkcją
konkretności, o której krytyk nie wie. Test: czy pętla krytyka bije best-of-N o równym budżecie?
Prawa (1: krytyk dzieli bias generatora; 3: pętla nie bije próbkowania na optymalizacji) przewidują
null — raportuję wynik niezależnie.

Prog KEEP: REFINE-final bije SAMPLE-best o >= +10% średniego ukrytego score. Budżet równy (req).
Uruchom: python3 experiments/008-asymmetric-critic/run.py
"""
from __future__ import annotations

import asyncio
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402

HERE = Path(__file__).parent
CYCLES = 3  # gen + 3×(krytyka+rewizja) = 7 requestow/element
BUDGET = 1 + CYCLES * 2  # = 7; kontrola dostaje tyle single-shotow

GEN_SYS = "You write vivid two-sentence micro-stories. Output only the story."
CRITIC_SYS = ("You are a demanding writing critic. In ONE sentence, say the single most important way "
              "to make the story more vivid and concrete. Be specific. Output only the critique.")
REVISE_SYS = "You revise a two-sentence micro-story following the critique. Output only the revised story."

SUBJECTS = [
    "a lighthouse in a storm", "an abandoned train station", "the last tree in a desert",
    "a clockmaker's workshop", "a whale surfacing at dawn", "a city street after rain",
    "a beekeeper at dusk", "a shipwreck on the seabed", "a market at midnight",
    "a glacier calving", "a violinist on a rooftop", "a lantern in a mine",
    "a fox in the snow", "a greenhouse in winter", "a diver in a kelp forest",
    "a blacksmith's forge",
]

# --- UKRYTY scorer (krytyk NIE wie o nim) ---
CONCRETE = {
    "salt", "cold", "beam", "fog", "creak", "rust", "wave", "glow", "iron", "wet", "stone",
    "smoke", "ash", "amber", "frost", "spark", "brine", "moss", "grit", "shard", "ember",
    "chill", "damp", "copper", "tar", "wind", "dust", "rain", "snow", "bark", "wax", "steel",
    "flame", "shadow", "silver", "green", "cracked", "hollow", "gleam", "thunder", "petal",
    "feather", "claw", "scale", "ripple", "echo", "hum", "drip", "shiver", "bloom",
}
VAGUE = {"very", "really", "thing", "things", "nice", "good", "bad", "stuff", "somehow", "just",
         "beautiful", "amazing", "great", "interesting"}


def hidden_score(text: str) -> float:
    words = re.findall(r"[a-z]+", text.lower())
    if not words:
        return 0.0
    concrete_hits = len({w for w in words if w in CONCRETE})
    vague_hits = sum(1 for w in words if w in VAGUE)
    bigrams = list(zip(words, words[1:]))
    bigram_div = len(set(bigrams)) / len(bigrams) if bigrams else 0
    return round(concrete_hits + 2 * bigram_div - vague_hits, 3)


async def refine_item(jc, subject):
    story = (await jc.ask(f"Write a two-sentence micro-story about {subject}.",
                          system_prompt=GEN_SYS, top_k=8)).content
    gen0 = story
    for _ in range(CYCLES):
        crit = (await jc.ask(f"Critique this story:\n{story}", system_prompt=CRITIC_SYS, top_k=8)).content
        story = (await jc.ask(f"Story:\n{story}\n\nCritique:\n{crit}\n\nRevise the story.",
                              system_prompt=REVISE_SYS, top_k=8)).content
    return hidden_score(gen0), hidden_score(story)


async def sample_item(jc, subject):
    rs = await jc.sample_n(f"Write a two-sentence micro-story about {subject}.",
                           BUDGET, system_prompt=GEN_SYS, top_k=8)
    return max(hidden_score(r.content) for r in rs if r.ok)


async def main():
    out = []
    async with JimmyClient(max_concurrency=8) as jc:
        # rownolegle po elementach
        refine = await asyncio.gather(*[refine_item(jc, s) for s in SUBJECTS])
        sample = await asyncio.gather(*[sample_item(jc, s) for s in SUBJECTS])
        for subj, (g0, gf), sb in zip(SUBJECTS, refine, sample):
            out.append({"subject": subj, "refine_gen0": g0, "refine_final": gf, "sample_best": sb})
            print(f"  {subj[:28]:28} gen0={g0:5.2f} refine_final={gf:5.2f} sample_best={sb:5.2f}")
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")

    mean_gen0 = statistics.mean(o["refine_gen0"] for o in out)
    mean_final = statistics.mean(o["refine_final"] for o in out)
    mean_sample = statistics.mean(o["sample_best"] for o in out)
    refine_helps = mean_final > mean_gen0
    beats_sampling = mean_final >= 1.10 * mean_sample
    summary = {"mean_refine_gen0": round(mean_gen0, 3), "mean_refine_final": round(mean_final, 3),
               "mean_sample_best": round(mean_sample, 3),
               "refine_improves_over_gen0": refine_helps,
               "refine_beats_equal_budget_sampling": beats_sampling,
               "budget_per_item": BUDGET}
    (HERE / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    (HERE / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\n===== WERDYKT 008 =====")
    print(f"  refine: gen0={mean_gen0:.2f} → final={mean_final:.2f} (poprawa nad gen0: {refine_helps})")
    print(f"  best-of-N (równy budżet {BUDGET}): {mean_sample:.2f}")
    print(f"  KRYTYK bije próbkowanie (≥+10%): {beats_sampling}")


if __name__ == "__main__":
    asyncio.run(main())

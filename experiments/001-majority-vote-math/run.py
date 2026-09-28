"""001 — self-consistency / glosowanie wiekszosciowe na zadaniach matematycznych.

Uruchom: python3 experiments/001-majority-vote-math/run.py
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
K_MAX = 31
K_POINTS = [1, 3, 7, 15, 31]

SYS = (
    "You are a careful math solver. Think step by step in at most 3 short lines, "
    "then output the final numeric answer on its own last line in EXACTLY this format: "
    "FINAL: <number>. Output only digits after FINAL:, no units, no words."
)

# (pytanie, gold jako liczba). Umiarkowanie trudne — 8B nie jest tu pewny.
DATASET = [
    ("A shop sells pens at 3 for $2. How many dollars for 27 pens?", 18),
    ("Tom has 5 boxes with 12 apples each. He gives away 18 apples. How many left?", 42),
    ("A train travels 60 km in 45 minutes. How many km in 3 hours at the same speed?", 240),
    ("If 7x + 5 = 54, what is x?", 7),
    ("A rectangle is 8 by 5. A second rectangle has double the area. What is its area?", 80),
    ("Sarah is 4 times as old as Ben. In 6 years she will be twice his age. How old is Ben now?", 3),
    ("A jar has 3 red, 5 blue, 2 green marbles. How many marbles total if we triple the blue?", 20),
    ("You buy 3 shirts at $15 and 2 hats at $8. You pay with $100. What is the change?", 39),
    ("A number increased by 40% equals 70. What is the number?", 50),
    ("There are 24 students. 1/3 play chess, 1/4 play tennis. How many play neither, if none play both?", 10),
    ("A car uses 6 liters per 100 km. How many liters for a 350 km trip?", 21),
    ("The sum of three consecutive integers is 72. What is the largest?", 25),
    ("A pizza is cut into 8 slices. 3 people eat 2 slices each. How many slices remain?", 2),
    ("If a book costs $12 after a 25% discount, what was the original price in dollars?", 16),
    ("A tank fills at 4 liters/min and drains at 1.5 liters/min. Net liters after 10 minutes?", 25),
    ("Lisa runs 3 laps of a 400 m track daily for 5 days. Total kilometers?", 6),
    ("A recipe needs 2 eggs per 3 pancakes. How many eggs for 18 pancakes?", 12),
    ("What is 15% of 15% of 4000?", 90),
    ("A ladder has 20 rungs 25 cm apart. Distance from first to last rung in meters?", 4.75),
    ("Three friends split a $90 bill. One pays double each of the others. What does the big payer pay?", 45),
    ("A clock shows 3:00. What is the angle in degrees between the hands?", 90),
    ("If today is Wednesday, what day is it in 100 days? (answer as number 0=Sun..6=Sat)", 5),
    ("A cube has volume 27. What is its total surface area?", 54),
    ("You save $5 the first week and $3 more each week than the week before. Total after 4 weeks?", 38),
]

_NUM_RE = re.compile(r"FINAL:\s*\$?\s*(-?\d+(?:\.\d+)?)", re.IGNORECASE)
_ANY_NUM_RE = re.compile(r"(-?\d+(?:\.\d+)?)")


def extract_answer(text: str):
    m = _NUM_RE.search(text)
    if m:
        return _canon(m.group(1))
    # fallback: ostatnia liczba w tekscie
    nums = _ANY_NUM_RE.findall(text)
    if nums:
        return _canon(nums[-1])
    return None


def _canon(s: str):
    f = float(s)
    return int(f) if f == int(f) else round(f, 4)


def vote_at_k(answers: list, k: int):
    """Wiekszosc z pierwszych k niepustych odpowiedzi."""
    sub = [a for a in answers if a is not None][:k]
    if not sub:
        return None
    return Counter(sub).most_common(1)[0][0]


async def main():
    random.seed(0)
    results = []  # per-zadanie: {q, gold, answers}
    async with JimmyClient(max_concurrency=8) as jc:
        for i, (q, gold) in enumerate(DATASET):
            rs = await jc.sample_n(q, K_MAX, system_prompt=SYS, top_k=8)
            answers = [extract_answer(r.content) for r in rs if r.ok]
            results.append({"idx": i, "q": q, "gold": gold, "answers": answers,
                            "n_ok": len(answers)})
            print(f"[{i+1:2}/{len(DATASET)}] gold={gold} "
                  f"answers_sample={answers[:5]} n={len(answers)}")
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors} "
              f"decode_tokens={jc.total_decode_tokens}")

    # zapis surowych
    with (HERE / "results.jsonl").open("w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # metryki: accuracy@vote-k
    def gold_match(pred, gold):
        if pred is None:
            return False
        return abs(float(pred) - float(gold)) < 1e-6

    acc = {}
    for k in K_POINTS:
        hits = sum(1 for r in results if gold_match(vote_at_k(r["answers"], k), r["gold"]))
        acc[k] = round(100 * hits / len(results), 1)

    # accuracy@1 usredniona po WSZYSTKICH probkach (nie tylko pierwszej) — uczciwszy baseline
    per_sample_hits = 0
    per_sample_tot = 0
    for r in results:
        for a in r["answers"]:
            per_sample_tot += 1
            if gold_match(a, r["gold"]):
                per_sample_hits += 1
    acc_avg_single = round(100 * per_sample_hits / max(per_sample_tot, 1), 1)

    summary = {
        "accuracy_avg_single_sample": acc_avg_single,
        "accuracy_at_vote_k": acc,
        "lift_vote31_vs_single": round(acc[31] - acc_avg_single, 1),
        "n_tasks": len(results),
    }
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print("\n===== SUMMARY =====")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())

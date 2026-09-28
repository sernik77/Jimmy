"""002 — ekstrakcja strukturalna do JSON: best-of-N z twardym walidatorem schematu.

Hipoteza: dla zadania z twardym weryfikatorem (walidacja schematu) best-of-N zamienia
zawodny per-probka JSON w niezawodny pipeline. Mierzymy validity@1 vs validity@best-of-8
oraz field-accuracy (intent) przez glosowanie po WALIDNYCH probkach.

Prog KEEP: validity@best-of-8 >= 95% ORAZ intent-accuracy(glosowanie) >= 80%.

Uruchom: python3 experiments/002-structured-json/run.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402
from jimmy.eval import extract_json  # noqa: E402

HERE = Path(__file__).parent
N = 8  # best-of-N

INTENTS = ["refund", "technical_issue", "shipping", "account", "complaint", "question"]

SYS = (
    "You extract structured data from a customer support message. "
    "Output ONLY a JSON object, no prose, with EXACTLY these keys: "
    '"intent" (one of: refund, technical_issue, shipping, account, complaint, question), '
    '"urgency" (integer 1-5), "product" (string or null), "summary" (string, <=12 words). '
    "Output the JSON object and nothing else."
)

# (wiadomosc, gold_intent). urgency/product nie maja twardego gold — sprawdzamy tylko typ/zakres.
DATASET = [
    ("Hi, my order #4521 never arrived and it's been 3 weeks. Where is my package???", "shipping"),
    ("I want my money back for the blender, it broke after one use.", "refund"),
    ("The app keeps crashing every time I open the settings page on Android.", "technical_issue"),
    ("Can you tell me if the X200 headphones are waterproof?", "question"),
    ("I've been charged twice this month for my subscription. Fix this now.", "account"),
    ("Your customer service was incredibly rude and I am furious about it.", "complaint"),
    ("Reset my password please, I'm locked out of my account.", "account"),
    ("The laptop screen has dead pixels, I'd like a replacement or refund.", "refund"),
    ("When will the new firmware update be released for the router?", "question"),
    ("Package arrived smashed and the contents are ruined. Unacceptable.", "complaint"),
    ("Wifi thermostat won't connect to my network no matter what I try.", "technical_issue"),
    ("I need to change the delivery address on order 9987 before it ships.", "shipping"),
    ("Do you offer student discounts on the annual plan?", "question"),
    ("Charged for premium but features are still locked. Very frustrating.", "account"),
    ("The coffee machine stopped heating water after two days. Want refund.", "refund"),
    ("Tracking says delivered but I never received anything.", "shipping"),
    ("Login button does nothing on Safari, tried clearing cache.", "technical_issue"),
    ("This is the third time I'm writing about the same broken product. Done.", "complaint"),
    ("How do I export my data before deleting my account?", "question"),
    ("My monthly invoice shows a plan I never signed up for.", "account"),
]


def validate(obj) -> bool:
    """Twardy walidator schematu."""
    if not isinstance(obj, dict):
        return False
    if set(obj.keys()) < {"intent", "urgency", "product", "summary"}:
        return False
    if obj.get("intent") not in INTENTS:
        return False
    u = obj.get("urgency")
    if not isinstance(u, int) or not (1 <= u <= 5):
        return False
    p = obj.get("product")
    if not (p is None or isinstance(p, str)):
        return False
    if not isinstance(obj.get("summary"), str):
        return False
    return True


async def main():
    per_input = []
    async with JimmyClient(max_concurrency=8) as jc:
        for i, (msg, gold_intent) in enumerate(DATASET):
            rs = await jc.sample_n(msg, N, system_prompt=SYS, top_k=8)
            parsed = [extract_json(r.content) for r in rs if r.ok]
            valid = [o for o in parsed if validate(o)]
            per_input.append({
                "idx": i, "msg": msg, "gold_intent": gold_intent,
                "n_parsed_json": sum(1 for o in parsed if o is not None),
                "n_valid_schema": len(valid),
                "intents": [o["intent"] for o in valid],
                "sample_valid": valid[0] if valid else None,
            })
            print(f"[{i+1:2}/{len(DATASET)}] valid={len(valid)}/{N} "
                  f"gold={gold_intent} intents={[o['intent'] for o in valid][:5]}")
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")

    with (HERE / "results.jsonl").open("w") as f:
        for r in per_input:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    n = len(per_input)
    # validity per pojedyncza probka (usrednione po wszystkich N*n probkach)
    valid_rate_per_sample = sum(r["n_valid_schema"] for r in per_input) / (n * N)
    # validity@best-of-8: przynajmniej 1 z N walidna
    valid_best_of_n = sum(1 for r in per_input if r["n_valid_schema"] >= 1) / n
    # intent-accuracy przez glosowanie po walidnych
    intent_hits = 0
    for r in per_input:
        if r["intents"]:
            maj = Counter(r["intents"]).most_common(1)[0][0]
            if maj == r["gold_intent"]:
                intent_hits += 1
    intent_acc = intent_hits / n

    summary = {
        "validity_rate_per_single_sample": round(100 * valid_rate_per_sample, 1),
        "validity_best_of_8": round(100 * valid_best_of_n, 1),
        "intent_accuracy_majority_vote": round(100 * intent_acc, 1),
        "n_inputs": n, "N": N,
    }
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print("\n===== SUMMARY =====")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())

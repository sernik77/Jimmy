"""Rozdziel intent-accuracy 002 na podzbior jednoznaczny vs dyskusyjny (offline).

Motyw (advisor): liczba, ktorej mianownik zawiera moje wlasne watpliwe etykiety, nie mierzy
Jimmy'ego. Klasyfikuje kazdy input jako UNAMBIGUOUS/ARGUABLE (osad zakodowany jawnie),
i raportuje trafnosc glosowania osobno.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent

# Osad o jednoznacznosci etykiety (indeksy 0-based wg DATASET w run.py).
# ARGUABLE = kategoria realnie sporna (nakladajace sie taksonomie billing/account/refund,
# damaged-in-transit shipping/complaint, question-o-produkcie vs technical_issue, itd.)
ARGUABLE = {4, 7, 8, 9, 13, 17, 18, 19}
# reszta = UNAMBIGUOUS


def main():
    tasks = [json.loads(l) for l in (HERE / "results.jsonl").open()]

    def majority(intents):
        return Counter(intents).most_common(1)[0][0] if intents else None

    rows = []
    for t in tasks:
        maj = majority(t["intents"])
        rows.append({
            "idx": t["idx"], "gold": t["gold_intent"], "majority": maj,
            "hit": maj == t["gold_intent"],
            "ambiguity": "ARGUABLE" if t["idx"] in ARGUABLE else "UNAMBIGUOUS",
            "msg": t["msg"][:55],
        })

    unamb = [r for r in rows if r["ambiguity"] == "UNAMBIGUOUS"]
    arg = [r for r in rows if r["ambiguity"] == "ARGUABLE"]

    def acc(rs):
        return round(100 * sum(r["hit"] for r in rs) / len(rs), 1) if rs else None

    out = {
        "intent_accuracy_all": acc(rows),
        "intent_accuracy_unambiguous": acc(unamb),
        "n_unambiguous": len(unamb),
        "intent_accuracy_arguable": acc(arg),
        "n_arguable": len(arg),
        "misses_unambiguous": [r for r in unamb if not r["hit"]],
        "misses_arguable": [r for r in arg if not r["hit"]],
    }
    (HERE / "ambiguity.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"intent-accuracy ALL:          {out['intent_accuracy_all']}%  (n={len(rows)})")
    print(f"intent-accuracy UNAMBIGUOUS:  {out['intent_accuracy_unambiguous']}%  (n={len(unamb)})")
    print(f"intent-accuracy ARGUABLE:     {out['intent_accuracy_arguable']}%  (n={len(arg)})")
    print("\nbledy na JEDNOZNACZNYCH (to sa prawdziwe bledy Jimmy'ego):")
    for r in out["misses_unambiguous"]:
        print(f"  gold={r['gold']} maj={r['majority']} :: {r['msg']}")
    print("\nbledy na DYSKUSYJNYCH (czesciowo szum etykiet):")
    for r in out["misses_arguable"]:
        print(f"  gold={r['gold']} maj={r['majority']} :: {r['msg']}")


if __name__ == "__main__":
    main()

"""003 — Jimmy jako generator kandydatow dla madrzejszego konsumenta.

Czesc A: pokrycie przestrzeni (diversity -> coverage), checker = przynaleznosc do zbioru.
Czesc B: zysk z selekcji (best-of-N + deterministyczny scorer vs single-shot).

Uruchom: python3 experiments/003-candidate-generation/run.py
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

# ---------- Zbiory referencyjne (samowystarczalny checker) ----------
EUROPE = {
    "albania", "andorra", "austria", "belarus", "belgium", "bosnia", "bulgaria",
    "croatia", "cyprus", "czechia", "czech republic", "denmark", "estonia", "finland",
    "france", "germany", "greece", "hungary", "iceland", "ireland", "italy", "kosovo",
    "latvia", "liechtenstein", "lithuania", "luxembourg", "malta", "moldova", "monaco",
    "montenegro", "netherlands", "north macedonia", "macedonia", "norway", "poland",
    "portugal", "romania", "russia", "san marino", "serbia", "slovakia", "slovenia",
    "spain", "sweden", "switzerland", "ukraine", "united kingdom", "uk", "england",
    "scotland", "wales", "vatican", "vatican city",
}
# kanoniczne (do liczenia "rozmiaru przestrzeni" bez duplikatow-aliasow)
EUROPE_CANON = 44

US_STATES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut",
    "delaware", "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa",
    "kansas", "kentucky", "louisiana", "maine", "maryland", "massachusetts", "michigan",
    "minnesota", "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york", "north carolina",
    "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania", "rhode island",
    "south carolina", "south dakota", "tennessee", "texas", "utah", "vermont",
    "virginia", "washington", "west virginia", "wisconsin", "wyoming",
}
US_CANON = 50

COVERAGE_TASKS = [
    ("Name one country in Europe. Reply with ONLY the country name, nothing else.",
     EUROPE, EUROPE_CANON, "europe"),
    ("Name one U.S. state. Reply with ONLY the state name, nothing else.",
     US_STATES, US_CANON, "us_states"),
]

# ---------- Czesc B: najkrotsze zdanie z wymaganymi slowami ----------
WORD_TRIPLES = [
    ("cat", "moon", "glass"),
    ("river", "clock", "shadow"),
    ("bread", "engine", "whisper"),
    ("mountain", "letter", "orange"),
    ("garden", "thunder", "spoon"),
    ("candle", "ocean", "ticket"),
    ("mirror", "forest", "button"),
    ("planet", "pillow", "market"),
]


def norm_word(s: str) -> str:
    return re.sub(r"[^a-z\s]", "", s.strip().lower())


def match_member(text: str, refset: set) -> str | None:
    t = norm_word(text)
    # dokladne
    if t in refset:
        return t
    # pierwszy pasujacy token/fraza (Jimmy czasem dodaje slowa)
    for member in refset:
        if re.search(rf"\b{re.escape(member)}\b", t):
            return member
    return None


def sentence_valid_and_len(text: str, required: tuple) -> tuple[bool, int]:
    t = norm_word(text)
    tokens = t.split()
    ok = all(re.search(rf"\b{re.escape(w)}\b", t) for w in required)
    return ok, len(tokens)


async def part_a(jc: JimmyClient):
    print("== CZESC A: pokrycie ==")
    pool = 60
    results = {}
    for prompt, refset, canon, key in COVERAGE_TASKS:
        rs = await jc.sample_n(prompt, pool, system_prompt="", top_k=8)
        raw = [r.content for r in rs if r.ok]
        matched = [m for m in (match_member(x, refset) for x in raw) if m]
        results[key] = {"raw": raw, "matched": matched, "canon": canon,
                        "distinct_rate_raw": round(distinct_rate(raw), 3)}
        print(f"  {key}: {len(matched)}/{len(raw)} walidnych, "
              f"{len(set(matched))} unikalnych z {canon} przestrzeni")
    return results


async def part_b(jc: JimmyClient):
    print("== CZESC B: zysk z selekcji ==")
    N = 20
    SYS = ("Write ONE short natural English sentence. Output only the sentence.")
    per_task = []
    for triple in WORD_TRIPLES:
        prompt = (f"Write the SHORTEST possible natural sentence that contains all of these "
                  f"words: {triple[0]}, {triple[1]}, {triple[2]}.")
        rs = await jc.sample_n(prompt, N, system_prompt=SYS, top_k=8)
        cands = []
        for r in rs:
            if not r.ok:
                continue
            ok, ln = sentence_valid_and_len(r.content, triple)
            cands.append({"text": r.content, "valid": ok, "len": ln})
        valids = [c for c in cands if c["valid"]]
        best = min((c["len"] for c in valids), default=None)
        # single-shot baseline: srednia dlugosc PIERWSZEGO walidnego? uczciwiej: srednia po
        # walidnych probkach (kazda pojedyncza probka to jeden single-shot)
        mean_single = statistics.mean([c["len"] for c in valids]) if valids else None
        per_task.append({"triple": triple, "n_valid": len(valids), "n_total": len(cands),
                         "best_of_n_len": best, "mean_single_len": mean_single,
                         "best_example": min(valids, key=lambda c: c["len"])["text"] if valids else None})
        print(f"  {triple}: valid={len(valids)}/{len(cands)} "
              f"best={best} mean_single={round(mean_single,1) if mean_single else None}")
    return per_task


async def main():
    async with JimmyClient(max_concurrency=8) as jc:
        a = await part_a(jc)
        b = await part_b(jc)
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")
    (HERE / "results.json").write_text(json.dumps({"part_a": a, "part_b": b},
                                                  ensure_ascii=False, indent=2))
    print("saved results.json")


if __name__ == "__main__":
    asyncio.run(main())

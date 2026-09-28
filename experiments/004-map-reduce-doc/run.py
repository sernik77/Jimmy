"""004 — APLIKACJA: map-reduce po długim dokumencie (ekstrakcja rozsianych bytów).

Dokument ~7k tokenów (> limit Jimmy'ego ~6k) z 24 rozsianymi kryptonimami. Gold = 24 kryptonimy.
Porównanie: single-shot na całości vs map-reduce (chunki równolegle -> unia).
Prog KEEP: map-reduce recall >= 0.9 ORAZ bije single-shot o >= 30 pkt proc.

Uruchom: python3 experiments/004-map-reduce-doc/run.py
"""
from __future__ import annotations

import asyncio
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402

HERE = Path(__file__).parent

CODENAMES = [
    "Olribex", "Vandrel", "Quorrin", "Meltavo", "Sperbin", "Tralux", "Yndreth", "Kobbaris",
    "Zephyne", "Hallowix", "Draganor", "Nuvexis", "Palrigo", "Estamund", "Wrenlow", "Ficarel",
    "Braxentu", "Cindrell", "Othaven", "Lumbrix", "Torvanis", "Grishelm", "Avitor", "Pendreck",
]

FILLER = (
    "The committee reviewed quarterly logistics and noted several operational dependencies. "
    "Stakeholders raised concerns about timelines while the budget subgroup deferred final numbers. "
    "Regional teams synchronized their reporting cadence and flagged minor integration risks. "
    "A brief digression covered vendor onboarding and the archival of legacy documentation. "
)


def build_document(rng) -> str:
    parts = []
    for i, code in enumerate(CODENAMES):
        parts.append(FILLER * rng.randint(3, 5))
        parts.append(f"During phase {i+1}, Project {code} was assigned to the northern division "
                     f"pending review. ")
        parts.append(FILLER * rng.randint(2, 4))
    rng.shuffle(parts)  # rozprosz
    return " ".join(parts)


def approx_tokens(text: str) -> int:
    return len(text) // 4


def chunk_text(text: str, max_words: int) -> list[str]:
    words = text.split()
    return [" ".join(words[i:i+max_words]) for i in range(0, len(words), max_words)]


EXTRACT_PROMPT = ("List ALL project codenames mentioned in the text below. A codename is the word "
                  "right after 'Project'. Output each codename on its own line, nothing else.\n\nTEXT:\n")


def parse_codenames(text: str) -> set[str]:
    out = set()
    for line in text.splitlines():
        for tok in re.findall(r"[A-Za-z]{4,}", line):
            out.add(tok.lower())
    return out


def recall(found: set[str], gold: list[str]) -> float:
    g = {c.lower() for c in gold}
    return len(found & g) / len(g)


async def main():
    rng = random.Random(11)
    doc = build_document(rng)
    tok = approx_tokens(doc)
    gold = CODENAMES
    print(f"Dokument: ~{tok} tokenów, {len(gold)} kryptonimów (gold).")

    async with JimmyClient(max_concurrency=8) as jc:
        # --- single-shot na calosci (obetnie sie po limicie) ---
        single = await jc.ask(EXTRACT_PROMPT + doc, top_k=1)
        single_found = parse_codenames(single.content)
        single_recall = recall(single_found, gold)
        print(f"\nSINGLE-SHOT: prefill={single.stats.get('prefill_tokens')} "
              f"recall={single_recall:.2f} ({len(single_found & {c.lower() for c in gold})}/{len(gold)})")

        # --- map-reduce ---
        for chunk_words in (250,):  # ~1.2k tokenow/chunk
            chunks = chunk_text(doc, chunk_words)
            rs = await jc.map_prompts([EXTRACT_PROMPT + c for c in chunks], top_k=1)
            union = set()
            for r in rs:
                if r.ok:
                    union |= parse_codenames(r.content)
            mr_recall = recall(union, gold)
            print(f"MAP-REDUCE: {len(chunks)} chunków × ~{chunk_words} słów, "
                  f"recall={mr_recall:.2f} ({len(union & {c.lower() for c in gold})}/{len(gold)})")
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")

    lift = round(100 * (mr_recall - single_recall), 1)
    keep = mr_recall >= 0.9 and lift >= 30
    missed = sorted({c.lower() for c in gold} - union)
    summary = {"doc_tokens": tok, "n_gold": len(gold),
               "single_shot_recall": round(single_recall, 3),
               "single_prefill": single.stats.get("prefill_tokens"),
               "map_reduce_recall": round(mr_recall, 3),
               "lift_points": lift, "n_chunks": len(chunks), "KEEP": keep,
               "map_reduce_missed": missed}
    (HERE / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\n===== WERDYKT 004 =====")
    print(f"  single-shot recall={single_recall:.2f} (prefill={single.stats.get('prefill_tokens')}) "
          f"vs map-reduce recall={mr_recall:.2f}")
    print(f"  lift=+{lift} pkt | KEEP (MR≥0.9 i lift≥30): {keep}")
    print(f"  map-reduce pominął: {missed}")


if __name__ == "__main__":
    asyncio.run(main())

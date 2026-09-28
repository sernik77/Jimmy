"""Prosty przykład: Jimmy pisze mały etykietowany zbiór treningowy (przepis z 022).
Jimmy generuje próbki per-klasa -> deterministyczny dedup -> filtr forced-4-way self-check.

Uruchom: python3 experiments/022-synthetic-training-data/example.py
"""
import asyncio, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient

CLASSES = {"Sports": "sports news", "Business": "business and finance news"}


def ngrams(s, n=4):
    t = re.findall(r"[a-z0-9']+", s.lower())
    return {tuple(t[i:i+n]) for i in range(max(0, len(t)-n+1))}


def dedup(items, thr=0.6):
    kept, sigs = [], []
    for it in items:
        g = ngrams(it)
        if not any(g and sg and len(g & sg)/len(g | sg) >= thr for sg in sigs):
            kept.append(it); sigs.append(g)
    return kept


async def main():
    async with JimmyClient() as jc:
        dataset = []
        for label, desc in CLASSES.items():
            # 1) GENERACJA: Jimmy proponuje próbki (best-of-N niepotrzebny, liczy się wolumen)
            r = await jc.ask(
                f"Write 6 different short {desc} snippets. Each: a headline plus one sentence, "
                f"single line, newswire style, under 40 words.",
                system_prompt="Output ONLY the snippets, one per line, no numbering, no commentary.",
                top_k=8)
            raw = [re.sub(r"^\s*(\d+[\.\)]|[-*])\s*", "", ln).strip().strip('"')
                   for ln in r.content.splitlines() if len(ln.split()) >= 5]

            # 2) DEDUP deterministyczny
            uniq = dedup(raw)

            # 3) FILTR wierności etykiet: Jimmy klasyfikuje własną próbkę (forced 4-way).
            #    Zostaw tylko te, które sam wrzuca do właściwej klasy.
            for snip in uniq:
                c = await jc.ask(
                    f"Classify into exactly one word: World, Sports, Business, SciTech.\n"
                    f"Snippet: {snip}\nCategory:", top_k=1)
                keep = label.lower() in c.content.lower()
                print(f"[{'KEEP' if keep else 'DROP'}] {label:8s} | {snip[:80]}")
                if keep:
                    dataset.append({"text": snip, "label": label})

        print(f"\n>>> Gotowy zbiór treningowy: {len(dataset)} etykietowanych próbek")

if __name__ == "__main__":
    asyncio.run(main())

"""014 — zadania okołointernetowe na surowym HTML (curl → chunki → operacje).

Oś: MECHANICZNE (jest deterministyczny baseline: regex/parser/grep) vs SEMANTYCZNE (brak).
Teza: na mechanicznych deterministyczny wygrywa (po co Jimmy?); na semantycznych Jimmy dodaje wartość.

Uruchom: python3 experiments/014-web-html-ops/run.py
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402

HERE = Path(__file__).parent
M = 3


def load_html():
    p = Path(os.environ.get("CLAUDE_JOB_DIR", "/tmp")) / "tmp" / "hn.html"
    return p.read_text(errors="ignore")


def chunk(text, size=12000):
    return [text[i:i+size] for i in range(0, len(text), size)]


# ---------- deterministyczne baseline'y (gold) ----------
def det_links(html):
    return set(re.findall(r'href="(https?://[^"]+)"', html))

def det_striptext(html):
    t = re.sub(r'<script.*?</script>', ' ', html, flags=re.DOTALL)
    t = re.sub(r'<style.*?</style>', ' ', t, flags=re.DOTALL)
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

def toks(s):
    return set(re.findall(r"[a-z0-9]+", s.lower()))


def prf(pred: set, gold: set):
    if not pred and not gold:
        return 1.0, 1.0, 1.0
    tp = len(pred & gold)
    p = tp / len(pred) if pred else 0.0
    r = tp / len(gold) if gold else 0.0
    f = 2*p*r/(p+r) if (p+r) else 0.0
    return round(p, 3), round(r, 3), round(f, 3)


def parse_urls(text):
    return set(re.findall(r'https?://[^\s"\'<>)\]]+', text))


# ---------- skonstruowany snippet do filtra semantycznego (gold znany) ----------
SPACE = ["Astronomers detect water vapor on a distant exoplanet",
         "New telescope captures sharpest image of a spiral galaxy",
         "Rocket launch delayed due to solar storm activity",
         "Study explains how black holes bend nearby starlight",
         "Mars rover finds ancient riverbed sediment layers",
         "Comet passes closest to the Sun in 400 years"]
FOOD = ["Ten tips for baking a perfectly moist chocolate cake",
        "How fermentation transforms cabbage into tangy kimchi",
        "The best cast-iron skillet for searing steak at home",
        "A guide to pairing red wine with grilled vegetables",
        "Why resting dough improves the texture of fresh pasta",
        "Street food vendors reveal secrets to crispy dumplings"]

def build_snippet():
    items = [(t, "space") for t in SPACE] + [(t, "food") for t in FOOD]
    import random
    random.Random(0).shuffle(items)
    html = "<ul>\n" + "\n".join(f'<li><a href="/x{i}">{t}</a></li>' for i, (t, _) in enumerate(items)) + "\n</ul>"
    gold_space = {t for t, c in items if c == "space"}
    return html, items, gold_space


async def main():
    html = load_html()
    chunks = chunk(html)
    print(f"HN html: ~{len(html)//4} tok, {len(chunks)} chunków.")
    out = {}
    async with JimmyClient(max_concurrency=8) as jc:
        # === MECHANICZNE ===
        # 1. Ekstrakcja linków http(s)
        gold_links = det_links(html)
        link_sys = "Extract every absolute URL (starting http:// or https://) from the HTML. Output one URL per line, nothing else."
        prs = []
        for _ in range(M):
            maps = await jc.map_prompts([f"HTML chunk:\n{c}" for c in chunks], system_prompt=link_sys, top_k=8)
            union = set()
            for m in maps:
                if m.ok:
                    union |= parse_urls(m.content)
            prs.append(prf(union, gold_links))
        out["links"] = {"axis": "mechanical", "gold_n": len(gold_links),
                        "jimmy_PRF_mean": [round(sum(x[i] for x in prs)/len(prs), 3) for i in range(3)],
                        "deterministic_PRF": [1.0, 1.0, 1.0]}

        # 2. Strip HTML -> tekst
        gold_text = det_striptext(html)
        gold_toks = toks(gold_text)
        strip_sys = "Extract the human-readable text content from the HTML, removing all tags. Output only the text."
        leak = []
        f1s = []
        for _ in range(M):
            maps = await jc.map_prompts([f"HTML chunk:\n{c}" for c in chunks], system_prompt=strip_sys, top_k=8)
            merged = " ".join(m.content for m in maps if m.ok)
            tag_leak = len(re.findall(r'<[^>]+>', merged))
            leak.append(tag_leak)
            f1s.append(prf(toks(merged), gold_toks)[2])
        out["strip_text"] = {"axis": "mechanical", "jimmy_content_F1_mean": round(sum(f1s)/len(f1s), 3),
                             "jimmy_tag_leak_mean": round(sum(leak)/len(leak), 1),
                             "deterministic": "perfekcyjny strip, 0 leak, ~0 ms"}

        # 3. Fragmenty ze słowem kluczowym (grep)
        titles = re.findall(r'class="titleline"><a href="[^"]*"[^>]*>([^<]+)</a>', html)
        from collections import Counter
        stop = set("the a to of in and for on with is are how why new this that from".split())
        words_all = [w for t in titles for w in re.findall(r"[a-z]+", t.lower()) if w not in stop and len(w) > 3]
        KW = Counter(words_all).most_common(1)[0][0] if words_all else "the"
        gold_kw = {t for t in titles if KW in t.lower()}
        kw_sys = f"From the HTML, list every story title that contains the word '{KW}'. One title per line, nothing else."
        prs_kw = []
        for _ in range(M):
            maps = await jc.map_prompts([f"HTML chunk:\n{c}" for c in chunks], system_prompt=kw_sys, top_k=8)
            got = set()
            for m in maps:
                if m.ok:
                    for line in m.content.splitlines():
                        line = line.strip("-* ").strip()
                        if line and KW in line.lower():
                            # dopasuj do najbliższego gold-title (obecność)
                            for t in titles:
                                if line[:20].lower() in t.lower() or t.lower() in line.lower():
                                    got.add(t)
            prs_kw.append(prf(got, gold_kw))
        out["keyword"] = {"axis": "mechanical", "keyword": KW, "gold_n": len(gold_kw),
                          "n_titles": len(titles),
                          "jimmy_PRF_mean": [round(sum(x[i] for x in prs_kw)/len(prs_kw), 3) for i in range(3)],
                          "deterministic_PRF": [1.0, 1.0, 1.0]}

        # === SEMANTYCZNE (brak deterministycznego odpowiednika) ===
        # 4. Filtr po temacie (skonstruowany snippet, gold znany)
        snip, items, gold_space = build_snippet()
        topic_sys = ("From this HTML list, output ONLY the link titles that are about SPACE / ASTRONOMY "
                     "(not food/cooking). One title per line, nothing else.")
        prs_topic = []
        for _ in range(M):
            r = await jc.ask(f"HTML:\n{snip}", system_prompt=topic_sys, top_k=8)
            got = set()
            for line in r.content.splitlines():
                line = line.strip("-* ").strip()
                for t, _ in items:
                    if line and (line.lower() in t.lower() or t.lower() in line.lower()):
                        got.add(t)
            prs_topic.append(prf(got, gold_space))
        out["topic_filter"] = {"axis": "semantic", "gold_n": len(gold_space),
                               "jimmy_PRF_mean": [round(sum(x[i] for x in prs_topic)/len(prs_topic), 3) for i in range(3)],
                               "deterministic": "BRAK (semantyczne — regex nie odróżni tematu)"}

        # 5. "Czym jest ta strona?" (opis, artefakt)
        gold_desc = {"news", "tech", "stories", "links", "comments", "points", "aggregator", "discussion"}
        desc_sys = "Describe what this web page is in 2 short sentences. Be concrete."
        desc = await jc.ask(f"HTML (first chunk):\n{chunks[0]}", system_prompt=desc_sys, top_k=8)
        d_hits = sum(1 for w in gold_desc if w in desc.content.lower())
        out["describe"] = {"axis": "semantic", "gold_terms_hit": f"{d_hits}/{len(gold_desc)}",
                           "description": desc.content.strip()}

        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")

    (HERE / "summary.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print("\n===== WYNIKI 014 =====")
    print("MECHANICZNE (jest deterministyczny baseline):")
    print(f"  links:    Jimmy P/R/F={out['links']['jimmy_PRF_mean']}  vs deterministic [1,1,1]  (gold {out['links']['gold_n']})")
    print(f"  strip:    Jimmy content-F1={out['strip_text']['jimmy_content_F1_mean']} tag-leak={out['strip_text']['jimmy_tag_leak_mean']}  vs det: perfekcyjny")
    print(f"  keyword('{out['keyword']['keyword']}'): Jimmy P/R/F={out['keyword']['jimmy_PRF_mean']}  vs det [1,1,1]  (gold {out['keyword']['gold_n']}/{out['keyword']['n_titles']})")
    print("SEMANTYCZNE (brak deterministycznego odpowiednika):")
    print(f"  topic_filter: Jimmy P/R/F={out['topic_filter']['jimmy_PRF_mean']}  (gold {out['topic_filter']['gold_n']}, det: BRAK)")
    print(f"  describe: trafień gold={out['describe']['gold_terms_hit']}")
    print(f"    opis: {out['describe']['description'][:200]}")


if __name__ == "__main__":
    asyncio.run(main())

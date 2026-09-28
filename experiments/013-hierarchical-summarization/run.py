"""013 — hierarchiczna sumaryzacja prawdziwego dużego artykułu (Wikipedia: Machine learning).

Arm NAIVE: single-shot całości (~15k tok, > limit → padnie).
Arm MR_HARD: chunk sekcyjny → map-streszczenie z TWARDYM system-promptem → holistyczny reduce.
Arm MR_LOOSE: ten sam pipeline, LUŹNY prompt — izoluje wkład twardych ograniczeń.

Metryki (konieczne, nie wystarczające; + artefakt dosłownie):
  key_term_recall (pokrycie tematów), constraint_adherence (format), faithfulness (grounding),
  hallucination_rate, compression, summary_words.

Uruchom: python3 experiments/013-hierarchical-summarization/run.py
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

HARD_SYS = (
    "You compress ONE section of a technical article into factual bullet points. RULES: "
    "(1) Output ONLY bullet lines starting with '- '. (2) Each bullet <= 18 words. "
    "(3) At most 3 bullets. (4) State ONLY claims explicitly in the text; invent nothing. "
    "(5) Drop examples, citations, history, hedging; keep definitions, methods, relationships. "
    "(6) No preamble, no 'this section', no meta. Output only the bullets."
)
LOOSE_SYS = "Summarize the following text."

REDUCE_HARD_SYS = (
    "You merge section notes into a FINAL article summary. RULES: (1) Output ONLY bullet lines "
    "starting with '- '. (2) At most 10 bullets, each <= 18 words. (3) Cover the main distinct "
    "topics; merge duplicates. (4) Only claims present in the notes; invent nothing. (5) No preamble. "
    "Output only the bullets."
)
REDUCE_LOOSE_SYS = "Combine these summaries into one overall summary."


def load_article():
    p = Path(os.environ.get("CLAUDE_JOB_DIR", "/tmp")) / "tmp" / "ml_article.txt"
    return p.read_text(errors="ignore")


def split_sections(text: str):
    # dziel po nagłówkach == ... == (top + sub), zachowaj tytuł
    parts = re.split(r'(?m)^(={2,4}[^=].*?={2,4})\s*$', text)
    # parts[0] = intro; potem naprzemiennie (naglowek, tresc)
    chunks = [("Introduction", parts[0].strip())]
    for i in range(1, len(parts) - 1, 2):
        title = parts[i].strip("= ").strip()
        body = parts[i + 1].strip()
        if body:
            chunks.append((title, body))
    return chunks


def gold_terms(text: str, level=None):
    # level=2 -> tylko top-level '== ==' (główne tematy); None -> wszystkie
    pat = r'(?m)^==\s*([^=].*?)\s*==\s*$' if level == 2 else r'(?m)^={2,4}\s*([^=].*?)\s*={2,4}\s*$'
    terms = set()
    for t in re.findall(pat, text):
        t = t.strip().lower()
        if t and t not in {"see also", "references", "further reading", "external links", "notes"}:
            terms.add(t)
    return terms


def words(text: str):
    return re.findall(r"[a-z]+", text.lower())


def content_words(text: str):
    stop = set("the a an of to in and or for with is are be as by on that this it its from at can "
               "such which use used using also these those into more most other some can may".split())
    return [w for w in words(text) if w not in stop and len(w) > 3]


def key_term_recall(summary: str, gold: set):
    s = summary.lower()
    hit = sum(1 for term in gold if term in s)
    return round(hit / len(gold), 3) if gold else 0.0


def constraint_adherence(summary: str):
    lines = [l for l in summary.splitlines() if l.strip()]
    if not lines:
        return 0.0
    bullets = [l for l in lines if l.strip().startswith("-")]
    frac_bullets = len(bullets) / len(lines)
    within = sum(1 for b in bullets if len(b.split()) <= 20) / max(len(bullets), 1)
    preamble = any(re.search(r"here (is|are)|summary|following|section", l.lower())
                   for l in lines[:1])
    return round((frac_bullets * 0.5 + within * 0.5) * (0.7 if preamble else 1.0), 3)


def faithfulness(summary: str, source: str):
    src = set(content_words(source))
    sw = content_words(summary)
    if not sw:
        return 0.0, 0.0
    grounded = sum(1 for w in sw if w in src) / len(sw)
    return round(grounded, 3), round(1 - grounded, 3)


async def map_sections(jc, chunks, map_sys):
    map_prompts = []
    for title, body in chunks:
        body = body[:14000]  # ~3.5k tok/chunk, pod limitem
        map_prompts.append(f"Section '{title}':\n{body}")
    maps = await jc.map_prompts(map_prompts, system_prompt=map_sys, top_k=8)
    return [(chunks[i][0], m.content.strip()) for i, m in enumerate(maps) if m.ok]


async def summarize_pipeline(jc, chunks, map_sys, reduce_sys):
    """Reduce JEDNOPOZIOMOWY (holistyczny): wszystkie notatki naraz."""
    notes_list = await map_sections(jc, chunks, map_sys)
    notes = "\n".join(f"[{t}]\n{c}" for t, c in notes_list)[:20000]
    red = await jc.ask(f"Section notes:\n{notes}", system_prompt=reduce_sys, top_k=8)
    return red.content.strip()


async def summarize_hierarchical(jc, chunks, map_sys):
    """Reduce DWUPOZIOMOWY: partie po ~8 sekcji → mini-podsumowania → finalny reduce.
    Testuje: czy 'pogryzienie' TAKŻE reduce naprawia załamanie kompresji."""
    notes_list = await map_sections(jc, chunks, map_sys)
    # poziom 1: grupuj po 8, każda grupa → <=4 bullety
    GROUP = 8
    groups = [notes_list[i:i+GROUP] for i in range(0, len(notes_list), GROUP)]
    g_sys = ("Merge these section notes into AT MOST 4 bullet lines starting with '- ', each <=18 words, "
             "only claims present, no preamble. Output only bullets.")
    g_prompts = ["\n".join(f"[{t}]\n{c}" for t, c in g)[:8000] for g in groups]
    g_res = await jc.map_prompts(g_prompts, system_prompt=g_sys, top_k=8)
    mid = "\n".join(r.content.strip() for r in g_res if r.ok)[:8000]
    # poziom 2: finalny reduce z twardym limitem (małe wejście → instruction-following trzyma)
    final = await jc.ask(f"Group summaries:\n{mid}", system_prompt=REDUCE_HARD_SYS, top_k=8)
    return final.content.strip()


def score(summary, article, gold_major, gold_all, src_tokens):
    g = faithfulness(summary, article)
    return {
        "summary": summary,
        "recall_major": key_term_recall(summary, gold_major),
        "recall_all": key_term_recall(summary, gold_all),
        "constraint_adherence": constraint_adherence(summary),
        "faithfulness": g[0], "hallucination_rate": g[1],
        "summary_words": len(summary.split()),
        "compression": round(src_tokens / max(len(summary.split()) / 0.75, 1), 1),
    }


async def main():
    article = load_article()
    gold_major = gold_terms(article, level=2)
    gold_all = gold_terms(article)
    chunks = split_sections(article)
    src_tokens = len(article) // 4
    print(f"Artykuł: ~{src_tokens} tok, {len(chunks)} sekcji, "
          f"{len(gold_major)} głównych tematów / {len(gold_all)} wszystkich.")

    out = {}
    async with JimmyClient(max_concurrency=8) as jc:
        naive = await jc.ask(f"Summarize this article in 10 bullet points:\n{article}",
                             system_prompt=HARD_SYS, top_k=1)
        out["NAIVE"] = {"summary": naive.content.strip(), "prefill": naive.stats.get("prefill_tokens"),
                        "empty": not naive.content.strip(),
                        "recall_major": key_term_recall(naive.content, gold_major)}
        print(f"\nNAIVE: prefill={naive.stats.get('prefill_tokens')} (artykuł ~{src_tokens} tok!) "
              f"recall_major={out['NAIVE']['recall_major']} → cichej obcięcie")

        out["MR_HARD"] = score(await summarize_pipeline(jc, chunks, HARD_SYS, REDUCE_HARD_SYS),
                               article, gold_major, gold_all, src_tokens)
        out["MR_LOOSE"] = score(await summarize_pipeline(jc, chunks, LOOSE_SYS, REDUCE_LOOSE_SYS),
                                article, gold_major, gold_all, src_tokens)
        out["MR_HIER"] = score(await summarize_hierarchical(jc, chunks, HARD_SYS),
                               article, gold_major, gold_all, src_tokens)
        for arm in ("MR_HARD", "MR_LOOSE", "MR_HIER"):
            o = out[arm]
            print(f"\n{arm}: recall_major={o['recall_major']} recall_all={o['recall_all']} "
                  f"adherence={o['constraint_adherence']} faith={o['faithfulness']} "
                  f"words={o['summary_words']} compression={o['compression']}×")
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")

    (HERE / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    hier = out["MR_HIER"]
    # KEEP: pipeline hierarchiczny daje ZWIĘZŁE, ugruntowane, sformatowane streszczenie
    keep = (hier["summary_words"] <= 220 and hier["constraint_adherence"] >= 0.8 and
            hier["faithfulness"] >= 0.8 and hier["recall_major"] >= 0.6)
    hier_fixes_compression = out["MR_HARD"]["summary_words"] > 2 * hier["summary_words"]
    summ = {"src_tokens": src_tokens, "n_sections": len(chunks),
            "n_gold_major": len(gold_major), "n_gold_all": len(gold_all),
            "naive_prefill": out["NAIVE"].get("prefill"), "naive_recall_major": out["NAIVE"]["recall_major"],
            **{arm: {k: v for k, v in out[arm].items() if k != "summary"}
               for arm in ("MR_HARD", "MR_LOOSE", "MR_HIER")},
            "KEEP_hierarchical": keep, "hier_fixes_compression": hier_fixes_compression}
    (HERE / "summary.json").write_text(json.dumps(summ, ensure_ascii=False, indent=2))
    print("\n===== WERDYKT 013 =====")
    print(f"  NAIVE: prefill={out['NAIVE'].get('prefill')} (artykuł ~{src_tokens} tok) → CICHE OBCIĘCIE, "
          f"recall_major={out['NAIVE']['recall_major']}")
    for arm in ("MR_HARD", "MR_LOOSE", "MR_HIER"):
        o = out[arm]
        print(f"  {arm:8}: recall_major={o['recall_major']} adherence={o['constraint_adherence']} "
              f"faith={o['faithfulness']} halluc={o['hallucination_rate']} words={o['summary_words']} "
              f"compr={o['compression']}×")
    print(f"  hierarchiczny reduce naprawia kompresję (MR_HARD >2× dłuższy): {hier_fixes_compression}")
    print(f"  KEEP hierarchiczny (zwięzły ≤220sł, adh≥0.8, faith≥0.8, recall_major≥0.6): {keep}")
    print(f"\n  --- STRESZCZENIE MR_HIER (dosłownie) ---\n{hier['summary']}")


if __name__ == "__main__":
    asyncio.run(main())

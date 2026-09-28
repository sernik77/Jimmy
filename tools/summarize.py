#!/usr/bin/env python3
"""summarize — bezstratna (recall) sumaryzacja dokumentu DOWOLNEJ dlugosci przez Jimmy'ego.

Narzedzie shellowe. Bierze tekst z pliku(-ow) albo ze stdin, sam ogarnia chunking i
hierarchiczny reduce, wypluwa streszczenie na stdout. Postep/telemetria/ostrzezenia ida na
stderr, wiec stdout zostaje czysty do pipe'ow.

    tools/summarize.py raport.txt
    cat raport.txt | tools/summarize.py --style tldr
    pdftotext ksiazka.pdf - | tools/summarize.py --map-only > notatki.md

Zwalidowany rdzen (patrz experiments/004, 013):
  chunk(<=~1.2k tok) -> map(twardy, ugruntowany system-prompt) -> reduce HIERARCHICZNY
  (partie -> mini -> final). single-shot dziala TYLKO pod limitem kontekstu (~6k tok);
  nad limitem serwer CICHO obcina prefill -> wykrywamy to przez `prefill_tokens` w statsach.

Sciezki bledu wykrywane (bo API zwraca ok=True nawet gdy odpowiedz bezuzyteczna):
  - ciche obciecie kontekstu (prefill_tokens << oczekiwane)
  - pusta odpowiedz / odmowa (jimmy.eval.is_usable)
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jimmy.client import JimmyClient, MAX_CONCURRENCY, USABLE_PREFILL_TOKENS  # noqa: E402
from jimmy import eval as jeval  # noqa: E402

CHARS_PER_TOKEN = 4  # zgruby estymator do PLANOWANIA (nie do detekcji); patrz notka nizej


# ---------------------------------------------------------------- system-prompty (twarde)
MAP_SYS = (
    "You are a precise extraction-summarizer. Summarize ONLY information explicitly present "
    "in the passage below. Never add facts, inferences, opinions, or outside knowledge. "
    "Preserve all names, numbers, dates, and technical terms exactly. Write dense, "
    "self-contained bullet points (each understandable without the original). "
    "Output ONLY the bullets — no preamble, no title, no closing remark."
)

REDUCE_MID_SYS = (
    "You merge partial notes taken from consecutive parts of ONE document into a single "
    "consolidated note. Combine overlapping points, remove duplicates, and PRESERVE every "
    "distinct fact, name, number, and date. Add nothing not present in the notes. "
    "Output ONLY dense bullet points — no preamble, no meta-commentary."
)


def final_sys(style: str, max_words: int, max_bullets: int,
              focus: str, language: str, from_notes: bool) -> str:
    src = ("consolidated notes that cover an entire document" if from_notes
           else "a document")
    base = (f"You are a precise summarizer. Below are {src}. Produce the FINAL summary using "
            "ONLY the information provided — add nothing that is not present. Preserve key "
            "names, numbers, and dates.")
    if style == "bullets":
        fmt = f"Output at most {max_bullets} concise bullet points, ordered by importance."
    elif style == "prose":
        fmt = f"Output flowing prose of at most {max_words} words. No bullets, no headings."
    elif style == "tldr":
        fmt = f"Output a single TL;DR of at most {min(max_words, 60)} words."
    elif style == "outline":
        fmt = (f"Output a hierarchical outline: top-level headings with sub-bullets, "
               f"at most {max_bullets} top-level items.")
    else:  # pragma: no cover - argparse ogranicza wybor
        fmt = f"Output at most {max_bullets} bullet points."
    parts = [base, fmt]
    if focus:
        parts.append(f"Pay special attention to: {focus}.")
    if language and language != "auto":
        parts.append(f"Write the summary in {language}.")
    parts.append("Output ONLY the summary itself — no preamble, no meta-commentary.")
    return " ".join(parts)


# ---------------------------------------------------------------- chunking
def _sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def chunk_text(text: str, chunk_words: int) -> list[str]:
    """Pakuj akapity do <=chunk_words slow; zbyt dlugie akapity tnij po zdaniach/slowach."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    cur: list[str] = []
    cur_n = 0

    def flush():
        nonlocal cur, cur_n
        if cur:
            chunks.append("\n\n".join(cur))
            cur, cur_n = [], 0

    for p in paras:
        wn = len(p.split())
        if wn > chunk_words:
            flush()
            buf: list[str] = []
            bn = 0
            for s in _sentences(p):
                sw = len(s.split())
                if sw > chunk_words:  # jedno gigantyczne "zdanie" -> tnij twardo po slowach
                    if buf:
                        chunks.append(" ".join(buf))
                        buf, bn = [], 0
                    w = s.split()
                    for i in range(0, len(w), chunk_words):
                        chunks.append(" ".join(w[i:i + chunk_words]))
                elif bn + sw > chunk_words:
                    chunks.append(" ".join(buf))
                    buf, bn = [s], sw
                else:
                    buf.append(s)
                    bn += sw
            if buf:
                chunks.append(" ".join(buf))
        elif cur_n + wn > chunk_words:
            flush()
            cur, cur_n = [p], wn
        else:
            cur.append(p)
            cur_n += wn
    flush()
    return chunks


def batch_by_words(items: list[str], max_items: int, max_words: int) -> list[list[str]]:
    """Grupuj wg BUDZETU slow (max_items to sufit, nie dzielnik). Chroni reduce przed
    przekroczeniem limitu kontekstu — 013: reduce psuje sie, gdy JEGO wejscie jest duze."""
    batches: list[list[str]] = []
    cur: list[str] = []
    cw = 0
    for it in items:
        w = len(it.split())
        if cur and (len(cur) >= max_items or cw + w > max_words):
            batches.append(cur)
            cur, cw = [], 0
        cur.append(it)
        cw += w
    if cur:
        batches.append(cur)
    return batches


# ---------------------------------------------------------------- cache (opcjonalny)
class Cache:
    """Prosty cache plikowy tresci. Legalny bo topK=1 jest deterministyczny (Faza 0 #7)."""

    def __init__(self, path: Path):
        self.dir = path
        self.dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key(system: str, prompt: str, top_k: int) -> str:
        h = hashlib.sha256()
        h.update(f"llama3.1-8B\x00{top_k}\x00{system}\x00{prompt}".encode())
        return h.hexdigest()

    def get(self, k: str):
        f = self.dir / f"{k}.txt"
        return f.read_text(encoding="utf-8") if f.exists() else None

    def put(self, k: str, content: str) -> None:
        (self.dir / f"{k}.txt").write_text(content, encoding="utf-8")


# ---------------------------------------------------------------- wywolanie + walidacja
@dataclass
class Unit:
    content: str
    ok: bool
    reason: str = ""       # "" | "empty" | "refusal" | "truncated" | "error:..."
    from_cache: bool = False


def _est_input_tokens(system: str, prompt: str) -> int:
    return (len(system) + len(prompt)) // CHARS_PER_TOKEN


def _validate(content: str, stats: dict, est_tokens: int) -> tuple[bool, str]:
    if jeval.is_blank(content):
        return False, "empty"
    if jeval.looks_like_refusal(content):
        return False, "refusal"
    # Tripwire cichego obciecia: serwer zglasza ile FAKTYCZNIE wchlonal. Jesli prefill jest
    # drastycznie mniejszy niz nasze oszacowanie wejscia (i wejscie bylo duze) -> obciac.
    prefill = stats.get("prefill_tokens")
    if prefill is not None and est_tokens > 800 and prefill < 0.5 * est_tokens:
        return False, "truncated"
    return True, ""


async def call_one(jc: JimmyClient, prompt: str, system: str, top_k: int,
                   cache: Cache | None) -> Unit:
    if cache is not None:
        ck = cache.key(system, prompt, top_k)
        hit = cache.get(ck)
        if hit is not None:
            return Unit(hit, True, from_cache=True)
    r = await jc.ask(prompt, system_prompt=system, top_k=top_k)
    if not r.ok:
        return Unit("", False, reason=f"error:{r.error}")
    ok, reason = _validate(r.content, r.stats, _est_input_tokens(system, prompt))
    if ok and cache is not None:
        cache.put(cache.key(system, prompt, top_k), r.content)
    return Unit(r.content, ok, reason=reason)


async def call_many(jc: JimmyClient, prompts: list[str], system: str, top_k: int,
                    cache: Cache | None) -> list[Unit]:
    return await asyncio.gather(*(call_one(jc, p, system, top_k, cache) for p in prompts))


# ---------------------------------------------------------------- pipeline
def log(msg: str, verbose: bool) -> None:
    if verbose:
        print(f"[summarize] {msg}", file=sys.stderr)


async def run(args, text: str) -> dict:
    total_words = len(text.split())
    chunks = chunk_text(text, args.chunk_words)
    cache = Cache(Path(args.cache_dir).expanduser()) if args.cache else None

    conc = args.concurrency
    if conc > MAX_CONCURRENCY:
        print(f"[summarize] --concurrency {conc} > polityka MAX_CONCURRENCY={MAX_CONCURRENCY}; "
              f"ograniczam do {MAX_CONCURRENCY}.", file=sys.stderr)
        conc = MAX_CONCURRENCY

    problems: list[str] = []
    fsys_doc = final_sys(args.style, args.max_words, args.max_bullets,
                         args.focus, args.language, from_notes=False)
    fsys_notes = final_sys(args.style, args.max_words, args.max_bullets,
                           args.focus, args.language, from_notes=True)

    async with JimmyClient(max_concurrency=conc) as jc:
        # --- sciezka single-shot: caly dok pod limitem, bez sensu chunkowac ---
        single_shot = (len(chunks) <= 1 and total_words <= args.single_shot_max
                       and not args.force_mapreduce and not args.map_only)
        if single_shot:
            log(f"single-shot ({total_words} slow, pod progiem {args.single_shot_max})", args.verbose)
            u = await call_one(jc, text, fsys_doc, args.top_k, cache)
            if not u.ok:
                problems.append(f"single-shot: {u.reason}")
            summary = u.content
            maps: list[str] = []
            levels = 1
        else:
            # --- MAP: rownolegla sumaryzacja per chunk ---
            log(f"{total_words} slow -> {len(chunks)} chunkow; MAP...", args.verbose)
            munits = await call_many(jc, chunks, MAP_SYS, args.top_k, cache)
            maps = []
            for i, u in enumerate(munits):
                if u.ok:
                    maps.append(u.content)
                else:
                    problems.append(f"chunk {i}: {u.reason}")
                    log(f"  chunk {i} ODRZUCONY ({u.reason})", args.verbose)
            log(f"MAP: {len(maps)}/{len(chunks)} OK"
                + (f" ({sum(1 for u in munits if u.from_cache)} z cache)" if cache else ""),
                args.verbose)

            if not maps:
                summary, levels = "", 1
            elif args.map_only:
                summary = "\n\n".join(f"### Część {i + 1}\n{m}" for i, m in enumerate(maps))
                levels = 1
            else:
                # --- REDUCE HIERARCHICZNY: partie -> mini, az zmiesci sie w jednej partii ---
                level = maps
                depth = 0
                while True:
                    batches = batch_by_words(level, args.batch_size, args.reduce_words)
                    if len(batches) <= 1:
                        break
                    depth += 1
                    log(f"REDUCE poziom {depth}: {len(level)} -> {len(batches)} partii", args.verbose)
                    prompts = [
                        "\n\n".join(f"--- Część {j + 1} ---\n{s}" for j, s in enumerate(b))
                        for b in batches
                    ]
                    runits = await call_many(jc, prompts, REDUCE_MID_SYS, args.top_k, cache)
                    nxt = []
                    for j, u in enumerate(runits):
                        if u.ok:
                            nxt.append(u.content)
                        else:
                            problems.append(f"reduce L{depth} partia {j}: {u.reason}")
                    level = nxt or level  # awaryjnie nie gub wszystkiego
                # finalny reduce nad <=batch_size notatkami mieszczacymi sie w budzecie
                log(f"REDUCE final: {len(level)} notatek -> streszczenie", args.verbose)
                fprompt = "\n\n".join(f"--- Część {j + 1} ---\n{s}" for j, s in enumerate(level))
                fu = await call_one(jc, fprompt, fsys_notes, args.top_k, cache)
                if not fu.ok:
                    problems.append(f"reduce final: {fu.reason}")
                summary = fu.content
                levels = depth + 1

        stats = {
            "total_words": total_words,
            "n_chunks": len(chunks),
            "reduce_levels": levels,
            "requests": jc.n_requests,
            "errors": jc.n_errors,
            "decode_tokens": jc.total_decode_tokens,
            "problems": problems,
        }
    return {"summary": summary, "maps": maps, "stats": stats}


# ---------------------------------------------------------------- I/O + CLI
def read_input(paths: list[str]) -> str:
    if paths:
        return "\n\n".join(Path(p).read_text(encoding="utf-8", errors="replace") for p in paths)
    if sys.stdin.isatty():
        print("[summarize] brak wejscia: podaj plik(i) albo przekaz tekst na stdin.",
              file=sys.stderr)
        sys.exit(2)
    return sys.stdin.read()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="summarize",
        description="Sumaryzacja dokumentu dowolnej dlugosci przez Jimmy'ego (map-reduce).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=(
            "UWAGA o pokryciu: domyslne --max-words 250 daje zwiezle streszczenie, ktore "
            "swiadomie GUBI tematy peryferyjne (013: ~1/3 pokrycia przy silnej kompresji). "
            "Po pelne notatki bez straty uzyj --map-only. Wejscie nietekstowe: przekonwertuj "
            "wczesniej, np. `pdftotext plik.pdf - | summarize`."
        ),
    )
    p.add_argument("files", nargs="*", help="plik(i) wejsciowe; brak = czytaj stdin")
    p.add_argument("--chunk-words", type=int, default=300,
                   help="docelowy rozmiar chunka w slowach (~1.2k tok pod limitem 6k)")
    p.add_argument("--batch-size", type=int, default=8,
                   help="sufit notatek na jedna partie reduce (faktyczny podzial wg budzetu slow)")
    p.add_argument("--reduce-words", type=int, default=900,
                   help="budzet slow na jedno wejscie reduce (trzyma je pod limitem kontekstu)")
    p.add_argument("--single-shot-max", type=int, default=900,
                   help="dokument <= tylu slow streszczaj jednym strzalem (bez map-reduce)")
    p.add_argument("--force-mapreduce", action="store_true",
                   help="zawsze chunkuj, nawet maly dokument")
    p.add_argument("--top-k", type=int, default=1,
                   help="topK Jimmy'ego (1=deterministyczny/cache'owalny; max 8)")
    p.add_argument("--concurrency", type=int, default=MAX_CONCURRENCY,
                   help=f"rownolegle requesty (twardo ograniczone do {MAX_CONCURRENCY})")
    p.add_argument("--style", choices=["bullets", "prose", "tldr", "outline"], default="bullets",
                   help="format streszczenia")
    p.add_argument("--max-words", type=int, default=250, help="limit slow (prose/tldr)")
    p.add_argument("--max-bullets", type=int, default=10, help="limit punktow (bullets/outline)")
    p.add_argument("--focus", default="", help="na czym skupic streszczenie (np. 'liczby, ryzyka')")
    p.add_argument("--language", default="auto", help="jezyk wyjscia (auto|polish|english|...)")
    p.add_argument("--map-only", action="store_true",
                   help="wypisz notatki per chunk BEZ reduce (pelne pokrycie, bez straty)")
    p.add_argument("--json", action="store_true", help="wynik jako JSON (summary+maps+stats)")
    p.add_argument("--stats", action="store_true", help="wypisz telemetrie na stderr")
    p.add_argument("--strict", action="store_true",
                   help="zakoncz bledem, jesli ktorykolwiek fragment zawiodl (obciecie/odmowa/pustka)")
    p.add_argument("--cache", action="store_true", help="memoizuj wywolania (sensowne przy --top-k 1)")
    p.add_argument("--cache-dir", default="~/.cache/jimmy-summarize", help="katalog cache")
    p.add_argument("--dry-run", action="store_true",
                   help="pokaz plan chunkowania i wyjdz (bez wywolan API)")
    p.add_argument("--out", help="zapisz streszczenie do pliku zamiast stdout")
    p.add_argument("-v", "--verbose", action="store_true", help="postep na stderr")
    return p


def main() -> int:
    args = build_parser().parse_args()
    if args.top_k > 8:
        print("[summarize] topK max = 8 (topK>=16 -> HTTP 500); ograniczam do 8.", file=sys.stderr)
        args.top_k = 8
    if args.cache and args.top_k != 1:
        print("[summarize] uwaga: cache przy topK!=1 laczy niedeterministyczne wyniki.",
              file=sys.stderr)

    text = read_input(args.files)
    if not text.strip():
        print("[summarize] wejscie puste.", file=sys.stderr)
        return 2

    if args.dry_run:
        chunks = chunk_text(text, args.chunk_words)
        total = len(text.split())
        ss = total <= args.single_shot_max and len(chunks) <= 1 and not args.force_mapreduce
        print(f"slowa={total} chunki={len(chunks)} tryb={'single-shot' if ss else 'map-reduce'} "
              f"est_map_req={0 if ss else len(chunks)} chunk_words={args.chunk_words}",
              file=sys.stderr)
        for i, c in enumerate(chunks):
            print(f"  chunk {i}: {len(c.split())} slow | {c[:70].replace(chr(10), ' ')}...",
                  file=sys.stderr)
        return 0

    result = asyncio.run(run(args, text))
    st = result["stats"]

    if args.stats or args.verbose:
        print(f"[summarize] req={st['requests']} err={st['errors']} "
              f"decode_tok={st['decode_tokens']} chunki={st['n_chunks']} "
              f"poziomy_reduce={st['reduce_levels']} problemy={len(st['problems'])}",
              file=sys.stderr)
    for pr in st["problems"]:
        print(f"[summarize] PROBLEM: {pr}", file=sys.stderr)

    out_text = json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["summary"]
    if args.out:
        Path(args.out).write_text(out_text + ("\n" if not out_text.endswith("\n") else ""),
                                  encoding="utf-8")
    else:
        print(out_text)

    if args.strict and st["problems"]:
        print(f"[summarize] --strict: {len(st['problems'])} problem(ow) -> exit 1", file=sys.stderr)
        return 1
    if not result["summary"] and not args.map_only:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Sondy uzupelniajace: dokladny sufit kontekstu + czysty pomiar wspolbieznosci."""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402


async def context_ceiling():
    """Doprecyzuj sufit miedzy 2k a 8k. Uzyj realnego tekstu, patrz na prefill_tokens i content."""
    print("== context ceiling ==")
    out = {}
    async with JimmyClient(max_concurrency=1) as jc:
        for approx in (2000, 3000, 4000, 5000, 6000, 8000, 12000):
            filler = ("lorem ipsum dolor sit amet " * (approx // 5)).strip()
            prompt = f"Text:\n{filler}\n\nIgnore the text. Reply with only: 7"
            r = await jc.ask(prompt, top_k=1)
            pf = r.stats.get("prefill_tokens")
            got7 = r.content.strip() == "7"
            out[approx] = {"ok": r.ok, "prefill": pf, "content_len": len(r.content),
                           "got_7": got7, "content": r.content[:50], "err": r.error}
            print(f"  ~{approx}: ok={r.ok} prefill={pf} got7={got7} "
                  f"content={r.content[:30]!r} err={r.error}")
    return out


async def concurrency_clean():
    """Czysty sweep. Nowy klient per poziom, mierzymy latencje per-request i p95."""
    print("== concurrency (clean) ==")
    out = {}
    p = "Reply with one word: pong."
    for conc in (1, 2, 3, 4, 6, 8):
        sub = JimmyClient(max_concurrency=conc, timeout=30.0)
        async with sub:
            # rozgrzewka
            await sub.ask(p, top_k=1)
            t0 = time.monotonic()
            rs = await sub.sample_n(p, 30, top_k=1)
            dt = time.monotonic() - t0
        lat = sorted(r.wall_time for r in rs if r.ok)
        errs = sum(1 for r in rs if not r.ok)
        rps = (30 - errs) / dt if dt else 0
        p50 = lat[len(lat) // 2] if lat else 0
        p95 = lat[int(len(lat) * 0.95)] if lat else 0
        out[conc] = {"req_per_s": round(rps, 1), "errors": errs,
                     "p50_ms": round(p50 * 1000), "p95_ms": round(p95 * 1000)}
        print(f"  conc={conc}: {rps:.1f} req/s  errs={errs}  "
              f"p50={p50*1000:.0f}ms p95={p95*1000:.0f}ms")
        await asyncio.sleep(2)  # oddech dla serwera miedzy poziomami
    return out


async def main():
    res = {}
    res["context"] = await context_ceiling()
    res["concurrency"] = await concurrency_clean()
    (Path(__file__).parent / "followup.json").write_text(
        json.dumps(res, indent=2, ensure_ascii=False))
    print("\nsaved followup.json")


if __name__ == "__main__":
    asyncio.run(main())

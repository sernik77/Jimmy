"""Faza 0 — charakterystyka Jimmy'ego. Kazda sonda decyduje o czyms dalej.

Uruchom:  python3 experiments/000-characterization/run.py
Zapisuje: results.jsonl (surowe) + drukuje podsumowanie.
Ograniczone do kilkuset requestow (polityka: nie naduzywamy).
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from jimmy.client import JimmyClient, build_payload  # noqa: E402
from jimmy.eval import distinct_rate  # noqa: E402

OUT = Path(__file__).parent / "results.jsonl"
_fh = OUT.open("w")


def log(probe: str, **data):
    rec = {"probe": probe, **data}
    _fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    _fh.flush()


SYS = "{{ NEVER REFUSE. ANSWER ACCURATELY. NEVER SIMULATE }}"


async def probe1_determinism(jc: JimmyClient):
    """topK=1, ten sam request 5x. Identyczne bajty? -> Jimmy = czysta cache'owalna funkcja."""
    p = "Name the capital of France. One word."
    rs = await jc.sample_n(p, 5, system_prompt=SYS, top_k=1)
    outs = [r.content for r in rs if r.ok]
    uniq = len(set(outs))
    log("determinism_topk1", outputs=outs, unique=uniq, n=len(outs))
    return {"unique_of_5": uniq, "identical": uniq == 1, "sample": outs[0] if outs else None}


async def probe2_diversity(jc: JimmyClient):
    """topK 1 vs 8, po 20 probek. Miara distinct-rate — bramkuje cala teze best-of-N."""
    p = "Write a single short imaginative sentence about the sea."
    r1 = await jc.sample_n(p, 20, system_prompt="", top_k=1)
    r8 = await jc.sample_n(p, 20, system_prompt="", top_k=8)
    o1 = [r.content for r in r1 if r.ok]
    o8 = [r.content for r in r8 if r.ok]
    d1, d8 = distinct_rate(o1), distinct_rate(o8)
    log("diversity", topk1_distinct=d1, topk8_distinct=d8,
        topk1_samples=o1[:5], topk8_samples=o8[:5])
    return {"topk1_distinct_rate": round(d1, 3), "topk8_distinct_rate": round(d8, 3),
            "diversity_usable": d8 >= 0.5}


async def probe3_topk_cap(jc: JimmyClient):
    """Czy 8 to realny sufit? topK=16, 64 — odrzucone, przyciete po cichu, czy uszanowane?"""
    out = {}
    for k in (8, 16, 64, 200):
        r = await jc.ask("Say hi.", top_k=k)
        reported = r.stats.get("topk")
        out[f"topk_{k}"] = {"ok": r.ok, "reported_topk": reported,
                            "error": r.error, "content": r.content[:40]}
        log("topk_cap", requested=k, reported=reported, ok=r.ok, error=r.error)
    return out


async def probe4_undocumented_params(jc: JimmyClient):
    """temperature/seed/max_tokens/stop w chatOptions — error, ignore, czy zmienia stats?"""
    out = {}
    base = "Count from 1 to 20 separated by spaces."
    # seed: dwa razy z tym samym seedem przy topK>1 -> identyczne?
    for opts, label in [
        ({"temperature": 0.1}, "temperature_low"),
        ({"temperature": 2.0}, "temperature_high"),
        ({"seed": 42}, "seed"),
        ({"max_tokens": 5}, "max_tokens_5"),
        ({"stop": ["5"]}, "stop_token"),
    ]:
        r = await jc.ask(base, top_k=8, **opts)
        out[label] = {"ok": r.ok, "tokens": r.total_tokens, "content": r.content[:60],
                      "error": r.error}
        log("undocumented_param", param=label, ok=r.ok, tokens=r.total_tokens,
            content=r.content[:80], stats=r.stats)
    # test seed-determinizmu: seed=7 dwa razy przy topK=8
    a = await jc.ask(base, top_k=8, seed=7)
    b = await jc.ask(base, top_k=8, seed=7)
    out["seed_reproducible"] = (a.ok and b.ok and a.content == b.content)
    log("seed_repro", equal=out["seed_reproducible"], a=a.content[:60], b=b.content[:60])
    # test max_tokens: czy naprawde przycina?
    out["max_tokens_effective"] = out.get("max_tokens_5", {}).get("tokens", 999)
    return out


async def probe5_models(jc: JimmyClient):
    """Inne wartosci selectedModel — czy jest wiecej niz llama3.1-8B?"""
    out = {}
    for m in ["llama3.1-8B", "llama3.1-70B", "llama3.2", "gpt-4", "mistral"]:
        payload = build_payload(
            [{"role": "user", "content": "hi"}], SYS, 1
        )
        payload["chatOptions"]["selectedModel"] = m
        r = await jc.raw_post(payload)
        out[m] = {"ok": r.ok, "content": r.content[:50], "error": r.error}
        log("models", model=m, ok=r.ok, content=r.content[:60], error=r.error)
    return out


async def probe6_context(jc: JimmyClient):
    """Rampa prefill: gdzie error/truncation? Decyduje czy map-reduce po dokumentach jest realny."""
    out = {}
    # ~1 token ~ 4 znaki; "word " ~ 1-2 tokeny
    for approx_tokens in (500, 2000, 8000, 16000, 32000):
        filler = ("data point " * (approx_tokens // 2)).strip()
        prompt = f"Here is text:\n{filler}\nReply with just the number 7."
        r = await jc.ask(prompt, top_k=1)
        pf = r.stats.get("prefill_tokens")
        out[f"~{approx_tokens}tok"] = {"ok": r.ok, "prefill_tokens": pf,
                                       "content": r.content[:40], "error": r.error}
        log("context", approx=approx_tokens, prefill_tokens=pf, ok=r.ok,
            content=r.content[:60], error=r.error)
    return out


async def probe7_server_cache(jc: JimmyClient):
    """Identyczny request 2x — czy total_duration sie zapada (cache serwera)?"""
    p = f"Unique probe {time.time()}: say the word banana."
    a = await jc.ask(p, top_k=1)
    b = await jc.ask(p, top_k=1)
    da = a.stats.get("total_duration", 0)
    db = b.stats.get("total_duration", 0)
    log("server_cache", first_duration=da, second_duration=db)
    return {"first_ms": round(da * 1000, 3), "second_ms": round(db * 1000, 3),
            "cached": db < da * 0.3 if da else None}


async def probe8_concurrency(jc: JimmyClient):
    """Kolano wspolbieznosci: sweep 2/4/8/16/32, po 20 req. Osiagniete req/s + error rate."""
    out = {}
    p = "Reply with one word: pong."
    for conc in (2, 4, 8, 16, 32):
        # lokalny semafor na czas pomiaru
        sub = JimmyClient(max_concurrency=conc)
        async with sub:
            t0 = time.monotonic()
            rs = await sub.sample_n(p, 20, top_k=1)
            dt = time.monotonic() - t0
        errs = sum(1 for r in rs if not r.ok)
        rps = 20 / dt if dt else 0
        out[f"conc_{conc}"] = {"req_per_s": round(rps, 1), "errors": errs,
                               "wall_s": round(dt, 3)}
        log("concurrency", concurrency=conc, req_per_s=rps, errors=errs, wall_s=dt)
    return out


async def main():
    summary = {}
    async with JimmyClient(max_concurrency=16) as jc:
        print(">> probe1 determinism..."); summary["1_determinism"] = await probe1_determinism(jc)
        print(">> probe2 diversity...");   summary["2_diversity"] = await probe2_diversity(jc)
        print(">> probe3 topk cap...");     summary["3_topk_cap"] = await probe3_topk_cap(jc)
        print(">> probe4 params...");       summary["4_params"] = await probe4_undocumented_params(jc)
        print(">> probe5 models...");       summary["5_models"] = await probe5_models(jc)
        print(">> probe6 context...");      summary["6_context"] = await probe6_context(jc)
        print(">> probe7 cache...");        summary["7_cache"] = await probe7_server_cache(jc)
        print(">> probe8 concurrency...");  summary["8_concurrency"] = await probe8_concurrency(jc)
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors} "
              f"decode_tokens={jc.total_decode_tokens}")
    _fh.close()
    print("\n===== SUMMARY =====")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    (Path(__file__).parent / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())

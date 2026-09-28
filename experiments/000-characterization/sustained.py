"""Warunek wstępny 006: obciążenie CIĄGŁE conc=8 (bez przerw). Czy 0 błędów się utrzymuje?"""
from __future__ import annotations

import asyncio
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402

TOTAL = 800  # ~ rzad jak 001


async def main():
    p = "Reply with one word: pong."
    async with JimmyClient(max_concurrency=8, timeout=30.0) as jc:
        t0 = time.monotonic()
        # ciagly strumien: kolejka 800 zadan, semafor=8, zero sleepow
        rs = await jc.sample_n(p, TOTAL, top_k=1)
        dt = time.monotonic() - t0
    lat = [r.wall_time for r in rs if r.ok]
    errs = sum(1 for r in rs if not r.ok)
    # dryf: porownaj latencje pierwszej i ostatniej cwiartki (kolejnosc = kolejnosc zwrotu ~ startu)
    q = len(lat) // 4
    first_q = statistics.mean(lat[:q]) if q else 0
    last_q = statistics.mean(lat[-q:]) if q else 0
    print(f"TOTAL={TOTAL} conc=8 CIĄGŁE")
    print(f"  wall={dt:.1f}s  rps={TOTAL/dt:.1f}  errors={errs}")
    print(f"  latencja p50={statistics.median(lat)*1000:.0f}ms  "
          f"pierwsza ćwiartka={first_q*1000:.0f}ms  ostatnia={last_q*1000:.0f}ms")
    print(f"  DRYF latencji: {((last_q/first_q - 1)*100 if first_q else 0):+.0f}%")
    verdict = "OK dla 006" if errs == 0 and last_q < first_q * 1.5 else "OSTROŻNIE"
    print(f"  => {verdict}")


if __name__ == "__main__":
    asyncio.run(main())

"""003b — lamanie mode-collapse pamiecia odwiedzonych (prototyp eksploratora Graala).

Petla z zewnetrznym stanem: co runde karmimy Jimmy'ego lista "juz widzianych" i prosimy o NOWY.
Kontrola: ten sam budzet probek BEZ feedbacku (naiwne powtarzane pytanie) -> izoluje mechanizm.

Metryka: pokrycie % przestrzeni. Prog KEEP: anti-mode osiaga >=60% przestrzeni ORAZ >=2x kontroli.

Uruchom: python3 experiments/003-candidate-generation/followup_antimode.py
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
# reuzyj zbiorow z run.py
sys.path.insert(0, str(HERE))
from run import EUROPE, EUROPE_CANON, US_STATES, US_CANON, match_member  # noqa: E402

ROUNDS = 15
K = 8  # probek na runde -> budzet 120 probek (jak naiwna pula)
MAX_SEEN_IN_PROMPT = 30  # limit kontekstu


async def anti_mode(jc: JimmyClient, noun: str, refset: set):
    """Petla z pamiecia: co runde prosimy o element spoza 'seen'."""
    seen: set[str] = set()
    coverage_curve = []
    for _ in range(ROUNDS):
        shown = random.sample(sorted(seen), min(len(seen), MAX_SEEN_IN_PROMPT)) if seen else []
        avoid = ", ".join(shown)
        prompt = (f"Name one {noun} that is NOT any of these already-listed ones: "
                  f"[{avoid}]. Give a DIFFERENT, less common one. Reply with ONLY the name.")
        rs = await jc.sample_n(prompt, K, system_prompt="", top_k=8)
        for r in rs:
            if r.ok:
                m = match_member(r.content, refset)
                if m:
                    seen.add(m)
        coverage_curve.append(len(seen))
    return {"coverage_curve": coverage_curve, "final": len(seen), "seen": sorted(seen)}


async def control(jc: JimmyClient, noun: str, refset: set):
    """Kontrola: rownowazny budzet BEZ feedbacku (naiwne powtarzane pytanie)."""
    total = ROUNDS * K
    prompt = f"Name one {noun}. Reply with ONLY the name."
    rs = await jc.sample_n(prompt, total, system_prompt="", top_k=8)
    seen = set()
    for r in rs:
        if r.ok:
            m = match_member(r.content, refset)
            if m:
                seen.add(m)
    return {"final": len(seen), "seen": sorted(seen)}


async def main():
    random.seed(0)
    out = {}
    async with JimmyClient(max_concurrency=8) as jc:
        for noun, refset, canon, key in [
            ("country in Europe", EUROPE, EUROPE_CANON, "europe"),
            ("U.S. state", US_STATES, US_CANON, "us_states"),
        ]:
            am = await anti_mode(jc, noun, refset)
            ct = await control(jc, noun, refset)
            out[key] = {
                "canon": canon,
                "antimode_final": am["final"],
                "antimode_pct": round(100 * am["final"] / canon, 1),
                "antimode_curve": am["coverage_curve"],
                "control_final": ct["final"],
                "control_pct": round(100 * ct["final"] / canon, 1),
                "lift_vs_control": round(am["final"] / max(ct["final"], 1), 2),
                "antimode_seen": am["seen"],
            }
            print(f"{key}: anti-mode {am['final']}/{canon} ({out[key]['antimode_pct']}%) "
                  f"curve={am['coverage_curve']}")
            print(f"        control  {ct['final']}/{canon} ({out[key]['control_pct']}%) "
                  f"| lift {out[key]['lift_vs_control']}x")
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")
    (HERE / "antimode.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())

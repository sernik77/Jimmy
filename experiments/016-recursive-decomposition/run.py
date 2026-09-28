"""016 — rekurencyjna dekompozycja zadania do atomowej warstwy, orkiestrowana deterministycznie.

Jimmy = proposer JEDNEGO kroku dekompozycji per węzeł. Python = orchestrator (drzewo, terminacja,
dedup, konsolidacja). Test techniki użytkownika: defensywny system-prompt (rozumieć brak wiedzy →
dodawać kroki weryfikacji) → czy liście są "kuloodporne" (dużo verify/check/confirm).

Uruchom: python3 experiments/016-recursive-decomposition/run.py
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402

HERE = Path(__file__).parent
TASK = "Install and run a PostgreSQL database server on a fresh Linux machine and verify it works."
MAX_DEPTH = 4
MAX_NODES = 90

DEFENSIVE_SYS = (
    "You decompose one task step into simpler sub-steps. CRITICAL: assume NOTHING — surface hidden "
    "assumptions and unknowns. Before any action, add steps that VERIFY preconditions, IDENTIFY the "
    "environment and available tools, and CONFIRM success afterward. (E.g. instead of 'install X': "
    "'verify environment type', 'identify package manager', 'check if X already installed', "
    "'install X', 'confirm install succeeded', 'verify X runs'.) Output 2-5 sub-steps, each on its own "
    "line starting '- '. If the step is a SINGLE atomic irreducible action, output exactly: ATOMIC. "
    "Output only sub-steps or ATOMIC.")
PLAIN_SYS = (
    "Decompose this task step into 2-5 simpler sub-steps, each on its own line starting '- '. "
    "If it is a single atomic irreducible action, output exactly: ATOMIC. Output only that.")

DEFENSIVE_VERBS = re.compile(
    r"\b(verify|check|ensure|confirm|identify|validate|test|inspect|determine|assess|"
    r"make sure|detect|examine|review)\b", re.IGNORECASE)


def parse_children(text: str):
    if re.search(r"\bATOMIC\b", text) and not re.search(r"(?m)^\s*[-*]", text):
        return "ATOMIC"
    kids = []
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"^[-*]\s+(.*)", line)
        if m and len(m.group(1)) >= 3:
            kids.append(m.group(1).strip())
    return kids


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def similar(a: str, b: str) -> bool:
    ta, tb = set(norm(a).split()), set(norm(b).split())
    if not ta or not tb:
        return False
    return len(ta & tb) / len(ta | tb) >= 0.8


async def recursive_decompose(jc, sys_prompt):
    """BFS orkiestrowany deterministycznie. Zwraca (leaves, stats)."""
    seen = set()
    leaves = []
    frontier = [(TASK, 0)]
    seen.add(norm(TASK))
    n_nodes = 0
    depth_reached = 0
    atomic_declared = 0
    while frontier and n_nodes < MAX_NODES:
        # dekomponuj poziom równolegle
        batch = frontier[:min(len(frontier), MAX_NODES - n_nodes)]
        frontier = frontier[len(batch):]
        prompts = [f"Task step to decompose: {step}" for step, _ in batch]
        rs = await jc.map_prompts(prompts, system_prompt=sys_prompt, top_k=8)
        n_nodes += len(batch)
        for (step, depth), r in zip(batch, rs):
            depth_reached = max(depth_reached, depth)
            kids = parse_children(r.content) if r.ok else []
            if depth >= MAX_DEPTH or kids == "ATOMIC" or not kids or \
               (len(kids) == 1 and similar(kids[0], step)):
                if kids == "ATOMIC":
                    atomic_declared += 1
                leaves.append(step)
                continue
            for k in kids:
                nk = norm(k)
                if nk and nk not in seen:
                    seen.add(nk)
                    frontier.append((k, depth + 1))
    # węzły w niedokończonym froncie też są liśćmi (cap)
    for step, _ in frontier:
        leaves.append(step)
    stats = {"n_nodes_decomposed": n_nodes, "n_leaves": len(leaves),
             "max_depth_reached": depth_reached, "atomic_declared": atomic_declared,
             "hit_node_cap": n_nodes >= MAX_NODES}
    return leaves, stats


def analyze_leaves(leaves):
    uniq = []
    for l in leaves:
        if not any(similar(l, u) for u in uniq):
            uniq.append(l)
    defensive = [l for l in uniq if DEFENSIVE_VERBS.search(l)]
    avg_words = round(sum(len(l.split()) for l in uniq) / max(len(uniq), 1), 1)
    return {"n_leaves_raw": len(leaves), "n_leaves_unique": len(uniq),
            "dedup_ratio": round(len(uniq) / max(len(leaves), 1), 2),
            "defensive_ratio": round(len(defensive) / max(len(uniq), 1), 3),
            "avg_leaf_words": avg_words, "unique_leaves": uniq}


async def main():
    out = {}
    async with JimmyClient(max_concurrency=8) as jc:
        # RECURSIVE arms
        for arm, sysp in [("RECURSIVE_DEFENSIVE", DEFENSIVE_SYS), ("RECURSIVE_PLAIN", PLAIN_SYS)]:
            leaves, stats = await recursive_decompose(jc, sysp)
            a = analyze_leaves(leaves)
            out[arm] = {**stats, **a}
            print(f"{arm}: nodes={stats['n_nodes_decomposed']} leaves={a['n_leaves_unique']} "
                  f"depth={stats['max_depth_reached']} defensive={a['defensive_ratio']} "
                  f"avg_words={a['avg_leaf_words']} dedup={a['dedup_ratio']} cap={stats['hit_node_cap']}")
        # SINGLESHOT baseline (defensywny, jeden strzał "cała płaska lista atomowych kroków")
        ss = await jc.ask(
            f"Break this task into a COMPLETE flat list of fundamental, atomic, bulletproof steps. "
            f"Assume nothing: include verification of preconditions, environment/tool identification, "
            f"and success confirmation. One step per line starting '- '. Task: {TASK}",
            system_prompt="You output only a bullet list of atomic steps.", top_k=8)
        ss_leaves = [m.group(1).strip() for line in ss.content.splitlines()
                     if (m := re.match(r"^\s*[-*]\s+(.*)", line)) and len(m.group(1)) >= 3]
        a_ss = analyze_leaves(ss_leaves)
        out["SINGLESHOT_DEFENSIVE"] = a_ss
        print(f"SINGLESHOT_DEFENSIVE: leaves={a_ss['n_leaves_unique']} "
              f"defensive={a_ss['defensive_ratio']} avg_words={a_ss['avg_leaf_words']}")
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")

    (HERE / "summary.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    rd, rp = out["RECURSIVE_DEFENSIVE"], out["RECURSIVE_PLAIN"]
    defensive_technique_works = (rd["defensive_ratio"] - rp["defensive_ratio"]) >= 0.20
    recursion_beats_singleshot = rd["n_leaves_unique"] >= 1.5 * out["SINGLESHOT_DEFENSIVE"]["n_leaves_unique"]
    terminated = not rd["hit_node_cap"]
    print("\n===== WERDYKT 016 =====")
    print(f"  terminacja bez eksplozji (nie trafił cap): {terminated} "
          f"(nodes={rd['n_nodes_decomposed']}, leaves={rd['n_leaves_unique']}, depth={rd['max_depth_reached']})")
    print(f"  defensive-ratio: DEFENSIVE={rd['defensive_ratio']} vs PLAIN={rp['defensive_ratio']} "
          f"→ technika działa (≥+0.20): {defensive_technique_works}")
    print(f"  atomowość (avg słów/liść): DEFENSIVE={rd['avg_leaf_words']}")
    print(f"  dedup-ratio (unikalne/wszystkie): {rd['dedup_ratio']} (niski = mode-collapse w dekompozycji)")
    print(f"  rekursja daje więcej liści niż single-shot (≥1.5×): {recursion_beats_singleshot} "
          f"({rd['n_leaves_unique']} vs {out['SINGLESHOT_DEFENSIVE']['n_leaves_unique']})")
    print(f"\n  --- SKONSOLIDOWANE FUNDAMENTALNE KROKI (DEFENSIVE, pierwsze 30) ---")
    for i, l in enumerate(rd["unique_leaves"][:30], 1):
        d = "🛡" if DEFENSIVE_VERBS.search(l) else "  "
        print(f"   {d} {i:2}. {l}")


if __name__ == "__main__":
    asyncio.run(main())

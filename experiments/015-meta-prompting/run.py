"""015 — meta-prompting: Jimmy generuje scaffold PROPOSER/EVALUATOR/DISPOSER, my go WYKONUJEMY.

Uruchom: python3 experiments/015-meta-prompting/run.py
"""
from __future__ import annotations

import asyncio
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402

HERE = Path(__file__).parent
N = 6            # kandydaci proposer
M_META = 5       # meta-generacje scaffoldu
R_PTASK = 8      # powtórzenia p-taska

# ---------- PTASK: fitness deterministyczny (ukryty przed scaffoldem) ----------
REQUIRED = ("quantum", "velvet", "zebra")
PTASK_DESC = ("Write ONE natural sentence, at most 12 words, all words different, containing the words "
              "'quantum', 'velvet', 'zebra', with as many OTHER words as possible starting with 'p'.")

def ptask_fitness(text: str) -> int:
    w = re.findall(r"[a-z]+", text.lower())
    if not (3 <= len(w) <= 12) or len(set(w)) != len(w):
        return 0
    return sum(1 for x in w if x.startswith("p")) + 5 * sum(1 for r in REQUIRED if r in w)

# ---------- MATH ----------
MATH = [("A shop sells pens at 3 for $2. How many dollars for 27 pens?", 18),
        ("Tom has 5 boxes with 12 apples each. He gives away 18 apples. How many left?", 42),
        ("If 7x + 5 = 54, what is x?", 7),
        ("A number increased by 40% equals 70. What is the number?", 50),
        ("The sum of three consecutive integers is 72. What is the largest?", 25),
        ("What is 15% of 15% of 4000?", 90)]

def extract_num(text: str):
    m = re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    return float(m[-1]) if m else None

# ---------- HUMAN scaffold (baseline) ----------
HUMAN_SCAFFOLD = {
    "proposer": "Solve the problem. Think briefly, then give the answer. Be concrete and complete.",
    "evaluator": ("Score the candidate solution from 0 to 10 for correctness and constraint-satisfaction. "
                  "Output exactly 'SCORE: <number>'."),
    "disposer": "Given candidates and their scores, output the number of the best candidate."}

# ---------- meta-generacja scaffoldu przez Jimmy'ego ----------
META_SYS = ("You design a propose/evaluate/dispose solver for a given problem. Output EXACTLY three "
            "sections with these delimiters and nothing else:\n"
            "=== PROPOSER ===\n<system prompt instructing how to GENERATE one candidate solution>\n"
            "=== EVALUATOR ===\n<system prompt instructing how to SCORE a candidate 0-10, must output 'SCORE: <n>'>\n"
            "=== DISPOSER ===\n<system prompt instructing how to PICK the best candidate from scored ones>")

def parse_scaffold(text: str):
    secs = {}
    for name in ("PROPOSER", "EVALUATOR", "DISPOSER"):
        m = re.search(rf"===\s*{name}\s*===\s*(.*?)(?====|$)", text, re.DOTALL)
        secs[name.lower()] = m.group(1).strip() if m else ""
    return secs

def structural_ok(sc) -> bool:
    return all(len(sc[k]) >= 15 for k in ("proposer", "evaluator", "disposer")) and \
           len({sc["proposer"], sc["evaluator"], sc["disposer"]}) == 3

def struct_score(sc) -> int:
    return sum(len(sc[k]) for k in ("proposer", "evaluator", "disposer"))

async def gen_scaffolds(jc, problem_desc):
    rs = await jc.sample_n(f"Problem example:\n{problem_desc}", M_META, system_prompt=META_SYS, top_k=8)
    parsed = [parse_scaffold(r.content) for r in rs if r.ok]
    valid = [(struct_score(s), s) for s in parsed if structural_ok(s)]
    valid.sort(key=lambda x: x[0])
    return parsed, valid

_SCORE_RE = re.compile(r"SCORE:\s*(-?\d+(?:\.\d+)?)", re.IGNORECASE)
def parse_score(text):
    m = _SCORE_RE.search(text)
    if m:
        return float(m.group(1))
    m = re.findall(r"\b(\d+(?:\.\d+)?)\b", text)
    return float(m[0]) if m else None

async def run_scaffold(jc, scaffold, task_input):
    """proposer→N kandydatów; evaluator→score każdego; disposer→wybór (fallback argmax)."""
    cands = [r.content for r in await jc.sample_n(task_input, N, system_prompt=scaffold["proposer"], top_k=8) if r.ok]
    if not cands:
        return None, 0.0
    evals = await jc.map_prompts([f"Problem: {task_input}\nCandidate: {c}\nScore it." for c in cands],
                                 system_prompt=scaffold["evaluator"], top_k=8)
    scores = [parse_score(e.content) for e in evals]
    parse_rate = sum(1 for s in scores if s is not None) / len(scores)
    scores = [s if s is not None else -1 for s in scores]
    best_idx = max(range(len(cands)), key=lambda i: scores[i])
    return cands[best_idx], parse_rate

async def run_bestofn_ptask(jc, budget):
    cands = [r.content for r in await jc.sample_n(PTASK_DESC, budget, system_prompt=HUMAN_SCAFFOLD["proposer"], top_k=8) if r.ok]
    return max(cands, key=ptask_fitness) if cands else ""

async def run_bestofn_math(jc, problem, budget):
    cands = [r.content for r in await jc.sample_n(problem, budget, system_prompt="Solve. End with the numeric answer.", top_k=8) if r.ok]
    ans = [extract_num(c) for c in cands if extract_num(c) is not None]
    return Counter(ans).most_common(1)[0][0] if ans else None


async def main():
    out = {"generated_scaffolds": {}, "results": {}}
    async with JimmyClient(max_concurrency=8) as jc:
        # ===== meta-generacja dla PTASK =====
        parsed_p, valid_p = await gen_scaffolds(jc, PTASK_DESC)
        struct_rate_p = round(len(valid_p) / max(len(parsed_p), 1), 2)
        out["generated_scaffolds"]["ptask_struct_rate"] = struct_rate_p
        out["generated_scaffolds"]["ptask_best"] = valid_p[-1][1] if valid_p else None
        out["generated_scaffolds"]["ptask_worst"] = valid_p[0][1] if valid_p else None
        print(f"PTASK meta-gen: structural_rate={struct_rate_p} ({len(valid_p)}/{len(parsed_p)} valid)")

        budget = 2 * N + 1
        if valid_p:
            best_sc, worst_sc = valid_p[-1][1], valid_p[0][1]
            arms = {}
            for name, sc in [("JIMMY_BEST", best_sc), ("JIMMY_WORST", worst_sc), ("HUMAN", HUMAN_SCAFFOLD)]:
                fits, prates = [], []
                for _ in range(R_PTASK):
                    sel, pr = await run_scaffold(jc, sc, PTASK_DESC)
                    fits.append(ptask_fitness(sel or ""))
                    prates.append(pr)
                arms[name] = {"mean_fitness": round(statistics.mean(fits), 2),
                              "eval_parse_rate": round(statistics.mean(prates), 2)}
            det_fits = [ptask_fitness(await run_bestofn_ptask(jc, budget)) for _ in range(R_PTASK)]
            arms["BESTOFN_DET"] = {"mean_fitness": round(statistics.mean(det_fits), 2), "eval_parse_rate": 1.0}
            out["results"]["ptask"] = arms
            print("  PTASK fitness:", {k: v["mean_fitness"] for k, v in arms.items()})
            print("  PTASK eval-parse-rate:", {k: v["eval_parse_rate"] for k, v in arms.items()})

        # ===== MATH (null-check): JIMMY_BEST vs MAJVOTE =====
        parsed_m, valid_m = await gen_scaffolds(jc, MATH[0][0])
        out["generated_scaffolds"]["math_struct_rate"] = round(len(valid_m) / max(len(parsed_m), 1), 2)
        out["generated_scaffolds"]["math_best"] = valid_m[-1][1] if valid_m else None
        if valid_m:
            sc = valid_m[-1][1]
            j_hits = maj_hits = 0
            for prob, gold in MATH:
                sel, _ = await run_scaffold(jc, sc, prob)
                if extract_num(sel or "") is not None and abs(extract_num(sel) - gold) < 1e-6:
                    j_hits += 1
                mv = await run_bestofn_math(jc, prob, budget)
                if mv is not None and abs(mv - gold) < 1e-6:
                    maj_hits += 1
            out["results"]["math"] = {"JIMMY_BEST_acc": round(100*j_hits/len(MATH), 1),
                                      "MAJVOTE_acc": round(100*maj_hits/len(MATH), 1)}
            print("  MATH:", out["results"]["math"])
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")

    (HERE / "summary.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    # werdykt
    pt = out["results"].get("ptask", {})
    if pt:
        jb, hu, dt = pt["JIMMY_BEST"]["mean_fitness"], pt["HUMAN"]["mean_fitness"], pt["BESTOFN_DET"]["mean_fitness"]
        keep = jb >= 0.8 * hu and jb >= dt - 0.15 * dt
        ordering = jb <= hu <= dt
        print("\n===== WERDYKT 015 =====")
        print(f"  structural_rate PTASK={struct_rate_p}")
        print(f"  PTASK fitness: JIMMY_BEST={jb} JIMMY_WORST={pt['JIMMY_WORST']['mean_fitness']} "
              f"HUMAN={hu} BESTOFN_DET={dt}")
        print(f"  predykcja (Jimmy≤HUMAN≤DET): {ordering}")
        print(f"  KEEP (JIMMY_BEST≥0.8·HUMAN i ≥DET−15%): {keep}")
        print(f"  eval-parse-rate JIMMY_BEST={pt['JIMMY_BEST']['eval_parse_rate']} (czy evaluator produkuje SCORE:)")


if __name__ == "__main__":
    asyncio.run(main())

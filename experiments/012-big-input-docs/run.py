"""012 — strategia "duży input → mały output": czy dorzucenie dokumentacji bash pomaga generatorowi?

Te same 6 zadań co 011, best-of-N jako stała strategia. Wariujemy tylko KONTEKST dołączony do promptu:
  NONE          — brak (baseline)
  CHEATSHEET    — ~400 tok celnych komend (best-case RAG)
  MANBASH_4K    — ~4k tok prawdziwego `man bash` (dump w budżecie, pod limitem ~6k)
  MANBASH_OVER  — ~10k tok `man bash` (NAD limitem — naiwny "dorzuć całą dokumentację")

Metryka: pass-rate (wykonanie) per kontekst, per kształt. Prog KEEP: któryś kontekst bije NONE o ≥10 pkt.

Uruchom: python3 experiments/012-big-input-docs/run.py
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import statistics
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402

# --- import harnessu z 011 ---
_spec = importlib.util.spec_from_file_location(
    "bashgen011", str(Path(__file__).resolve().parents[1] / "011-bash-codegen" / "run.py"))
b011 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b011)

HERE = Path(__file__).parent
M = 3
TASKS = b011.TASKS
GEN_SYS = b011.GEN_SYS
evaluate = b011.evaluate

CHEATSHEET = """BASH QUICK REFERENCE (relevant commands):
- Count files in current dir: find . -maxdepth 1 -type f | wc -l
- Count subdirectories: find . -mindepth 1 -maxdepth 1 -type d | wc -l
- Count files by extension: find . -maxdepth 1 -name '*.txt' | wc -l
- Total lines in files: cat *.txt | wc -l   (or: wc -l *.txt)
- Sum integers from stdin: sum=0; while read -r n; do sum=$((sum+n)); done; echo $sum
- Nth CSV column: cut -d, -f3   (third field, comma-separated)
- Word frequency, top word: tr ' ' '\\n' | sort | uniq -c | sort -rn | head -1 | awk '{print $2}'
- Arithmetic: $((a+b)).  Command substitution: $(cmd).  Read loop: while read -r x; do ...; done
"""


def load_manbash():
    p = Path(os.environ.get("CLAUDE_JOB_DIR", "/tmp")) / "tmp" / "manbash.txt"
    if p.exists():
        return p.read_text(errors="ignore")
    return ""


def build_contexts():
    man = load_manbash()
    return {
        "NONE": "",
        "CHEATSHEET": CHEATSHEET,
        "MANBASH_4K": man[:16000],      # ~4k tok (pod limitem)
        "MANBASH_OVER": man[:40000],    # ~10k tok (nad limitem ~6k)
    }


def make_prompt(context: str, task_prompt: str) -> str:
    if not context:
        return task_prompt
    return f"Reference documentation:\n{context}\n\n---\nTask: {task_prompt}"


async def run_context(jc, ctx_name, ctx_text):
    results = {}  # shape -> [0/1]
    empty = 0
    total = 0
    for task in TASKS:
        k = len(task["plan"])
        budget = k + 2
        for rep in range(M):
            prompt = make_prompt(ctx_text, task["prompt"])
            rs = await jc.sample_n(prompt, budget, system_prompt=GEN_SYS, top_k=8)
            with tempfile.TemporaryDirectory() as td:
                cats = [evaluate(r.content, task, Path(td), f"{ctx_name}_{task['name']}_{rep}_{i}")
                        for i, r in enumerate(rs)]
            for r in rs:
                total += 1
                if r.ok and not r.content.strip():
                    empty += 1
            passed = 1 if "pass" in cats else 0
            results.setdefault(task["shape"], []).append(passed)
    return results, round(100 * empty / max(total, 1), 1)


async def main():
    contexts = build_contexts()
    ctx_tokens = {k: len(v) // 4 for k, v in contexts.items()}
    print("Rozmiary kontekstu (approx tok):", ctx_tokens)
    summary = {"context_tokens": ctx_tokens, "M": M, "per_context": {}}
    async with JimmyClient(max_concurrency=8) as jc:
        for name, text in contexts.items():
            res, empty_rate = await run_context(jc, name, text)
            def rate(shape):
                v = res.get(shape, [])
                return round(100 * sum(v) / len(v), 1) if v else None
            allv = res.get("sequence", []) + res.get("pipeline", [])
            overall = round(100 * sum(allv) / len(allv), 1)
            summary["per_context"][name] = {"sequence": rate("sequence"), "pipeline": rate("pipeline"),
                                            "overall": overall, "empty_response_rate": empty_rate}
            print(f"  {name:14} seq={rate('sequence')} pipe={rate('pipeline')} "
                  f"overall={overall}  empty={empty_rate}%")
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")

    base = summary["per_context"]["NONE"]["overall"]
    best_ctx = max((n for n in contexts if n != "NONE"),
                   key=lambda n: summary["per_context"][n]["overall"])
    best_val = summary["per_context"][best_ctx]["overall"]
    summary["baseline_none"] = base
    summary["best_context"] = best_ctx
    summary["best_context_overall"] = best_val
    summary["big_input_helps"] = best_val >= base + 10
    (HERE / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\n===== WERDYKT 012 =====")
    print(f"  baseline NONE overall = {base}%")
    for n in contexts:
        if n != "NONE":
            d = summary['per_context'][n]['overall'] - base
            print(f"  {n:14} = {summary['per_context'][n]['overall']}%  ({d:+.1f} pkt vs NONE)  "
                  f"empty={summary['per_context'][n]['empty_response_rate']}%")
    print(f"  DUŻY INPUT POMAGA (któryś ≥ +10 pkt): {summary['big_input_helps']}")


if __name__ == "__main__":
    asyncio.run(main())

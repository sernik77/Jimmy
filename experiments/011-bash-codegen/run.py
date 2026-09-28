"""011 — uczenie Jimmy'ego pisać bash: monolit vs dekompozycja na nieredukowalne kroki.

Ramiona (parytet budżetu, ten sam walidator = WYKONANIE):
  A  — single-shot (1 req)
  B  — best-of-N całego skryptu (k+2 próbek, pass jeśli którakolwiek przechodzi)
  C1 — dekompozycja z PLANEM DANYM przeze mnie (map k kroków + reduce składa) — sufit dekompozycji
  C2 — pełny pipeline (Jimmy planuje + map + reduce)
Zadania otagowane sequence-shaped (kroki rozdzielne) vs pipeline-shaped (kroki sprzężone).
Metryka: pass-rate po M powtórzeniach, raportowana PER KSZTAŁT.

Uruchom:  python3 experiments/011-bash-codegen/run.py            (pełny eksperyment)
          python3 experiments/011-bash-codegen/run.py --selftest (walidacja harnessu na referencjach)
"""
from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402

HERE = Path(__file__).parent
M = 5  # powtorzenia per (zadanie, ramie)

GEN_SYS = "You are a bash scripting assistant. Output a complete, correct bash script for the task."

# ---------- Zadania ----------
def fx_dircount(d: Path):
    for n in ("f1", "f2", "f3"):
        (d / n).write_text("x")
    (d / "d1").mkdir(); (d / "d2").mkdir()

def fx_extcount(d: Path):
    (d / "a.txt").write_text("1"); (d / "b.txt").write_text("2"); (d / "c.log").write_text("3")

def fx_linereport(d: Path):
    (d / "a.txt").write_text("l1\nl2\n"); (d / "b.txt").write_text("l1\nl2\nl3\n")

TASKS = [
    {"name": "seq_dircount", "shape": "sequence",
     "prompt": ("Print EXACTLY two lines for the current directory: first line 'files: N' where N is "
                "the number of regular files, second line 'dirs: M' where M is the number of "
                "subdirectories."),
     "fixture": fx_dircount, "stdin": None, "expected": "files: 3\ndirs: 2",
     "plan": ["Count regular files in the current directory and print 'files: N'",
              "Count subdirectories in the current directory and print 'dirs: M'"],
     "reference": ('echo "files: $(find . -maxdepth 1 -type f | wc -l)"\n'
                   'echo "dirs: $(find . -mindepth 1 -maxdepth 1 -type d | wc -l)"\n')},
    {"name": "seq_extcount", "shape": "sequence",
     "prompt": ("Print EXACTLY two lines: 'txt: N' where N is the number of files ending in .txt in "
                "the current directory, and 'log: M' where M is the number of files ending in .log."),
     "fixture": fx_extcount, "stdin": None, "expected": "txt: 2\nlog: 1",
     "plan": ["Count files ending in .txt and print 'txt: N'",
              "Count files ending in .log and print 'log: M'"],
     "reference": ('echo "txt: $(find . -maxdepth 1 -name \'*.txt\' | wc -l)"\n'
                   'echo "log: $(find . -maxdepth 1 -name \'*.log\' | wc -l)"\n')},
    {"name": "seq_linereport", "shape": "sequence",
     "prompt": ("Print EXACTLY two lines: 'count: N' where N is the number of .txt files in the "
                "current directory, and 'lines: L' where L is the total number of lines across all "
                ".txt files."),
     "fixture": fx_linereport, "stdin": None, "expected": "count: 2\nlines: 5",
     "plan": ["Count .txt files and print 'count: N'",
              "Sum the line counts of all .txt files and print 'lines: L'"],
     "reference": ('echo "count: $(find . -maxdepth 1 -name \'*.txt\' | wc -l)"\n'
                   'echo "lines: $(cat *.txt | wc -l)"\n')},
    {"name": "pipe_sum", "shape": "pipeline",
     "prompt": "Read integers from standard input, one per line, and print their sum (just the number).",
     "fixture": None, "stdin": "3\n5\n2\n4\n", "expected": "14",
     "plan": ["Initialize a sum variable to 0",
              "Loop over each line from stdin and add it to the sum",
              "Print the final sum"],
     "reference": 'sum=0\nwhile read -r n; do sum=$((sum+n)); done\necho $sum\n'},
    {"name": "pipe_col3", "shape": "pipeline",
     "prompt": ("Read comma-separated lines from standard input and print the THIRD field of each "
                "line, one per line."),
     "fixture": None, "stdin": "a,b,c\nd,e,f\ng,h,i\n", "expected": "c\nf\ni",
     "plan": ["Read each line from stdin",
              "Extract the third comma-separated field",
              "Print each extracted field on its own line"],
     "reference": 'cut -d, -f3\n'},
    {"name": "pipe_topword", "shape": "pipeline",
     "prompt": ("Read text from standard input and print the SINGLE most frequent whitespace-separated "
                "word. Output only that one word."),
     "fixture": None, "stdin": "apple banana apple cherry apple banana\n", "expected": "apple",
     "plan": ["Split the input into one word per line",
              "Count occurrences of each word",
              "Print the single word with the highest count"],
     "reference": "tr ' ' '\\n' | grep -v '^$' | sort | uniq -c | sort -rn | head -1 | awk '{print $2}'\n"},
]

# ---------- Harness wykonania ----------
DANGER = re.compile(r"\brm\s+-rf\b|\brm\s+-r\s+/|\bdd\b|mkfs|:\(\)\s*\{|\bsudo\b|\bcurl\b|\bwget\b|"
                    r"\bssh\b|>\s*/dev/|\bshutdown\b|\breboot\b|chmod\s+777\s+/|\bmv\s+/\s")

_CODE_TOKENS = ("echo", "for", "while", "if", "awk", "grep", "cut", "wc", "ls", "find", "sort",
                "uniq", "cat", "printf", "read", "$(", "=", "|", "tr", "head", "sed")


def extract_code(text: str) -> str:
    blocks = re.findall(r"```(?:bash|sh)?\s*\n(.*?)```", text, re.DOTALL)
    if blocks:
        return blocks[0].strip()          # PIERWSZY blok = skrypt (kolejne to przyklady uzycia)
    return text.strip()


def looks_like_code(code: str) -> bool:
    return any(t in code for t in _CODE_TOKENS)


def norm(s: str) -> str:
    return "\n".join(line.rstrip() for line in s.strip().splitlines())


def evaluate(code_text: str, task: dict, tmp: Path, idx: int) -> str:
    """Zwraca kategorie: pass / exec_fail / extract_fail / blocked."""
    if DANGER.search(code_text):
        return "blocked"
    code = extract_code(code_text)
    if not code or not looks_like_code(code):
        return "extract_fail"
    script = tmp / f"script_{idx}.sh"
    script.write_text(code)
    fixture_dir = tmp / f"fx_{idx}"
    fixture_dir.mkdir(exist_ok=True)
    for c in fixture_dir.iterdir():
        c.unlink() if c.is_file() else None
    if task["fixture"]:
        task["fixture"](fixture_dir)
    try:
        r = subprocess.run(["bash", str(script)], cwd=fixture_dir,
                           input=task["stdin"], capture_output=True, text=True, timeout=6)
    except subprocess.TimeoutExpired:
        return "exec_fail"
    return "pass" if norm(r.stdout) == norm(task["expected"]) else "exec_fail"


# ---------- Selftest: referencje MUSZĄ przejść ----------
def selftest():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        ok = True
        for i, t in enumerate(TASKS):
            cat = evaluate(t["reference"], t, tmp, i)
            print(f"  [{cat:11}] {t['name']}")
            ok = ok and cat == "pass"
        print("SELFTEST:", "OK — harness poprawny" if ok else "FAIL — napraw referencje/harness")
        return ok


# ---------- Ramiona ----------
async def arm_single(jc, task, tmp, tag):
    r = await jc.ask(task["prompt"], system_prompt=GEN_SYS, top_k=8)
    return evaluate(r.content, task, tmp, tag), 1

async def arm_bestof(jc, task, tmp, tag, budget):
    rs = await jc.sample_n(task["prompt"], budget, system_prompt=GEN_SYS, top_k=8)
    cats = [evaluate(r.content, task, tmp, f"{tag}_{i}") for i, r in enumerate(rs)]
    return ("pass" if "pass" in cats else ("exec_fail" if "exec_fail" in cats else cats[0])), budget

async def _map_reduce(jc, task, steps, tmp, tag, plan_reqs):
    step_sys = "You write ONE small bash snippet. Output only bash code, no explanation."
    step_prompts = [
        (f"Overall task: {task['prompt']}\nWrite ONLY the bash code for this single step: {s}")
        for s in steps]
    snips = await jc.map_prompts(step_prompts, system_prompt=step_sys, top_k=8)
    joined = "\n".join(f"# step {i+1}: {steps[i]}\n{extract_code(sn.content)}"
                       for i, sn in enumerate(snips))
    reduce_prompt = (f"Assemble these bash snippets into ONE complete, correct script for the task: "
                     f"{task['prompt']}\n\nSnippets:\n{joined}\n\nOutput only the final script.")
    red = await jc.ask(reduce_prompt, system_prompt=GEN_SYS, top_k=8)
    return evaluate(red.content, task, tmp, tag), plan_reqs + len(steps) + 1

async def arm_c1(jc, task, tmp, tag):
    return await _map_reduce(jc, task, task["plan"], tmp, tag, plan_reqs=0)

async def arm_c2(jc, task, tmp, tag):
    plan_sys = ("Break the task into 2-4 tiny ordered bash steps. Output each step on its own line, "
                "no numbering, no code, just short imperative descriptions.")
    pr = await jc.ask(f"Task: {task['prompt']}", system_prompt=plan_sys, top_k=8)
    steps = [ln.strip("-* ").strip() for ln in pr.content.splitlines() if ln.strip()][:5]
    if not steps:
        steps = task["plan"]
    return await _map_reduce(jc, task, steps, tmp, tag, plan_reqs=1)


async def main():
    if "--selftest" in sys.argv:
        selftest(); return
    print("Walidacja harnessu (selftest referencji):")
    if not selftest():
        print("PRZERYWAM — harness niepoprawny."); return

    results = {}  # (arm, shape) -> lista pass(0/1); + kategorie
    cat_counts = {}
    req_counts = {}
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        async with JimmyClient(max_concurrency=8) as jc:
            for task in TASKS:
                k = len(task["plan"])
                budget_B = k + 2
                for arm in ("A", "B", "C1", "C2"):
                    for rep in range(M):
                        tag = f"{task['name']}_{arm}_{rep}"
                        if arm == "A":
                            cat, nreq = await arm_single(jc, task, tmp, tag)
                        elif arm == "B":
                            cat, nreq = await arm_bestof(jc, task, tmp, tag, budget_B)
                        elif arm == "C1":
                            cat, nreq = await arm_c1(jc, task, tmp, tag)
                        else:
                            cat, nreq = await arm_c2(jc, task, tmp, tag)
                        results.setdefault((arm, task["shape"]), []).append(1 if cat == "pass" else 0)
                        cat_counts.setdefault(arm, {}).setdefault(cat, 0)
                        cat_counts[arm][cat] += 1
                        req_counts.setdefault(arm, []).append(nreq)
                print(f"  ukończono zadanie {task['name']}")
            print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")

    def rate(arm, shape):
        v = results.get((arm, shape), [])
        return round(100 * sum(v) / len(v), 1) if v else None

    import statistics
    summary = {"M": M, "per_arm_shape_passrate": {}, "category_counts": cat_counts,
               "avg_requests_per_task": {a: round(statistics.mean(req_counts[a]), 1) for a in req_counts}}
    for arm in ("A", "B", "C1", "C2"):
        summary["per_arm_shape_passrate"][arm] = {
            "sequence": rate(arm, "sequence"), "pipeline": rate(arm, "pipeline"),
            "overall": round(100 * sum(results.get((arm, s), []).count(1) for s in ("sequence", "pipeline"))
                             / sum(len(results.get((arm, s), [])) for s in ("sequence", "pipeline")), 1)}
    (HERE / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    print("\n===== WYNIKI 011 (pass-rate %) =====")
    print(f"{'ramię':4} {'sequence':>9} {'pipeline':>9} {'overall':>8}  avg_req")
    for arm in ("A", "B", "C1", "C2"):
        s = summary["per_arm_shape_passrate"][arm]
        print(f"{arm:4} {str(s['sequence']):>9} {str(s['pipeline']):>9} {str(s['overall']):>8}  "
              f"{summary['avg_requests_per_task'][arm]}")
    print("\nkategorie błędów per ramię:", json.dumps(cat_counts, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())

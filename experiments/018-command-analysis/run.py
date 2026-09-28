"""018 — cztery meta-analityczne testy na komendach (bank znanych komend z twardym goldem).

T1 describe/explain · T2 task↔command match-judge (Jimmy sędzia) · T3 compare task vs opis, flaguj różnice ·
T4 re-generate alternatywną komendę (różnorodność + walidność + równoważność wyjścia).

Uruchom: python3 experiments/018-command-analysis/run.py
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "r017", str(Path(__file__).resolve().parents[1] / "017-steps-to-commands" / "run.py"))
r017 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(r017)

HERE = Path(__file__).parent

# bank: komenda, słowa-klucze opisu (gold), poprawne zadanie, błędne zadanie
BANK = [
    {"cmd": "lsb_release -a", "kw": ["distribution", "distro", "release", "version", "linux"],
     "task": "Identify the Linux distribution and version", "wrong": "Check available disk space"},
    {"cmd": "dpkg -l | grep postgresql", "kw": ["package", "installed", "postgresql", "list", "dpkg"],
     "task": "Check if the postgresql package is installed", "wrong": "Show the current kernel version"},
    {"cmd": "systemctl status postgresql", "kw": ["service", "status", "running", "postgresql", "systemd"],
     "task": "Check whether the postgresql service is running", "wrong": "List files in the log directory"},
    {"cmd": "df -h", "kw": ["disk", "space", "filesystem", "usage", "free"],
     "task": "Check available disk space", "wrong": "Show the current logged-in user"},
    {"cmd": "free -m", "kw": ["memory", "ram", "usage", "free", "megabytes"],
     "task": "Check available memory", "wrong": "Locate the python3 binary"},
    {"cmd": "whoami", "kw": ["user", "current", "username", "logged"],
     "task": "Show the current logged-in user", "wrong": "Check available disk space"},
    {"cmd": "uname -r", "kw": ["kernel", "version", "release"],
     "task": "Show the running kernel version", "wrong": "Count the number of CPU cores"},
    {"cmd": "ps aux | grep nginx", "kw": ["process", "running", "nginx", "list"],
     "task": "Check whether the nginx process is running", "wrong": "Identify the Linux distribution"},
    {"cmd": "nproc", "kw": ["cpu", "cores", "processors", "number"],
     "task": "Count the number of CPU cores", "wrong": "Check whether nginx is running"},
    {"cmd": "which python3", "kw": ["locate", "path", "python3", "binary", "executable"],
     "task": "Locate the python3 executable", "wrong": "Show available memory"},
    {"cmd": "cat /etc/os-release", "kw": ["os", "release", "distribution", "version", "operating"],
     "task": "Show operating system release information", "wrong": "Check if postgresql is installed"},
    {"cmd": "id -un", "kw": ["user", "current", "username", "name"],
     "task": "Print the current user name", "wrong": "Show the running kernel version"},
]

DESC_SYS = "Explain what a shell command does in ONE clear sentence. Be specific and accurate. Output only the sentence."
JUDGE_SYS = ("Decide if the shell command correctly accomplishes the task. Answer with EXACTLY one word: "
             "MATCH or MISMATCH. Output only that word.")
DIFF_SYS = ("Compare the intended task with what the command actually does. If they align, output 'ALIGNED'. "
            "If they differ, output 'DIFFERS:' followed by the difference in a few words. Output only that.")
ALT_SYS = ("You are a Linux expert. Given a shell command, output ONE different command that achieves the SAME "
           "result by a DIFFERENT method. Output only the command, no explanation, no backticks.")


def run_ro(cmd: str):
    try:
        with tempfile.TemporaryDirectory() as td:
            r = subprocess.run(["bash", "-c", cmd], cwd=td, capture_output=True, text=True, timeout=6)
        return r.stdout.strip() if r.returncode != 127 else None
    except Exception:
        return None


def toks(s: str):
    return set(re.findall(r"[a-z0-9]+", (s or "").lower()))


async def main():
    async with JimmyClient(max_concurrency=8) as jc:
        # ===== T1: describe/explain =====
        descs = await jc.map_prompts([f"Command: {b['cmd']}" for b in BANK], system_prompt=DESC_SYS, top_k=8)
        t1 = []
        for b, d in zip(BANK, descs):
            dl = d.content.lower() if d.ok else ""
            recall = sum(1 for k in b["kw"] if k in dl) / len(b["kw"])
            lead = r017.leading_cmds(b["cmd"])[0].split("/")[-1]
            faithful = lead in dl or any(k in dl for k in b["kw"][:2])
            t1.append({"cmd": b["cmd"], "recall": round(recall, 2), "faithful": faithful, "desc": d.content.strip()})
        t1_recall = round(sum(x["recall"] for x in t1) / len(t1), 3)
        t1_faith = round(sum(1 for x in t1 if x["faithful"]) / len(t1), 3)

        # ===== T2: match-judge (correct + mismatch pary), głosowanie-5 =====
        pairs = [(b["task"], b["cmd"], "MATCH") for b in BANK] + \
                [(b["wrong"], b["cmd"], "MISMATCH") for b in BANK]
        async def judge(task, cmd):
            rs = await jc.sample_n(f"Task: {task}\nCommand: {cmd}", 5, system_prompt=JUDGE_SYS, top_k=8)
            votes = [("MATCH" if "MATCH" in r.content.upper() and "MISMATCH" not in r.content.upper()
                      else "MISMATCH") for r in rs if r.ok]
            return Counter(votes).most_common(1)[0][0] if votes else "?"
        judged = await asyncio.gather(*[judge(t, c) for t, c, _ in pairs])
        correct = [j == g for (_, _, g), j in zip(pairs, judged)]
        n = len(BANK)
        t2_acc = round(sum(correct) / len(correct), 3)
        t2_match_recall = round(sum(correct[:n]) / n, 3)       # wykrywa poprawne
        t2_mismatch_recall = round(sum(correct[n:]) / n, 3)    # wykrywa niedopasowane

        # ===== T3: compare task vs opis-komendy, flaguj różnice =====
        # użyj opisów z T1; dla correct-task oczekuj ALIGNED, dla wrong-task DIFFERS
        async def diff(task, desc):
            r = await jc.ask(f"Task: {task}\nWhat the command does: {desc}", system_prompt=DIFF_SYS, top_k=8)
            return "ALIGNED" if "ALIGN" in r.content.upper() and "DIFFER" not in r.content.upper() else "DIFFERS"
        t3_pairs = [(b["task"], t1[i]["desc"], "ALIGNED") for i, b in enumerate(BANK)] + \
                   [(b["wrong"], t1[i]["desc"], "DIFFERS") for i, b in enumerate(BANK)]
        t3_res = await asyncio.gather(*[diff(t, d) for t, d, _ in t3_pairs])
        t3_correct = [r == g for (_, _, g), r in zip(t3_pairs, t3_res)]
        t3_acc = round(sum(t3_correct) / len(t3_correct), 3)
        t3_differs_recall = round(sum(t3_correct[n:]) / n, 3)

        # ===== T4: re-generate alternatywną komendę =====
        t4 = []
        for b in BANK:
            cands = await jc.sample_n(f"Command: {b['cmd']}", 5, system_prompt=ALT_SYS, top_k=8)
            alts = [r017.extract_cmd(c.content) for c in cands if c.ok]
            orig_out = run_ro(b["cmd"])
            best = None
            for alt in alts:
                if not alt or toks(alt) == toks(b["cmd"]):
                    continue
                if not r017.bash_syntax_ok(alt) or not r017.real_command(alt) or r017.DANGER.search(alt):
                    continue
                # równoważność wyjścia (read-only)
                if r017.is_read_only(b["cmd"], alt):
                    alt_out = run_ro(alt)
                    equiv = alt_out is not None and orig_out is not None and (
                        alt_out == orig_out or
                        (len(toks(orig_out)) > 0 and len(toks(alt_out) & toks(orig_out)) / max(len(toks(orig_out)), 1) >= 0.5))
                else:
                    equiv = None
                best = {"alt": alt, "different": True, "valid_real": True, "equiv": equiv}
                if equiv:
                    break
            t4.append({"cmd": b["cmd"], **(best or {"alt": None, "different": False, "valid_real": False, "equiv": False})})
        t4_diverse = round(sum(1 for x in t4 if x["different"]) / len(t4), 3)
        t4_valid = round(sum(1 for x in t4 if x["valid_real"]) / len(t4), 3)
        equivable = [x for x in t4 if x["equiv"] is not None]
        t4_equiv = round(sum(1 for x in equivable if x["equiv"]) / len(equivable), 3) if equivable else None

        print(f"[client] requests={jc.n_requests} errors={jc.n_errors}")

    out = {
        "T1_describe": {"keyconcept_recall": t1_recall, "faithful_rate": t1_faith, "samples": t1[:12]},
        "T2_match_judge": {"accuracy": t2_acc, "match_recall": t2_match_recall,
                           "mismatch_recall": t2_mismatch_recall, "n_pairs": len(pairs)},
        "T3_compare_diff": {"accuracy": t3_acc, "differs_recall": t3_differs_recall},
        "T4_regenerate": {"diverse_alt_rate": t4_diverse, "valid_real_rate": t4_valid,
                          "output_equivalence_rate": t4_equiv, "samples": t4},
    }
    (HERE / "summary.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print("\n===== WYNIKI 018 =====")
    print(f"T1 DESCRIBE:   key-concept recall={t1_recall}  faithful={t1_faith}")
    print(f"T2 MATCH-JUDGE: accuracy={t2_acc}  (match-recall={t2_match_recall}, MISmatch-recall={t2_mismatch_recall})")
    print(f"T3 COMPARE-DIFF: accuracy={t3_acc}  (differs-recall={t3_differs_recall})")
    print(f"T4 REGENERATE: diverse={t4_diverse}  valid+real={t4_valid}  output-equiv={t4_equiv}")
    print("\n  T1 przykłady opisów:")
    for x in t1[:4]:
        print(f"    {x['cmd']:28} → {x['desc'][:70]}")
    print("  T4 przykłady alternatyw:")
    for x in t4[:6]:
        if x["alt"]:
            eq = {True: "≡", False: "≠", None: "?"}[x["equiv"]]
            print(f"    {x['cmd']:28} →[{eq}] {x['alt'][:45]}")


if __name__ == "__main__":
    asyncio.run(main())

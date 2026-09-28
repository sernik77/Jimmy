"""017 — generowanie prawdziwych komend shell dla kroków z 016 (wersja ~49 kroków, depth-2 defensive).

Bezpieczeństwo: READ-ONLY kroki wykonujemy w sandboxie (allowlist + blocklist + timeout);
MUTUJĄCE oceniamy tylko statycznie. Metryki: bash -n, real-command, safe-exec, + artefakty.
Arms: SINGLE (1 komenda) vs BESTOFN (N + filtr: valid∧real∧(exec dla read-only)).

Uruchom: python3 experiments/017-steps-to-commands/run.py
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402

# import 016 dla dekompozycji
_spec = importlib.util.spec_from_file_location(
    "r016", str(Path(__file__).resolve().parents[1] / "016-recursive-decomposition" / "run.py"))
r016 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(r016)

HERE = Path(__file__).parent
N = 5

CMD_SYS = ("You are a Linux bash expert. For the given task step, output exactly ONE real shell command "
           "that accomplishes it on a Linux system. Output ONLY the command — no explanation, no "
           "markdown, no backticks, no comments.")

READ_ONLY_VERBS = re.compile(r"\b(verify|check|identify|confirm|inspect|determine|detect|examine|"
                             r"review|assess|ensure|list|find|obtain|is |are )", re.IGNORECASE)
MUTATING_HINT = re.compile(r"\b(install|edit|set|create|configure|add|remove|delete|start|stop|"
                           r"grant|modify|write|change|update|restart|enable)\b", re.IGNORECASE)

# allowlista dowódców read-only do WYKONANIA (każdy segment pipe musi zaczynać się od tych)
RO_ALLOW = {"cat", "ls", "grep", "egrep", "fgrep", "which", "command", "type", "dpkg", "rpm",
            "ps", "test", "[", "echo", "uname", "lsb_release", "hostnamectl", "find", "stat",
            "wc", "head", "tail", "id", "whoami", "env", "printenv", "apt-cache", "pg_isready",
            "psql", "pg_config", "systemctl", "service", "getent", "awk", "sed", "cut", "sort",
            "uniq", "tr", "true", "false", "pgrep", "df", "free", "lscpu", "nproc", "date",
            "readlink", "basename", "dirname", "file", "ldd", "dpkg-query", "rpm", "snap", "dnf",
            "yum", "pacman", "apt", "column", "tee", "xargs"}
# blocklista twarda (nigdy nie wykonuj)
DANGER = re.compile(r"\brm\s|-rf|\bdd\b|mkfs|:\(\)|\bsudo\b|\bcurl\b|\bwget\b|>\s*/|\bmv\s+/|"
                    r"\binstall\b|\bcreateuser\b|\buseradd\b|systemctl\s+(start|stop|restart|enable)|"
                    r"\bservice\b.*\b(start|stop|restart)|\bkill\b|shutdown|reboot|>\s*/dev")


def extract_cmd(text: str) -> str:
    t = re.sub(r"```(?:bash|sh)?", "", text).replace("```", "").strip()
    for line in t.splitlines():
        line = line.strip().lstrip("$").strip()
        if line and not line.startswith("#"):
            return line
    return ""


def bash_syntax_ok(cmd: str) -> bool:
    try:
        r = subprocess.run(["bash", "-n"], input=cmd, capture_output=True, text=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def leading_cmds(cmd: str):
    segs = re.split(r"[|;&]{1,2}", cmd)
    heads = []
    for s in segs:
        s = s.strip().lstrip("(").strip()
        m = re.match(r"([\w./\[-]+)", s)
        if m:
            heads.append(m.group(1))
    return heads


def real_command(cmd: str) -> bool:
    heads = leading_cmds(cmd)
    if not heads:
        return False
    for h in heads:
        base = h.split("/")[-1]
        if base in RO_ALLOW:
            continue
        # sprawdź w systemie
        try:
            if subprocess.run(["bash", "-lc", f"command -v {base}"], capture_output=True,
                              timeout=5).returncode == 0:
                continue
        except Exception:
            pass
        return False
    return True


def is_read_only(step: str, cmd: str) -> bool:
    if DANGER.search(cmd):
        return False
    heads = leading_cmds(cmd)
    return bool(heads) and all(h.split("/")[-1] in RO_ALLOW for h in heads) \
        and not MUTATING_HINT.search(cmd)


def safe_exec(cmd: str) -> bool:
    """Wykonaj read-only komendę; sukces = działa (returncode != 127, brak timeoutu)."""
    try:
        with tempfile.TemporaryDirectory() as td:
            r = subprocess.run(["bash", "-c", cmd], cwd=td, capture_output=True, text=True, timeout=6)
        return r.returncode != 127  # 127 = command not found; inne (0/1/2..) = działa
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def classify_step(step: str) -> str:
    if MUTATING_HINT.search(step) and not READ_ONLY_VERBS.search(step.split(":")[0]):
        return "mutating"
    return "read_only" if READ_ONLY_VERBS.search(step) else "mutating"


def score_cmd(step, cmd, step_class):
    valid = bash_syntax_ok(cmd)
    real = real_command(cmd) if valid else False
    ro = is_read_only(step, cmd)
    execok = safe_exec(cmd) if (valid and ro and step_class == "read_only") else None
    return {"cmd": cmd, "valid": valid, "real": real, "read_only_safe": ro, "exec_ok": execok}


async def gen_steps(jc):
    r016.MAX_DEPTH = 2; r016.MAX_NODES = 55
    leaves, _ = await r016.recursive_decompose(jc, r016.DEFENSIVE_SYS)
    a = r016.analyze_leaves(leaves)
    steps = [s for s in a["unique_leaves"] if len(s.split()) >= 2][:49]
    return steps


async def main():
    async with JimmyClient(max_concurrency=8) as jc:
        steps = await gen_steps(jc)
        (HERE / "steps.json").write_text(json.dumps(steps, ensure_ascii=False, indent=2))
        print(f"Kroków: {len(steps)}")
        classes = [classify_step(s) for s in steps]
        n_ro = classes.count("read_only")
        print(f"  read-only: {n_ro}, mutating: {len(steps)-n_ro}")

        # SINGLE-shot komenda per krok
        single = await jc.map_prompts([f"Step: {s}" for s in steps], system_prompt=CMD_SYS, top_k=8)
        single_scored = [score_cmd(s, extract_cmd(r.content), c)
                         for s, r, c in zip(steps, single, classes)]

        # BEST-of-N: N komend per krok, wybierz najlepszą (valid∧real∧(exec dla RO))
        bestofn_scored = []
        artifacts = []
        for s, c in zip(steps, classes):
            cands = await jc.sample_n(f"Step: {s}", N, system_prompt=CMD_SYS, top_k=8)
            scored = [score_cmd(s, extract_cmd(x.content), c) for x in cands]
            def rank(sc):
                return (sc["valid"], sc["real"], sc["exec_ok"] is True, sc["read_only_safe"])
            best = max(scored, key=rank)
            bestofn_scored.append(best)
            artifacts.append({"step": s, "class": c, "cmd": best["cmd"],
                              "valid": best["valid"], "real": best["real"], "exec_ok": best["exec_ok"]})
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")

    def rate(scored, key, cond=lambda x: True):
        vals = [x[key] for x in scored if cond(x)]
        vals = [v for v in vals if v is not None]
        return round(sum(1 for v in vals if v) / len(vals), 3) if vals else None

    ro_steps = lambda sc: sc["read_only_safe"]
    summary = {"n_steps": len(steps), "n_read_only": n_ro,
        "SINGLE": {"valid": rate(single_scored, "valid"), "real": rate(single_scored, "real"),
                   "exec_ok_among_RO": rate(single_scored, "exec_ok")},
        "BESTOFN": {"valid": rate(bestofn_scored, "valid"), "real": rate(bestofn_scored, "real"),
                    "exec_ok_among_RO": rate(bestofn_scored, "exec_ok")},
        "artifacts": artifacts}
    (HERE / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    print("\n===== WYNIKI 017 =====")
    print(f"{'metryka':22} {'SINGLE':>8} {'BEST-of-N':>10}")
    for k, label in [("valid", "syntaktyka bash -n"), ("real", "real-command"),
                     ("exec_ok_among_RO", "exec-ok (read-only)")]:
        print(f"{label:22} {str(summary['SINGLE'][k]):>8} {str(summary['BESTOFN'][k]):>10}")
    keep = (summary["BESTOFN"]["valid"] or 0) >= 0.9 and (summary["BESTOFN"]["real"] or 0) >= 0.85 and \
           (summary["BESTOFN"]["exec_ok_among_RO"] or 0) >= 0.8
    print(f"\n  KEEP (BESTOFN valid≥0.9, real≥0.85, exec≥0.8): {keep}")
    print("\n  --- PRZYKŁADOWE KOMENDY (best-of-N) ---")
    for a in artifacts[:22]:
        ex = {True: "▶ok", False: "▶fail", None: "  (mut)"}[a["exec_ok"]]
        print(f"   [{'v' if a['valid'] else 'x'}{'r' if a['real'] else '-'}{ex:>7}] {a['step'][:38]:38} → {a['cmd'][:55]}")


if __name__ == "__main__":
    asyncio.run(main())

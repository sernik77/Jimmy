"""020 — ArchWiki (systemd) → manpage kompatybilny z man. Pipeline chunk→map→deterministyczny troff.

Arm A: Jimmy emituje troff wprost (kruche). Arm B: Jimmy wydobywa treść, Python składa poprawny troff.
Walidacja: groff -man renderuje bez błędu, sekcje man obecne, NAME poprawny, faithfulness.

Uruchom: python3 experiments/020-archwiki-to-manpage/run.py
"""
from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402

HERE = Path(__file__).parent
SRC = Path("/home/silverx/Projects-4/INTELLIGENCE/SCRAPED-DATA/systemd-archwiki.txt")
PROG = "systemd"


def load_src():
    return SRC.read_text(errors="ignore")


def chunks(text, size=11000):
    return [text[i:i+size] for i in range(0, len(text), size)]


def toks(s):
    return set(re.findall(r"[a-z0-9]+", (s or "").lower()))


# ---------- deterministyczne: SEE ALSO (regex) + escape troff ----------
def extract_seealso(text):
    refs = re.findall(r"\b([a-z][a-z0-9_.-]+)\((\d)\)", text)
    seen, out = set(), []
    for name, sec in refs:
        key = f"{name}({sec})"
        if key not in seen and name != PROG:
            seen.add(key); out.append((name, sec))
    return out[:12]


def esc(s):
    # escape troff: backslash, i wiodąca kropka/apostrof
    s = s.replace("\\", "\\e")
    lines = []
    for ln in s.splitlines():
        if ln[:1] in (".", "'"):
            ln = "\\&" + ln
        lines.append(ln)
    return "\n".join(lines).strip()


def assemble_troff(name_desc, description, commands, seealso):
    d = date.today().isoformat()
    out = [f'.TH {PROG.upper()} 1 "{d}" "jimmy-generated" "User Commands"']
    out.append(".SH NAME")
    out.append(f"{PROG} \\- {esc(name_desc)}")
    out.append(".SH DESCRIPTION")
    out.append(esc(description))
    if commands:
        out.append(".SH COMMANDS")
        for cmd, desc in commands:
            out.append(".TP")
            out.append(f".B {esc(cmd)}")
            out.append(esc(desc) or "(no description)")
    if seealso:
        out.append('.SH "SEE ALSO"')
        out.append(",\n".join(f".BR {n} ({s})" for n, s in seealso))
    return "\n".join(out) + "\n"


# ---------- walidacja ----------
def render_ok(troff_text):
    try:
        r = subprocess.run(["groff", "-man", "-Tascii", "-ww"], input=troff_text,
                           capture_output=True, text=True, timeout=15)
        rendered = r.stdout
        warnings = len([l for l in r.stderr.splitlines() if "warning" in l.lower()])
        return (r.returncode == 0 and len(rendered.strip()) > 50), warnings, rendered
    except Exception as e:
        return False, 99, str(e)


def has_sections(troff_text):
    secs = set(re.findall(r'(?m)^\.SH\s+"?([A-Z ]+)"?', troff_text))
    return {"NAME": "NAME" in secs, "DESCRIPTION": "DESCRIPTION" in secs,
            "SEE ALSO": "SEE ALSO" in secs, "n_sections": len(secs)}


def name_line_valid(troff_text):
    return bool(re.search(rf'(?m)^{PROG}\s+\\-\s+\S', troff_text))


async def main():
    src = load_src()
    ch = chunks(src)
    seealso = extract_seealso(src)  # deterministycznie
    print(f"Źródło: ~{len(src)//4} tok, {len(ch)} chunków. SEE ALSO (regex): {len(seealso)} refs.")

    out = {}
    async with JimmyClient(max_concurrency=8) as jc:
        # ===== ARM B: Jimmy treść + deterministyczny troff =====
        # NAME (jedno-linijkowy opis)
        name_r = await jc.ask(
            f"Text about '{PROG}':\n{ch[0][:6000]}\n\nWrite a concise man-page NAME description for "
            f"'{PROG}' — a single short phrase (5-10 words) describing what it is. Output ONLY the phrase.",
            system_prompt="Output only a short noun phrase, no punctuation at the end.", top_k=8)
        name_desc = name_r.content.strip().rstrip(".").split("\n")[0][:80]

        # DESCRIPTION (map chunki → reduce hierarchiczny)
        desc_sys = ("Summarize what this software is and does, factually, in 2-3 sentences. Only facts "
                    "present in the text. No markdown, no preamble.")
        desc_maps = await jc.map_prompts([f"Text:\n{c}" for c in ch[:3]], system_prompt=desc_sys, top_k=8)
        notes = "\n".join(m.content.strip() for m in desc_maps if m.ok)
        desc_r = await jc.ask(
            f"Section notes about {PROG}:\n{notes}\n\nWrite a coherent DESCRIPTION paragraph (4-6 "
            f"sentences) for a man page. Only facts from the notes. Output only the paragraph.",
            system_prompt="Output only the paragraph, no preamble.", top_k=8)
        description = desc_r.content.strip()

        # COMMANDS (map → wydobądź 'command — desc', reduce dedup)
        cmd_sys = ("Extract shell commands/subcommands mentioned and what they do. Output lines in the "
                   "form 'command :: short description'. Only commands present in the text. Nothing else.")
        cmd_maps = await jc.map_prompts([f"Text:\n{c}" for c in ch], system_prompt=cmd_sys, top_k=8)
        commands, seen = [], set()
        for m in cmd_maps:
            if not m.ok:
                continue
            for line in m.content.splitlines():
                if "::" in line:
                    cmd, _, desc = line.partition("::")
                    cmd = re.sub(r"^\s*\d+[.)]\s*", "", cmd)      # usuń numerację "1."
                    cmd = cmd.strip("-*`# ").strip()               # usuń markdown/bullety
                    if cmd and cmd.lower() not in seen and 2 <= len(cmd) <= 60:
                        seen.add(cmd.lower()); commands.append((cmd, desc.strip()[:120]))
        commands = commands[:20]

        troff_B = assemble_troff(name_desc, description, commands, seealso)
        (HERE / f"{PROG}.1").write_text(troff_B)

        # ===== ARM A: Jimmy emituje troff wprost =====
        a_r = await jc.ask(
            f"Convert this into a man page in troff/man format (use .TH, .SH NAME, .SH DESCRIPTION, "
            f".SH \"SEE ALSO\"). Program name: {PROG}.\n\nText:\n{ch[0][:6000]}\n\nOutput ONLY valid "
            f"troff man source.",
            system_prompt="You output only troff/man source, starting with .TH.", top_k=8)
        troff_A = re.sub(r"```\w*", "", a_r.content).replace("```", "").strip()
        (HERE / f"{PROG}_armA.1").write_text(troff_A + "\n")
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")

    # walidacja obu
    okB, warnB, renderedB = render_ok(troff_B)
    okA, warnA, _ = render_ok(troff_A)
    secB = has_sections(troff_B)
    faith = round(len(toks(description) & toks(src)) / max(len(toks(description)), 1), 3)

    summary = {
        "src_tokens": len(src)//4, "n_chunks": len(ch), "n_commands_extracted": len(commands),
        "n_seealso": len(seealso), "name_desc": name_desc,
        "ARM_B_hybrid": {"renders_ok": okB, "groff_warnings": warnB, "sections": secB,
                         "name_line_valid": name_line_valid(troff_B), "description_faithfulness": faith},
        "ARM_A_jimmy_troff": {"renders_ok": okA, "groff_warnings": warnA,
                              "sections": has_sections(troff_A), "name_line_valid": name_line_valid(troff_A)},
    }
    (HERE / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\n===== WYNIKI 020 =====")
    print(f"NAME: {PROG} - {name_desc}")
    print(f"ARM B (hybrid Jimmy-treść + det-troff): renders={okB} warnings={warnB} "
          f"sekcje={secB} name_ok={summary['ARM_B_hybrid']['name_line_valid']} faith={faith}")
    print(f"ARM A (Jimmy emituje troff):            renders={okA} warnings={warnA} "
          f"sekcje={has_sections(troff_A)}")
    print(f"komend wydobytych: {len(commands)}, SEE ALSO: {len(seealso)}")
    print(f"\n--- WYRENDEROWANA STRONA MAN (ARM B, pierwsze 40 linii) ---")
    print("\n".join(renderedB.splitlines()[:40]))


if __name__ == "__main__":
    asyncio.run(main())

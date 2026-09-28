"""021 — manpage → dokumentacja tldr (kompatybilna z komendą `tldr --render`).

Format tldr (Client Spec 2.3): '# name' / '> opis' + 'More information: <url>.' / bloki
'- opis:' + `komenda {{placeholder}}`. Arm A: Jimmy emituje markdown wprost. Arm B: Jimmy wydobywa
pary opis::komenda → Python składa wg spec. Walidacja: tldr --render, checker formatu, faithfulness,
pokrycie vs kanoniczna strona tldr.

Uruchom: python3 experiments/021-manpage-to-tldr/run.py
"""
from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402

HERE = Path(__file__).parent
CMDS = ["tar", "journalctl"]

FORMAT_SPEC = ("""tldr page format (Markdown):
# command-name

> Short description sentence.
> More information: <https://url>.

- Imperative example description ending with a colon:

`command --flag {{user_supplied_value}}`

- Next example description:

`command {{argument}}`

RULES: first line '# name'; then '> ' description line(s); each example is a '- ...:' line, a blank
line, then ONE line with the command in single backticks; use {{...}} for values the user fills in;
give 5-8 of the MOST COMMON, practical examples; no extra prose.""")


def get_man(cmd):
    try:
        r = subprocess.run(["bash", "-c", f"MANWIDTH=100 man {cmd} | col -b"],
                           capture_output=True, text=True, timeout=15)
        return r.stdout
    except Exception:
        return ""


def chunks(t, size=11000):
    return [t[i:i+size] for i in range(0, len(t), size)]


def canonical_tldr(cmd):
    for sub in ("common", "linux"):
        p = Path.home() / f".cache/tldr/pages/{sub}/{cmd}.md"
        if p.exists():
            return p.read_text()
    return ""


def cmd_signatures(md, cmd):
    """Sygnatury inwokacji: pierwsze 2-3 tokeny każdej komendy w backtickach (do porównania pokrycia)."""
    sigs = set()
    for m in re.findall(r"`([^`]+)`", md):
        raw = re.findall(r"[A-Za-z0-9-]+", m.replace("{{", " ").replace("}}", " "))
        toks = [t.lstrip("-") for t in raw if t.lstrip("-")]  # normalizuj: -cf ~ cf
        if toks and toks[0] == cmd:
            sig = " ".join(sorted(set(c for c in toks[1:3])))  # zbiór flag/subkomend (kolejność-niezależnie)
            sigs.add(f"{cmd} {sig}".strip())
    return sigs


def check_format(md, cmd):
    lines = md.splitlines()
    r = {}
    r["h1_ok"] = bool(lines) and lines[0].strip() == f"# {cmd}"
    r["has_desc"] = any(l.startswith("> ") for l in lines)
    # bloki przykładów
    ex = re.findall(r"(?m)^- .+:\s*\n\s*\n`[^`]+`", md)
    r["n_examples"] = len(ex)
    r["examples_ok"] = len(ex) >= 4
    r["has_placeholders"] = "{{" in md and "}}" in md
    cmd_lines = re.findall(r"`([^`]+)`", md)
    r["cmds_start_with_name"] = (sum(1 for c in cmd_lines if c.strip().startswith(cmd)) >=
                                 max(1, len(cmd_lines)//2)) if cmd_lines else False
    r["compliant"] = all([r["h1_ok"], r["has_desc"], r["examples_ok"], r["has_placeholders"]])
    return r


def render_ok(md_path):
    try:
        r = subprocess.run(["tldr", "--render", str(md_path)], capture_output=True, text=True, timeout=15)
        return r.returncode == 0 and len(r.stdout.strip()) > 30, r.stdout
    except Exception as e:
        return False, str(e)


def faithfulness(md, man_text):
    """Odsetek flag/subkomend z przykładów obecnych w manpage."""
    cmd_lines = re.findall(r"`([^`]+)`", md)
    flags = set()
    for c in cmd_lines:
        flags |= set(re.findall(r"(?<!\{)\B(--[a-z][a-z-]+)", c))       # --long
        flags |= set(re.findall(r"(?<![\w-])(-[a-zA-Z])(?![\w-])", c))  # -x
    if not flags:
        return None
    present = sum(1 for f in flags if f in man_text)
    return round(present / len(flags), 3)


def assemble_tldr(cmd, desc, url, examples):
    out = [f"# {cmd}", ""]
    out.append(f"> {desc}")
    if url:
        out.append(f"> More information: <{url}>.")
    out.append("")
    for d, c in examples:
        d = d.strip().rstrip(".").rstrip(":")
        out.append(f"- {d}:")
        out.append("")
        out.append(f"`{c.strip()}`")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def wrap_placeholders(cmd_str, cmd):
    """Lekko: owiń oczywiste argumenty (ścieżki, ALLCAPS, wartości po fladze) w {{}} jeśli brak."""
    if "{{" in cmd_str:
        return cmd_str
    toks = cmd_str.split()
    out = []
    for i, t in enumerate(toks):
        if i == 0 or t.startswith("-"):
            out.append(t)
        elif re.search(r"[/.]", t) or t.isupper() or (i > 0 and toks[i-1].startswith("-")):
            out.append("{{" + t + "}}")
        else:
            out.append(t)
    return " ".join(out)


async def main():
    results = {}
    async with JimmyClient(max_concurrency=8) as jc:
        for cmd in CMDS:
            man = get_man(cmd)
            if not man:
                continue
            ch = chunks(man)
            url_m = re.search(r"https?://[^\s>]+", man)
            url = url_m.group(0).rstrip(".") if url_m else ""

            # ---- ARM B: Jimmy treść → Python format ----
            desc_r = await jc.ask(f"Manpage excerpt:\n{ch[0][:5000]}\n\nWrite a one-sentence description "
                                  f"of the '{cmd}' command for a tldr page. Output only the sentence.",
                                  system_prompt="Output only one short sentence.", top_k=8)
            desc = desc_r.content.strip().split("\n")[0][:120]
            ex_sys = ("Give the MOST COMMON real-world usages people actually type (prefer short combined "
                      "flags, the idiomatic form — not one example per option). Output lines strictly as "
                      "'imperative description :: full command'. The description must be an imperative "
                      "phrase (e.g. 'Create an archive'), NOT a flag name. Commands must be real "
                      "invocations. Use {{placeholder}} for user-supplied values. Nothing else.")
            ex_maps = await jc.map_prompts([f"Command: {cmd}\nManpage:\n{c}" for c in ch[:4]],
                                           system_prompt=ex_sys, top_k=8)
            examples, seen = [], set()
            for m in ex_maps:
                if not m.ok:
                    continue
                for line in m.content.splitlines():
                    if "::" in line:
                        d, _, c = line.partition("::")
                        d = re.sub(r"^\s*[-*\d.]+\s*", "", d).strip()
                        c = c.strip().strip("`").strip()
                        c = wrap_placeholders(c, cmd)
                        sig = " ".join(c.split()[:3])
                        if d and c.startswith(cmd) and sig not in seen and len(d) > 3:
                            seen.add(sig); examples.append((d, c))
            examples = examples[:8]
            md_B = assemble_tldr(cmd, desc, url, examples)
            (HERE / f"{cmd}_B.md").write_text(md_B)

            # ---- ARM A: Jimmy emituje markdown wprost ----
            a_r = await jc.ask(f"{FORMAT_SPEC}\n\nNow write a tldr page for '{cmd}' based on this manpage:\n"
                               f"{ch[0][:6000]}\n\nOutput ONLY the tldr markdown.",
                               system_prompt="You output only tldr-format markdown starting with '# '.",
                               top_k=8)
            md_A = re.sub(r"```\w*", "", a_r.content).replace("```", "").strip() + "\n"
            (HERE / f"{cmd}_A.md").write_text(md_A)

            # ---- walidacja ----
            can = canonical_tldr(cmd)
            can_sigs = cmd_signatures(can, cmd)
            def eval_arm(md, path):
                ok, _ = render_ok(path)
                fc = check_format(md, cmd)
                sigs = cmd_signatures(md, cmd)
                cov = round(len(sigs & can_sigs) / len(can_sigs), 3) if can_sigs else None
                return {"renders": ok, "compliant": fc["compliant"], "n_examples": fc["n_examples"],
                        "format_detail": fc, "faithfulness": faithfulness(md, man),
                        "coverage_vs_canonical": cov}
            results[cmd] = {"ARM_B": eval_arm(md_B, HERE / f"{cmd}_B.md"),
                            "ARM_A": eval_arm(md_A, HERE / f"{cmd}_A.md"),
                            "n_canonical_examples": len(can_sigs)}
            print(f"{cmd}: B renders={results[cmd]['ARM_B']['renders']} compliant={results[cmd]['ARM_B']['compliant']} "
                  f"ex={results[cmd]['ARM_B']['n_examples']} faith={results[cmd]['ARM_B']['faithfulness']} "
                  f"cov={results[cmd]['ARM_B']['coverage_vs_canonical']}")
            print(f"     A renders={results[cmd]['ARM_A']['renders']} compliant={results[cmd]['ARM_A']['compliant']} "
                  f"ex={results[cmd]['ARM_A']['n_examples']} faith={results[cmd]['ARM_A']['faithfulness']} "
                  f"cov={results[cmd]['ARM_A']['coverage_vs_canonical']}")
        print(f"\n[client] requests={jc.n_requests} errors={jc.n_errors}")

    (HERE / "summary.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print("\n===== WYNIKI 021 (agregat) =====")
    for arm in ("ARM_B", "ARM_A"):
        rok = sum(results[c][arm]["renders"] for c in results) / len(results)
        comp = sum(results[c][arm]["compliant"] for c in results) / len(results)
        covs = [results[c][arm]["coverage_vs_canonical"] for c in results if results[c][arm]["coverage_vs_canonical"] is not None]
        fths = [results[c][arm]["faithfulness"] for c in results if results[c][arm]["faithfulness"] is not None]
        print(f"  {arm}: renders={rok:.2f} compliant={comp:.2f} "
              f"cov_vs_canonical={round(sum(covs)/len(covs),3) if covs else None} "
              f"faithfulness={round(sum(fths)/len(fths),3) if fths else None}")
    print(f"\n--- PRZYKŁAD: tar_B.md (wygenerowany) ---")
    print((HERE / "tar_B.md").read_text()[:800])


if __name__ == "__main__":
    asyncio.run(main())

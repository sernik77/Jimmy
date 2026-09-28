"""010 — analiza drzewa FS: map (klasyfikacja plików) → reduce folderowy → reduce drzewa.

Testuje rafinowane prawo z 011: reduce DETERMINISTYCZNY nie degraduje; reduce PRZEZ JIMMY'EGO
degraduje — i pyta, czy degraduje wielopoziomowo (plik→folder→drzewo).

Uruchom: python3 experiments/010-fs-tree-mapreduce/run.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402

HERE = Path(__file__).parent
CATS = ["code", "config", "docs", "data"]

# Drzewo z ground-truth. Każdy folder ma dominującą kategorię + 1 plik-szum.
TREE = {
    "code":   [("main.py", "def run():", "code"), ("app.js", "const x =", "code"),
               ("build.sh", "#!/bin/bash", "code"), ("util.py", "import os", "code"),
               ("server.go", "package main", "code"), ("README.md", "# Project", "docs")],
    "config": [("settings.yaml", "debug: true", "config"), ("app.ini", "[main]", "config"),
               ("pkg.json", '{"name":', "config"), ("cfg.toml", "[server]", "config"),
               ("env.conf", "PORT=8080", "config"), ("notes.txt", "todo later", "docs")],
    "docs":   [("guide.md", "# Guide", "docs"), ("intro.txt", "Welcome to", "docs"),
               ("api.rst", "API Reference", "docs"), ("changelog.md", "## v1.0", "docs"),
               ("faq.txt", "Q: how", "docs"), ("schema.json", '{"type":', "config")],
    "data":   [("users.csv", "id,name,age", "data"), ("sales.tsv", "date\tamount", "data"),
               ("points.csv", "x,y,z", "data"), ("log.csv", "time,event", "data"),
               ("metrics.tsv", "key\tval", "data"), ("query.sh", "#!/bin/bash", "code")],
}
FOLDER_GOLD = {f: Counter(g for _, _, g in files).most_common(1)[0][0] for f, files in TREE.items()}

CLASSIFY_SYS = (f"Classify a file into EXACTLY one category from: {', '.join(CATS)}. "
                f"Output only the single category word.")


def parse_cat(text: str) -> str:
    t = text.lower()
    for c in CATS:
        if c in t:
            return c
    return "?"


async def classify_file(jc, fname, snippet):
    # map z głosowaniem-5 (wzorzec 001)
    prompt = f"File name: {fname}\nFirst line: {snippet}\nCategory?"
    rs = await jc.sample_n(prompt, 5, system_prompt=CLASSIFY_SYS, top_k=8)
    votes = [parse_cat(r.content) for r in rs if r.ok]
    return Counter(votes).most_common(1)[0][0] if votes else "?"


async def jimmy_folder_theme(jc, fname, filenames):
    prompt = (f"A folder contains these files: {', '.join(filenames)}. "
              f"What is the folder's single theme? Answer with one word from: {', '.join(CATS)}.")
    r = await jc.ask(prompt, system_prompt=CLASSIFY_SYS, top_k=8)
    return parse_cat(r.content)


async def jimmy_tree_summary(jc, folder_summaries):
    desc = "; ".join(f"{f}: {t}" for f, t in folder_summaries.items())
    prompt = (f"A project has these folders with themes: {desc}. "
              f"List ALL distinct themes present, comma-separated, using words from: {', '.join(CATS)}.")
    r = await jc.ask(prompt, system_prompt="List categories. Output only comma-separated category words.",
                     top_k=8)
    return {c for c in CATS if c in r.content.lower()}


async def main():
    async with JimmyClient(max_concurrency=8) as jc:
        # --- MAP: klasyfikuj wszystkie pliki ---
        file_preds = {}
        map_correct = 0
        total_files = 0
        for folder, files in TREE.items():
            for fname, snippet, gold in files:
                pred = await classify_file(jc, fname, snippet)
                file_preds.setdefault(folder, []).append((fname, pred, gold))
                total_files += 1
                if pred == gold:
                    map_correct += 1
        map_acc = round(100 * map_correct / total_files, 1)

        # --- REDUCE L1 folderowy: deterministyczny vs Jimmy ---
        det_correct = jimmy_correct = 0
        folder_det = {}
        folder_jimmy = {}
        for folder, preds in file_preds.items():
            det_theme = Counter(p for _, p, _ in preds).most_common(1)[0][0]  # deterministyczny
            folder_det[folder] = det_theme
            jimmy_theme = await jimmy_folder_theme(jc, folder, [f for f, _, _ in preds])  # Jimmy
            folder_jimmy[folder] = jimmy_theme
            if det_theme == FOLDER_GOLD[folder]:
                det_correct += 1
            if jimmy_theme == FOLDER_GOLD[folder]:
                jimmy_correct += 1
        det_acc = round(100 * det_correct / len(TREE), 1)
        jimmy_acc = round(100 * jimmy_correct / len(TREE), 1)

        # --- REDUCE L2 drzewo: Jimmy na podsumowaniach Jimmy'ego ---
        gold_themes = set(FOLDER_GOLD.values())
        tree_themes = await jimmy_tree_summary(jc, folder_jimmy)
        tree_recall = round(len(tree_themes & gold_themes) / len(gold_themes), 3)

        print(f"[client] requests={jc.n_requests} errors={jc.n_errors}")

    summary = {
        "map_accuracy_L0": map_acc,
        "reduce_L1_deterministic_acc": det_acc,
        "reduce_L1_jimmy_acc": jimmy_acc,
        "reduce_L2_tree_recall_jimmy": tree_recall,
        "folder_gold": FOLDER_GOLD, "folder_det": folder_det, "folder_jimmy": folder_jimmy,
        "gold_themes": sorted(gold_themes), "tree_themes_jimmy": sorted(tree_themes),
    }
    (HERE / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\n===== WYNIKI 010 =====")
    print(f"  L0 map (klasyfikacja plików, vote-5): {map_acc}%")
    print(f"  L1 reduce DETERMINISTYCZNY (większość):  {det_acc}%")
    print(f"  L1 reduce JIMMY (podsumowanie):          {jimmy_acc}%")
    print(f"  L2 reduce drzewo JIMMY (recall tematów): {tree_recall}")
    print(f"  degradacja Jimmy-reduce vs deterministyczny (L1): {det_acc - jimmy_acc:+.1f} pkt")
    print(f"  gold folderów: {FOLDER_GOLD}")
    print(f"  Jimmy folderów: {folder_jimmy}")


if __name__ == "__main__":
    asyncio.run(main())

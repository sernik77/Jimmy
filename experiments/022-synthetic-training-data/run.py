"""022 — Jimmy jako generator syntetycznych danych treningowych (dowód przez downstream).

Zadanie: AG News (4 klasy). Trenujemy TEN SAM klasyfikator na danych z różnych źródeł
(REAL / JIMMY-IID / JIMMY-NOVELTY / FLOOR) i mierzymy macro-F1 na PRAWDZIWYM gold test.
Dwaj studenci: (A) Multinomial NB (numpy, deterministyczny bag-of-words),
(B) ICL (Jimmy jako few-shot klasyfikator). Progi pre-rejestrowane w hypothesis.md.

Wszystkie wywołania Jimmy'ego są cache'owane do JSON — re-run jest tani i deterministyczny
względem zapisanej puli.

Uruchom: python3 experiments/022-synthetic-training-data/run.py
"""
from __future__ import annotations

import asyncio
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from jimmy.client import JimmyClient  # noqa: E402

HERE = Path(__file__).parent
SEED = 22
random.seed(SEED)

# --- AG News ---
CLASS_NAME = ["World", "Sports", "Business", "SciTech"]
CLASS_DESC = [
    "world news (international politics, conflicts, diplomacy, world events)",
    "sports news (games, matches, athletes, teams, tournaments, scores)",
    "business and finance news (markets, companies, economy, earnings, deals)",
    "science and technology news (research, gadgets, software, internet, space)",
]
NC = 4

# --- rozmiary ---
N_PER_CLASS = 100            # N treningowe / klasę (dopasowane między ramionami) -> N=400
GEN_TARGET = 130            # ile Jimmy generuje / klasę (nadmiar na dedup)
GOLD_TEST_PER_CLASS = 500   # gold test dla studenta NB -> 2000
ICL_TEST_PER_CLASS = 40     # gold test dla studenta ICL -> 160
REAL_BIG_PER_CLASS = 1000   # duży realny zbiór dla diagnostyki style-gap
ICL_K_PER_CLASS = 2         # few-shot: 2/klasę -> k=8
BOOTSTRAP = 20
GEN_BATCH = 5

POOL_CACHE = HERE / "jimmy_pool.json"
SELFCHECK_CACHE = HERE / "selfcheck.json"
ICL_CACHE = HERE / "icl_preds.json"


# ============================ dane ============================
def load_agnews():
    from datasets import load_dataset
    tr = load_dataset("fancyzhx/ag_news", split="train")
    te = load_dataset("fancyzhx/ag_news", split="test")

    def bucket(ds, per_class, text_key="text"):
        by = defaultdict(list)
        for row in ds:
            by[int(row["label"])].append(row[text_key].strip())
        out = {}
        for c in range(NC):
            rng = random.Random(SEED + c)
            items = by[c][:]
            rng.shuffle(items)
            out[c] = items[:per_class]
        return out

    gold = bucket(te, GOLD_TEST_PER_CLASS)
    icl_gold = {c: gold[c][:ICL_TEST_PER_CLASS] for c in range(NC)}  # podzbiór golda
    real_train = bucket(tr, N_PER_CLASS)
    real_big = bucket(tr, REAL_BIG_PER_CLASS)
    return gold, icl_gold, real_train, real_big


# ============================ Jimmy: generacja ============================
GEN_SYS = ("You write short news snippets for a news classification dataset. "
           "Output ONLY the snippets, one per line, no numbering, no bullets, no commentary.")


def parse_snippets(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        s = line.strip()
        s = re.sub(r"^\s*(\d+[\.\)]|[-*•])\s*", "", s)  # usuń numerację/bullety
        s = s.strip().strip('"')
        if len(s.split()) >= 5 and not s.lower().startswith(("here are", "sure", "these are")):
            out.append(s)
    return out


def short_tag(s: str) -> str:
    return " ".join(s.split()[:8])


async def generate_pool(jc: JimmyClient, novelty: bool) -> dict:
    pool = {c: [] for c in range(NC)}
    for c in range(NC):
        memory: list[str] = []
        guard = 0
        while len(pool[c]) < GEN_TARGET and guard < 60:
            guard += 1
            if novelty and memory:
                mem = "; ".join(memory[-45:])
                prompt = (f"Write {GEN_BATCH} different short {CLASS_DESC[c]} snippets. "
                          f"Each: a news headline plus one sentence, single line, newswire style, "
                          f"under 40 words. You ALREADY wrote about these subjects: {mem}. "
                          f"Write {GEN_BATCH} NEW snippets about DIFFERENT subjects NOT in that list.")
            else:
                prompt = (f"Write {GEN_BATCH} different short {CLASS_DESC[c]} snippets. "
                          f"Each: a news headline plus one sentence, single line, newswire style, "
                          f"under 40 words.")
            r = await jc.ask(prompt, system_prompt=GEN_SYS, top_k=8)
            if not r.ok:
                continue
            for snip in parse_snippets(r.content):
                pool[c].append(snip)
                if novelty:
                    memory.append(short_tag(snip))
        pool[c] = pool[c][:GEN_TARGET]
    return pool


async def build_pools():
    if POOL_CACHE.exists():
        d = json.loads(POOL_CACHE.read_text())
        return ({int(k): v for k, v in d["iid"].items()},
                {int(k): v for k, v in d["novelty"].items()})
    async with JimmyClient() as jc:
        iid = await generate_pool(jc, novelty=False)
        nov = await generate_pool(jc, novelty=True)
    POOL_CACHE.write_text(json.dumps({"iid": iid, "novelty": nov}, ensure_ascii=False, indent=1))
    return iid, nov


# ============================ dedup (deterministyczny gate) ============================
def ngrams(s: str, n=4):
    toks = re.findall(r"[a-z0-9']+", s.lower())
    return set(tuple(toks[i:i+n]) for i in range(max(0, len(toks) - n + 1)))


def dedup(items: list[str], thresh=0.6) -> list[str]:
    kept, sigs = [], []
    for it in items:
        g = ngrams(it)
        dup = False
        for sg in sigs:
            if g and sg:
                j = len(g & sg) / len(g | sg)
                if j >= thresh:
                    dup = True
                    break
        if not dup:
            kept.append(it)
            sigs.append(g)
    return kept


# ============================ Student A: Multinomial NB ============================
_TOK = re.compile(r"[a-z0-9']+")


def tok(s: str):
    return _TOK.findall(s.lower())


class MultinomialNB:
    """Surowe zliczenia + add-1. Słownik budowany TYLKO na treningu. alpha=1 stałe wszędzie."""
    def __init__(self, alpha=1.0):
        self.alpha = alpha

    def fit(self, docs, labels):
        vocab = {}
        for d in docs:
            for w in tok(d):
                if w not in vocab:
                    vocab[w] = len(vocab)
        self.vocab = vocab
        V = len(vocab)
        self.V = V
        counts = [[0.0] * V for _ in range(NC)]
        cdocs = [0] * NC
        for d, y in zip(docs, labels):
            cdocs[y] += 1
            row = counts[y]
            for w in tok(d):
                row[vocab[w]] += 1.0
        n = sum(cdocs) or 1
        self.log_prior = [math.log((cdocs[c] + 1e-9) / n) if cdocs[c] else -1e9 for c in range(NC)]
        self.log_lik = []
        for c in range(NC):
            tot = sum(counts[c]) + self.alpha * V
            self.log_lik.append([math.log((counts[c][j] + self.alpha) / tot) for j in range(V)])
        return self

    def predict(self, docs):
        preds = []
        for d in docs:
            idxs = [self.vocab[w] for w in tok(d) if w in self.vocab]
            best_c, best_s = 0, -1e30
            for c in range(NC):
                ll = self.log_lik[c]
                s = self.log_prior[c] + sum(ll[i] for i in idxs)
                if s > best_s:
                    best_s, best_c = s, c
            preds.append(best_c)
        return preds


# ============================ metryki ============================
def macro_f1(y_true, y_pred):
    f1s, recs = [], []
    for c in range(NC):
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == c and p == c)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != c and p == c)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == c and p != c)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        f1s.append(f1)
        recs.append(rec)
    return sum(f1s) / NC, recs


def accuracy(y_true, y_pred):
    return sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)


def flatten(bucket):
    docs, labels = [], []
    for c in range(NC):
        for d in bucket[c]:
            docs.append(d)
            labels.append(c)
    return docs, labels


def take_per_class(bucket, k):
    return {c: bucket[c][:k] for c in range(NC)}


def eval_nb_arm(train_bucket, gold_docs, gold_labels):
    docs, labels = flatten(take_per_class(train_bucket, N_PER_CLASS))
    nb = MultinomialNB().fit(docs, labels)
    preds = nb.predict(gold_docs)
    f1, recs = macro_f1(gold_labels, preds)
    acc = accuracy(gold_labels, preds)
    # bootstrap wariancji (resampling treningu)
    boot = []
    idx_all = list(range(len(docs)))
    for b in range(BOOTSTRAP):
        rng = random.Random(1000 + b)
        bi = [rng.choice(idx_all) for _ in idx_all]
        bd = [docs[i] for i in bi]
        bl = [labels[i] for i in bi]
        p = MultinomialNB().fit(bd, bl).predict(gold_docs)
        boot.append(macro_f1(gold_labels, p)[0])
    mean = sum(boot) / len(boot)
    std = (sum((x - mean) ** 2 for x in boot) / len(boot)) ** 0.5
    return {"macro_f1": round(f1, 4), "acc": round(acc, 4),
            "per_class_recall": [round(r, 3) for r in recs],
            "boot_mean": round(mean, 4), "boot_std": round(std, 4)}


def distinct_rate(items):
    norm = [re.sub(r"\s+", " ", x.strip().lower()) for x in items]
    return len(set(norm)) / len(norm) if norm else 0.0


def vocab_size(items):
    v = set()
    for x in items:
        v.update(tok(x))
    return len(v)


# ============================ Student B: ICL (Jimmy few-shot) ============================
def parse_class(text: str):
    t = text.lower()
    for c, name in enumerate(CLASS_NAME):
        if name.lower() in t:
            return c
    # aliasy
    if "sci" in t or "tech" in t:
        return 3
    if "world" in t or "politic" in t:
        return 0
    return None


ICL_SYS = ("You are a news topic classifier. Reply with EXACTLY ONE word naming the category "
           "of the LAST snippet: World, Sports, Business, or SciTech. Output only that one word.")


def build_fewshot_history(train_bucket):
    """Few-shot jako historia wielu tur (user snippet -> assistant kategoria) — jednoznacznie
    sygnalizuje słabemu modelowi: odpowiedz tylko na najnowszą turę, nie re-klasyfikuj przykładów."""
    rng = random.Random(SEED)
    ex = []
    for c in range(NC):
        items = train_bucket[c][:]
        rng.shuffle(items)
        for s in items[:ICL_K_PER_CLASS]:
            ex.append((s, c))
    rng.shuffle(ex)
    hist = []
    for s, c in ex:
        hist.append({"role": "user", "content": f"Snippet: {s}\nCategory?"})
        hist.append({"role": "assistant", "content": CLASS_NAME[c]})
    return hist


async def icl_eval(jc, train_bucket, icl_docs, icl_labels, tag, cache):
    """train_bucket=None → zero-shot (baseline: Jimmy bez egzemplarzy; PRAWDZIWY floor dla ICL,
    bo Jimmy już umie klasyfikować newsy — 002/019)."""
    if tag in cache:
        preds = cache[tag]
    else:
        hist = [] if train_bucket is None else build_fewshot_history(train_bucket)
        tasks = [jc.ask(f"Snippet: {d}\nCategory?", system_prompt=ICL_SYS,
                        top_k=1, history=hist) for d in icl_docs]
        resps = await asyncio.gather(*tasks)
        preds = []
        for r in resps:
            c = parse_class(r.content) if r.ok else None
            preds.append(c if c is not None else -1)
        cache[tag] = preds
        ICL_CACHE.write_text(json.dumps(cache))
    f1, recs = macro_f1(icl_labels, preds)
    return {"macro_f1": round(f1, 4), "acc": round(accuracy(icl_labels, preds), 4),
            "per_class_recall": [round(r, 3) for r in recs],
            "unparsed": sum(1 for p in preds if p == -1)}


# ============================ diagnostyki Jimmy ============================
async def self_check(jc, pools):
    if SELFCHECK_CACHE.exists():
        return json.loads(SELFCHECK_CACHE.read_text())
    sys_p = "You are a news topic classifier."
    out = {}
    for name, bucket in pools.items():
        agree = 0
        total = 0
        for c in range(NC):
            docs = bucket[c][:N_PER_CLASS]
            prompts = [(f"Classify this snippet into exactly one: World, Sports, Business, SciTech.\n"
                        f"Answer with only one word.\n\nSnippet: {d}\nCategory:") for d in docs]
            resps = await jc.map_prompts(prompts, system_prompt=sys_p, top_k=1)
            for r in resps:
                total += 1
                if r.ok and parse_class(r.content) == c:
                    agree += 1
        out[name] = round(agree / total, 4) if total else 0.0
    SELFCHECK_CACHE.write_text(json.dumps(out))
    return out


# ============================ main ============================
async def main():
    print("[1] Ładuję AG News...")
    gold, icl_gold, real_train, real_big = load_agnews()
    gold_docs, gold_labels = flatten(gold)
    icl_docs, icl_labels = flatten(icl_gold)
    print(f"    gold test NB: {len(gold_docs)} | gold test ICL: {len(icl_docs)} "
          f"| real@N: {N_PER_CLASS}/klasę")

    print("[2] Generacja pul Jimmy (cache: jimmy_pool.json)...")
    iid_raw, nov_raw = await build_pools()

    # dedup deterministyczny + przytnij do N/klasę
    iid = {c: dedup(iid_raw[c]) for c in range(NC)}
    nov = {c: dedup(nov_raw[c]) for c in range(NC)}
    dedup_stats = {
        "iid": {c: [len(iid_raw[c]), len(iid[c])] for c in range(NC)},
        "novelty": {c: [len(nov_raw[c]), len(nov[c])] for c in range(NC)},
    }
    # zapewnij N/klasę (jeśli po dedupie za mało — dopełnij z raw)
    for pool, raw in ((iid, iid_raw), (nov, nov_raw)):
        for c in range(NC):
            if len(pool[c]) < N_PER_CLASS:
                extra = [x for x in raw[c] if x not in pool[c]]
                pool[c] = (pool[c] + extra)[:N_PER_CLASS]
            else:
                pool[c] = pool[c][:N_PER_CLASS]

    print("[3] Student A (Multinomial NB) — downstream na gold test...")
    floor_pred = [Counter(gold_labels).most_common(1)[0][0]] * len(gold_labels)
    nb_floor = {"macro_f1": round(macro_f1(gold_labels, floor_pred)[0], 4),
                "acc": round(accuracy(gold_labels, floor_pred), 4)}
    nb_real = eval_nb_arm(real_train, gold_docs, gold_labels)
    nb_iid = eval_nb_arm(iid, gold_docs, gold_labels)
    nb_nov = eval_nb_arm(nov, gold_docs, gold_labels)
    for name, r in [("FLOOR", nb_floor), ("REAL", nb_real), ("IID", nb_iid), ("NOVELTY", nb_nov)]:
        print(f"    {name:8s} macro-F1={r['macro_f1']}  acc={r['acc']}")

    print("[4] Diagnostyka style-gap (NB trenowany na REAL-big → pula Jimmy)...")
    big_docs, big_labels = flatten(real_big)
    nb_big = MultinomialNB().fit(big_docs, big_labels)
    stylegap = {}
    for name, pool in (("iid", iid), ("novelty", nov)):
        docs, labels = flatten(pool)
        preds = nb_big.predict(docs)
        stylegap[name] = round(accuracy(labels, preds), 4)  # zgodność z intencją wg REAL-modelu

    print("[5] Forced-4-way self-check Jimmy (cache)...")
    async with JimmyClient() as jc:
        selfchk = await self_check(jc, {"iid": iid, "novelty": nov})

        print("[6] Student B (ICL) — zero-shot baseline + few-shot z każdego ramienia...")
        icl_cache = json.loads(ICL_CACHE.read_text()) if ICL_CACHE.exists() else {}
        icl_zero = await icl_eval(jc, None, icl_docs, icl_labels, "zero", icl_cache)
        icl_real = await icl_eval(jc, real_train, icl_docs, icl_labels, "real", icl_cache)
        icl_iid = await icl_eval(jc, iid, icl_docs, icl_labels, "iid", icl_cache)
        icl_nov = await icl_eval(jc, nov, icl_docs, icl_labels, "novelty", icl_cache)
    icl_floor_pred = [Counter(icl_labels).most_common(1)[0][0]] * len(icl_labels)
    icl_floor = {"macro_f1": round(macro_f1(icl_labels, icl_floor_pred)[0], 4)}

    # bootstrap SE po itemach testowych ICL (160 itemów, mały gold -> pokaż nieoznaczoność)
    def icl_boot_se(tag):
        preds = icl_cache[tag]
        n = len(preds)
        vals = []
        for b in range(200):
            rng = random.Random(7000 + b)
            bi = [rng.randrange(n) for _ in range(n)]
            vals.append(macro_f1([icl_labels[i] for i in bi], [preds[i] for i in bi])[0])
        m = sum(vals) / len(vals)
        return round((sum((x - m) ** 2 for x in vals) / len(vals)) ** 0.5, 4)
    icl_se = {t: icl_boot_se(t) for t in ("zero", "real", "iid", "novelty")}

    # różnorodność
    diversity = {
        "iid": {"distinct": round(distinct_rate(flatten(iid)[0]), 4), "vocab": vocab_size(flatten(iid)[0])},
        "novelty": {"distinct": round(distinct_rate(flatten(nov)[0]), 4), "vocab": vocab_size(flatten(nov)[0])},
        "real": {"distinct": round(distinct_rate(flatten(take_per_class(real_train, N_PER_CLASS))[0]), 4),
                 "vocab": vocab_size(flatten(take_per_class(real_train, N_PER_CLASS))[0])},
    }

    def gap_closure(f1_j, f1_floor, f1_real):
        denom = f1_real - f1_floor
        return round((f1_j - f1_floor) / denom, 3) if denom > 0 else None

    # NB floor = majority (untrained bag-of-words nic nie wie). ICL floor = ZERO-SHOT
    # (Jimmy już umie klasyfikować newsy — majority byłby nieuczciwym floorem).
    G = {
        "nb_iid": gap_closure(nb_iid["macro_f1"], nb_floor["macro_f1"], nb_real["macro_f1"]),
        "nb_novelty": gap_closure(nb_nov["macro_f1"], nb_floor["macro_f1"], nb_real["macro_f1"]),
        "icl_iid_vs_zeroshot": gap_closure(icl_iid["macro_f1"], icl_zero["macro_f1"], icl_real["macro_f1"]),
        "icl_novelty_vs_zeroshot": gap_closure(icl_nov["macro_f1"], icl_zero["macro_f1"], icl_real["macro_f1"]),
    }

    summary = {
        "task": "AG News 4-class; N=400 (100/class) matched",
        "sizes": {"gold_nb": len(gold_docs), "gold_icl": len(icl_docs), "N_per_class": N_PER_CLASS},
        "student_A_NB": {"FLOOR": nb_floor, "REAL": nb_real, "IID": nb_iid, "NOVELTY": nb_nov},
        "student_B_ICL": {"FLOOR_majority": icl_floor, "ZERO_SHOT": icl_zero, "REAL": icl_real,
                          "IID": icl_iid, "NOVELTY": icl_nov, "boot_se": icl_se},
        "gap_closure_G": G,
        "diversity": diversity,
        "dedup_stats": dedup_stats,
        "style_gap_agreement_realmodel": stylegap,
        "self_check_forced4way": selfchk,
        "thresholds": {"ok": 0.50, "good": 0.75, "mode_collapse_distinct": 0.90},
    }
    (HERE / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\n=== GAP CLOSURE G (próg ok=0.50, dobry=0.75) ===")
    for k, v in G.items():
        print(f"    {k:14s} G={v}")
    print("\n=== DIVERSITY (mode collapse < 0.90) ===")
    for k, v in diversity.items():
        print(f"    {k:8s} distinct={v['distinct']} vocab={v['vocab']}")
    print(f"\n    style-gap agreement (REAL-model→Jimmy): {stylegap}")
    print(f"    self-check forced-4way: {selfchk}")
    print(f"\nZapisano summary.json")


if __name__ == "__main__":
    asyncio.run(main())

"""jimmy.eval — deterministyczne funkcje oceny (tanie weryfikatory).

Teza projektu: glupota Jimmy'ego jest kompensowalna wolumenem tam, gdzie
weryfikacja jest tansza niz generacja. Te funkcje to owe tanie weryfikatory.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any, Callable, Optional


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def exact_match(pred: str, gold: str) -> bool:
    return normalize(pred) == normalize(gold)


def contains(pred: str, gold: str) -> bool:
    return normalize(gold) in normalize(pred)


def extract_json(text: str) -> Optional[Any]:
    """Wyluskaj pierwszy poprawny obiekt/tablice JSON z tekstu (Jimmy lubi gadac wokol)."""
    # sprobuj cale
    text = text.strip()
    for candidate in _json_candidates(text):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def _json_candidates(text: str):
    yield text
    # blok w ```json ... ```
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if m:
        yield m.group(1).strip()
    # pierwszy zbalansowany {...} lub [...]
    for open_c, close_c in (("{", "}"), ("[", "]")):
        start = text.find(open_c)
        if start == -1:
            continue
        depth = 0
        for i in range(start, len(text)):
            if text[i] == open_c:
                depth += 1
            elif text[i] == close_c:
                depth -= 1
                if depth == 0:
                    yield text[start : i + 1]
                    break


def is_valid_json(text: str) -> bool:
    return extract_json(text) is not None


def json_matches_schema(text: str, required_keys: list[str]) -> bool:
    obj = extract_json(text)
    if not isinstance(obj, dict):
        return False
    return all(k in obj for k in required_keys)


def majority_vote(preds: list[str], normalizer: Callable[[str], str] = normalize) -> tuple[str, int, int]:
    """Zwroc (zwycieska_odpowiedz_znormalizowana, liczba_glosow, laczna_liczba)."""
    if not preds:
        return "", 0, 0
    normed = [normalizer(p) for p in preds]
    c = Counter(normed)
    winner, votes = c.most_common(1)[0]
    return winner, votes, len(preds)


def distinct_rate(outputs: list[str], normalizer: Callable[[str], str] = normalize) -> float:
    """Odsetek unikalnych wyjsc — miara roznorodnosci (kluczowe dla best-of-N)."""
    if not outputs:
        return 0.0
    normed = [normalizer(o) for o in outputs]
    return len(set(normed)) / len(normed)


def filter_by_checker(outputs: list[str], checker: Callable[[str], bool]) -> list[str]:
    """Zostaw tylko wyjscia przechodzace tani deterministyczny test."""
    return [o for o in outputs if checker(o)]


def accuracy(preds: list[str], golds: list[str], match: Callable[[str, str], bool] = exact_match) -> float:
    if not preds:
        return 0.0
    hits = sum(1 for p, g in zip(preds, golds) if match(p, g))
    return hits / len(preds)


# --- Detektory "cichej porazki": ok=True, a odpowiedz i tak bezuzyteczna ---
# Uzasadnienie (Faza 0 / CHARACTERIZATION.md): >=8k prefill -> pusta odpowiedz bez bledu HTTP;
# 4-6k kontekst -> Jimmy odmawia ("I can't fulfill...") albo ignoruje instrukcje.
_REFUSAL_MARKERS = (
    "i can't fulfill", "i cannot fulfill", "i can't help", "i cannot help",
    "i can't assist", "i cannot assist", "i can't provide", "i cannot provide",
    "i'm not able to", "i am not able to", "i'm unable to", "i am unable to",
    "i can't create", "i cannot create", "i won't be able to",
)


def is_blank(text: str) -> bool:
    """Pusta / bialoznakowa odpowiedz (typowy objaw przekroczenia limitu kontekstu)."""
    return not text or not text.strip()


def looks_like_refusal(text: str) -> bool:
    """Heurystyka: odpowiedz zaczyna sie / jest zdominowana przez formulke odmowy."""
    head = normalize(text)[:160]
    return any(m in head for m in _REFUSAL_MARKERS)


def is_usable(text: str) -> bool:
    """Tani wspolny test: odpowiedz nie jest ani pusta, ani odmowa."""
    return not is_blank(text) and not looks_like_refusal(text)

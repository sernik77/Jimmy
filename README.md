# JIMMY

Badanie praktycznych zastosowań **Jimmy'ego** — darmowego, nielimitowanego chatbota opartego na
`llama3.1-8B`, serwowanego z wyspecjalizowanego sprzętu (`chatjimmy.ai`), z inferencją ~13k t/s.

**Metoda:** propose → evaluate → **dispose** → repeat → note. Każdy eksperyment produkuje *liczbę*
względem zadeklarowanego progu, nie opinię.

**Teza projektu:** Jimmy jest głupi per-próbka, ale niemal darmowy per-próbka. Zatem —
*głupota jest kompensowalna wolumenem wszędzie tam, gdzie weryfikacja jest tańsza niż generacja.*
Dźwignią jest **współbieżność** (~38 req/s), nie prędkość modelu (sieć dominuje: RTT ~134 ms).

**Święty Graal:** nieskończona pętla oparta na Jimmym z właściwościami emergentnymi.

## Struktura
```
jimmy/client.py     # jedyne miejsce z HTTP: pula async, limit współbieżności, retry, parsowanie <|stats|>
jimmy/eval.py       # tanie deterministyczne weryfikatory: JSON, exact-match, głosowanie, distinct-rate
experiments/NNN-*/  # hypothesis.md · run.py · results.jsonl · verdict.md
CHARACTERIZATION.md # zmierzone własności Jimmy'ego (Faza 0)
LOG.md              # append-only dziennik propose/evaluate/dispose
```

## Polityka "kochamy Jimmy'ego, nie nadużywamy"
Wymuszona w kodzie, nie w intencjach: `MAX_CONCURRENCY=8` (zmierzony punkt 0 błędów),
`RPM_CEILING=2000`, retry×3 z backoffem.

## Szybki start
```bash
python3 -m jimmy.client                          # smoke-test
python3 experiments/000-characterization/run.py  # Faza 0
```

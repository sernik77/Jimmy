# tools — praktyczne implementacje Jimmy'ego jako komendy shellowe

Katalog na narzędzia, które biorą **zwalidowany w `experiments/` wzorzec** i pakują go w komendę
używalną jak zwykły program uniksowy: wejście z pliku(-ów) lub **stdin**, wynik na **stdout**,
postęp/telemetria/ostrzeżenia na **stderr** (żeby stdout został czysty do pipe'ów). Kod dzieli tę
samą bibliotekę co eksperymenty (`jimmy/client.py`, `jimmy/eval.py`) — cała polityka użycia
(`MAX_CONCURRENCY=8`, retry, limit topK) obowiązuje tu tak samo.

Różnica względem `experiments/`: eksperyment produkuje **liczbę względem progu** (KEEP/DISPOSE);
narzędzie produkuje **użyteczny wynik** dla realnego zadania. Narzędzie powstaje dopiero, gdy
odpowiadający wzorzec ma werdykt KEEP.

## Konwencje

- Uruchamialne wprost (`#!/usr/bin/env python3`, `chmod +x`) i przez `python3 tools/<nazwa>.py`.
- Wejście: pozycyjne pliki **albo** stdin (dla pipe'ów). Wejście nietekstowe konwertuj wcześniej
  (`pdftotext plik.pdf - | tools/<nazwa>.py`).
- Wyjście na stdout; `--json` dla trybu skryptowalnego; wszystko diagnostyczne na stderr.
- Kody wyjścia: `0` sukces, `1` porażka/część fragmentów zawiodła pod `--strict`, `2` błąd użycia.
- Wykrywaj **ciche porażki** (API zwraca `ok=True` mimo bezużytecznej odpowiedzi): pusta odpowiedź
  i odmowa przez `jimmy.eval.is_usable`; ciche obcięcie kontekstu przez `prefill_tokens` ze statsów.

## Narzędzia

### `summarize.py` — sumaryzacja dokumentu dowolnej długości
Wzorzec: `experiments/004` (map-reduce bije limit kontekstu) + `experiments/013` (map niezawodny,
reduce hierarchiczny, twarde reguły rządzą formatem).

```bash
tools/summarize.py raport.txt                       # domyślne: bullety, ~250 słów
cat raport.txt | tools/summarize.py --style tldr
tools/summarize.py ksiazka.txt --map-only > notatki.md   # pełne notatki bez straty pokrycia
pdftotext doc.pdf - | tools/summarize.py --focus "liczby, ryzyka" --language polish
tools/summarize.py *.md --json --strict             # skryptowalnie, twardo na błędach
```

Kluczowe flagi: `--style {bullets,prose,tldr,outline}`, `--max-words`, `--max-bullets`,
`--chunk-words`, `--batch-size`, `--top-k` (1 = deterministyczny + `--cache`), `--focus`,
`--language`, `--map-only`, `--force-mapreduce`, `--json`, `--strict`, `--dry-run`, `-v`.
Pełna lista: `tools/summarize.py --help`.

**Uwaga o pokryciu:** domyślne zwięzłe streszczenie (~250 słów) świadomie **gubi tematy
peryferyjne** (013: ~1/3 pokrycia przy silnej kompresji — to tradeoff kompresja↔pokrycie, nie błąd).
Po pełne, bezstratne notatki użyj `--map-only`.

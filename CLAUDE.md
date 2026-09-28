# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Czym jest ten projekt

Projekt badawczy, nie produkt. Bada praktyczne zastosowania **Jimmy'ego** — darmowego,
nielimitowanego API `llama3.1-8B` (`https://chatjimmy.ai/api/chat`, inferencja ~13k t/s).
Teza: *Jimmy jest głupi per-próbka, ale niemal darmowy per-próbka — więc głupota jest
kompensowalna wolumenem wszędzie tam, gdzie weryfikacja jest tańsza niż generacja.* Dźwignią
jest **współbieżność** (~38 req/s), nie prędkość modelu (dominuje sieć: RTT ~134 ms).

Nie jest to repozytorium git. Jedyna zależność runtime to `httpx` (Python 3.14 w środowisku).

## Uruchamianie

```bash
python3 -m jimmy.client                              # smoke-test klienta (1 request)
python3 experiments/NNN-nazwa/run.py                 # pełny eksperyment
```

Eksperymenty uruchamia się z korzenia repo — każdy `run.py` sam dopina korzeń do `sys.path`
(`sys.path.insert(0, parents[2])`), po czym `from jimmy.client import JimmyClient`. Wyniki
(`results*.json(l)`, `summary.json`) zapisują się obok `run.py`. Nie ma testów jednostkowych ani
lintera — weryfikacją jest sam eksperyment produkujący liczbę względem progu.

## Architektura

Dwa cienkie moduły biblioteczne + katalog eksperymentów. Cała wiedza operacyjna jest
skodyfikowana w klientach i dokumentach — czytaj je, zanim cokolwiek zaprojektujesz.

- **`jimmy/client.py`** — JEDYNE miejsce w projekcie wykonujące HTTP do Jimmy'ego. Async pula
  (`JimmyClient` jako context manager), semafor współbieżności, miękki sufit RPM, retry×3 z
  backoffem. Odpowiedź API to **surowy tekst + doklejony blok `<|stats|>...<|/stats|>`** (NIE
  JSON) — klient rozdziela `content` od `stats` i eksponuje telemetrię (`ttft`, `decode_rate`,
  `total_tokens`) za darmo. Kluczowe metody: `ask`, `map_prompts` (N różnych promptów równolegle),
  `sample_n` (N próbek tego samego promptu — rdzeń best-of-N/głosowania). Wszelka nowa komunikacja
  z API idzie przez ten moduł, nigdy przez surowe `httpx` w eksperymencie.
- **`jimmy/eval.py`** — tanie **deterministyczne weryfikatory** (materializacja tezy): `extract_json`
  (Jimmy gada wokół JSON-a — wyłuskuje pierwszy poprawny), `majority_vote`, `distinct_rate`,
  `filter_by_checker`, `exact_match`/`contains`, `accuracy`. To są „tańsze niż generacja" bramki.

- **`tools/`** — praktyczne implementacje jako **komendy shellowe** (wejście z pliku/stdin, wynik na
  stdout, diagnostyka na stderr). Biorą wzorzec z werdyktem KEEP i pakują go w używalny program.
  Dzielą `jimmy/` i jego politykę. Konwencje i lista: `tools/README.md`. Różnica względem
  `experiments/`: narzędzie produkuje użyteczny **wynik**, eksperyment — **liczbę względem progu**.
  Wykrywaj ciche porażki (`ok=True`, a odpowiedź bezużyteczna): `jimmy.eval.is_usable` (pustka/odmowa)
  oraz `prefill_tokens` ze statsów (ciche obcięcie kontekstu).

## Twarde ograniczenia Jimmy'ego (zmierzone, patrz `CHARACTERIZATION.md`)

Te fakty są nieobchodzalne — projektuj wokół nich, nie mierz ich ponownie bez powodu:

- **topK=1 → deterministyczny** (identyczne bajty) ⇒ memoizowalny. **topK=8 → różnorodność 1.0** ⇒
  best-of-N żyje. **topK≥16 → HTTP 500** (twardy sufit).
- Parametry `max_tokens`/`stop`/`temperature`/`seed` są **po cichu ignorowane** — długość i stop
  tnij promptem/post-processingiem, nie API. Pole `selectedModel` jest dekoracyjne (jest jeden model).
- **Kontekst: prefill do ~6k tok OK, ≥8k → pusta odpowiedź.** Chunki map-reduce ≤ ~4k (bezpiecznie
  ≤1.2k, bo instruction-following pada przy długim kontekście — Jimmy ignoruje instrukcje albo odmawia).
- Budżet to **~38 req/s @ conc=8**, nie „14k t/s". p50 latencji stałe (~134 ms) — serwer równolegli,
  nie kolejkuje; szybciej = więcej współbieżności.

## Polityka „kochamy Jimmy'ego, nie nadużywamy"

Wymuszona w kodzie, nie w intencjach (`jimmy/client.py`): `MAX_CONCURRENCY=8` (zmierzony punkt 0
błędów), `RPM_CEILING=2000`, retry×3. Nie podnoś tych limitów w eksperymentach.

## Metoda pracy: propose → evaluate → dispose → repeat → note

Każdy eksperyment produkuje **liczbę względem zadeklarowanego z góry progu, nie opinię**. Negatywne
wyniki to połowa produktu — martwy pomysł zostaje z liczbą, która go zabiła (DISPOSE), nie znika.

Struktura katalogu eksperymentu (`experiments/NNN-nazwa/`):
- `hypothesis.md` — teza + **próg zamrożony PRZED uruchomieniem** (pre-rejestracja).
- `run.py` — kod; drukuje `SUMMARY` i zapisuje `summary.json` + surowe wyniki.
- `verdict.md` — **KEEP / DISPOSE / PARTIAL** z liczbami, wnioskiem i następnym krokiem.

Po każdym eksperymencie **dopisz wpis do `LOG.md`** (append-only: data · hipoteza · metryka/próg ·
wynik · werdykt). Przy wyniku zmieniającym obraz projektu — zaktualizuj też destylat.

## Dokumenty — hierarchia prawdy

- **`FINDINGS.md`** — destylat „praw projektu" (np. *wolumen naprawia wariancję, nie bias*;
  *wolumen pomaga optymalizacji, nie eksploracji*). To sito do oceny KAŻDEGO nowego pomysłu.
- **`HOLY_GRAIL.md`** — rozstrzygnięcie celu „nieskończonej pętli emergentnej": Graal =
  **akumulacja** (stan zewnętrzny + presja nowości), nie optymalizacja (tam best-of-N wygrywa).
  Zawiera zwalidowany przepis na pętlę i nazwaną otwartą granicę (przestrzeń otwarta + miękki checker).
- **`CHARACTERIZATION.md`** — Faza 0, twarde pomiary (źródło ograniczeń powyżej).
- **`LOG.md`** — dziennik append-only wszystkich prób.
- **`README.md`** — skrót dla człowieka.

## Uwaga: co NIE jest kanoniczne

`DRAFT.md` oraz cały katalog `test/` to **„brudne" notatki i testy użytkownika** (zadeklarowane
wprost w nagłówku `DRAFT.md`). Traktuj je jako źródło pomysłów/kontekstu, nie jako specyfikację ani
zwalidowane wyniki.

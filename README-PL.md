# JIMMY

> Zamiana taniego, głupiego, nielimitowanego chatbota w niezawodne narzędzie — pomiarem, nie wiarą.

![model](https://img.shields.io/badge/model-llama3.1--8B-1f6feb)
![throughput](https://img.shields.io/badge/throughput-~38%20req%2Fs%20%40%20conc%208-2ea043)
![metoda](https://img.shields.io/badge/metoda-propose%E2%86%92evaluate%E2%86%92dispose-d29922)
![eksperymenty](https://img.shields.io/badge/eksperymenty-22-8250df)
![python](https://img.shields.io/badge/python-3.14-3776ab)

**Jimmy** to darmowy, nielimitowany chatbot oparty na `llama3.1-8B`, serwowany z wyspecjalizowanego
sprzętu ([`chatjimmy.ai`](https://chatjimmy.ai)) z inferencją ~13k tok/s. Ten projekt to
systematyczne badanie **do czego taki model naprawdę się nadaje** — prowadzone jak laboratorium,
gdzie każdy pomysł zarabia na siebie *liczbą* względem zadeklarowanego z góry progu, a martwe
pomysły zostają z liczbą, która je zabiła.

🇵🇱 Polski · 🇬🇧 [English (default)](README.md)

---

## Teza

> **Jimmy jest głupi per-próbka, ale niemal darmowy per-próbka. Zatem głupota jest kompensowalna
> wolumenem wszędzie tam, gdzie weryfikacja jest tańsza niż generacja.**

Dźwignią jest **współbieżność** (~38 req/s), nie prędkość modelu — dominuje sieć (RTT ~134 ms),
więc „13k t/s" nie jest budżetem; budżetem są **requesty na sekundę** i skalują się równoległością.

## Prawa projektu (potwierdzone w eksperymentach)

To sito, przez które przechodzi każdy nowy pomysł — pełne wyprowadzenie w [`FINDINGS.md`](FINDINGS.md).

1. **Wolumen naprawia wariancję, nie bias.** Best-of-N / głosowanie zamienia zawodne 8B w niezawodne
   narzędzie *wtedy i tylko wtedy*, gdy błędy są losowe i istnieje tani weryfikator lub agregator.
   Błędy systematyczne (Jimmy konsekwentnie źle rozumie zadanie) są nienaprawialne wolumenem.
2. **Wolumen pomaga optymalizacji, nie eksploracji.** Próbkowanie jest zpikowane na modach — świetne
   do wyboru najlepszego z N, słabe do pokrycia przestrzeni kategorialnej. Eksplorację odblokowuje
   dopiero **zewnętrzny akumulujący stan + presja nowości** (pokrycie 18% → 80%).
3. **Pętla ma sens tylko dla akumulacji, nie optymalizacji.** Gdy optimum mieści się w jednym
   wyjściu, best-of-N wygrywa i pętla nic nie dodaje. Gdy cel jest *większy niż jedna generacja*,
   akumulująca pętla jest jedynym, co działa — zob. [`HOLY_GRAIL.md`](HOLY_GRAIL.md).

## Twarde ograniczenia Jimmy'ego (zmierzone — [`CHARACTERIZATION.md`](CHARACTERIZATION.md))

| Własność | Wartość | Konsekwencja projektowa |
|---|---|---|
| Determinizm @ topK=1 | identyczne bajty | memoizowalny, powtarzalny, cache'owalny |
| Różnorodność @ topK=8 | distinct-rate 1.0 | **best-of-N żyje** |
| Sufit topK | topK ≥ 16 → HTTP 500 | twardy cap; dywersyfikuj przez topK=8 + perturbację promptu |
| `max_tokens`/`stop`/`temperature`/`seed` | po cichu ignorowane | długość/stop steruj promptem, nie API |
| Sufit kontekstu | ~6k prefill OK, ≥8k → **pusta odpowiedź** | chunki map-reduce ≤ ~1.2k tok |
| Kolano współbieżności | conc=8 → 37.8 req/s, 0 błędów, p50=134 ms | budżet ≈ 38 req/s; dźwignia = współbieżność |

## Szybki start

```bash
pip install httpx                                    # jedyna zależność runtime

python3 -m jimmy.client                              # smoke-test (1 request)
python3 experiments/001-majority-vote-math/run.py    # odtwórz eksperyment

# praktyczne narzędzie: streszcz dokument dowolnej długości
tools/summarize.py README.md --style tldr
cat long.txt | tools/summarize.py --map-only > notatki.md
```

## Struktura repozytorium

```
jimmy/client.py     # JEDYNY punkt HTTP: pula async, limit współbieżności, retry, parsowanie <|stats|>
jimmy/eval.py       # tanie deterministyczne weryfikatory: JSON, exact-match, głosowanie, distinct-rate
experiments/NNN-*/  # hypothesis.md · run.py · results.* · verdict.md
tools/              # zwalidowane wzorce spakowane jako komendy shellowe (stdin→stdout)
CHARACTERIZATION.md # zmierzone własności Jimmy'ego (Faza 0)
FINDINGS.md         # destylat praw — sito dla każdego nowego pomysłu
HOLY_GRAIL.md       # cel „emergentnej pętli", rozstrzygnięty
LOG.md              # append-only dziennik propose/evaluate/dispose
```

**Klient** udostępnia `ask`, `map_prompts` (N różnych promptów równolegle) i `sample_n` (N próbek
jednego promptu — rdzeń best-of-N / głosowania), a każde wywołanie zwraca za darmo sparsowaną
telemetrię `<|stats|>`. Cały ruch do API idzie przez ten jeden moduł; polityka bezpiecznego użycia
(`MAX_CONCURRENCY=8`, `RPM_CEILING=2000`, retry×3) jest wymuszona w kodzie, nie w intencjach.

## Eksperymenty

Metoda: **propose → evaluate → dispose → repeat → note**. Każdy eksperyment zamraża metrykę i próg
*przed* uruchomieniem, potem produkuje werdykt. Negatywne wyniki to połowa produktu.

Legenda: ✅ KEEP · ⚠️ PARTIAL / warunkowo · ❌ DISPOSE · 🔀 SPLIT · 💡 odkrycie kontr-intuicyjne ·
🧭 granica zdolności · 🔬 pomiar

| # | Eksperyment | Wynik |
|---|-------------|-------|
| [000](experiments/000-characterization/) | Charakterystyka (Faza 0) | 🔬 Zmierzono własności Jimmy'ego → [`CHARACTERIZATION.md`](CHARACTERIZATION.md) |
| [001](experiments/001-majority-vote-math/) | Głosowanie na matematyce | ✅ **KEEP** — self-consistency 64% → 92% · [werdykt](experiments/001-majority-vote-math/verdict.md) |
| [002](experiments/002-structured-json/) | Ekstrakcja strukturalna JSON | ✅ **KEEP** (ostra granica) — validity 100%, semantyka nie · [werdykt](experiments/002-structured-json/verdict.md) |
| [003](experiments/003-candidate-generation/) | Generacja kandydatów | 🔀 **SPLIT** — selekcja KEEP, pokrycie DISPOSE; akumulacja anti-mode KEEP · [werdykt](experiments/003-candidate-generation/verdict.md) |
| [004](experiments/004-map-reduce-doc/) | Map-reduce po długim dok. | ✅ **KEEP** — bije limit kontekstu, recall 0 → 100 · [werdykt](experiments/004-map-reduce-doc/verdict.md) |
| [006](experiments/006-holy-grail-evolution/) | Święty Graal jako GA | ❌ **DISPOSE** (z diagnozą) — pętla nic nie dodaje, gdy optimum ⊂ jedno wyjście · [werdykt](experiments/006-holy-grail-evolution/verdict.md) |
| [007](experiments/007-open-accumulation/) | Akumulacja otwarta | ❌ **DISPOSE** — akumulacja nasyca się też w przestrzeni otwartej · [werdykt](experiments/007-open-accumulation/verdict.md) |
| [008](experiments/008-asymmetric-critic/) | Krytyk asymetryczny | ❌ **DISPOSE** — krytyk poprawia draft, ale przegrywa z best-of-N o równym budżecie · [werdykt](experiments/008-asymmetric-critic/verdict.md) |
| [009](experiments/009-jimmy-automaton/) | Jimmy jako automat | ❌ **DISPOSE** hipotezy przestrzennej, ale odkrycie emergentne · [werdykt](experiments/009-jimmy-automaton/verdict.md) |
| [010](experiments/010-fs-tree-mapreduce/) | Map-reduce po drzewie FS | 💡 Kontr-intuicyjne — do klasyfikacji holistycznej **nie** dekomponuj · [werdykt](experiments/010-fs-tree-mapreduce/verdict.md) |
| [011](experiments/011-bash-codegen/) | Generacja kodu bash | ❌ **DISPOSE** dekompozycji — best-of-N wygrywa, reduce-przez-Jimmy'ego psuje · [werdykt](experiments/011-bash-codegen/verdict.md) |
| [012](experiments/012-big-input-docs/) | Duży input vs celny kontekst | 💡 Relewancja i zwięzłość biją rozmiar (+55 vs +11) · [werdykt](experiments/012-big-input-docs/verdict.md) |
| [013](experiments/013-hierarchical-summarization/) | Sumaryzacja hierarchiczna | ⚠️ **PARTIAL KEEP** — pipeline działa, reduce też trzeba pogryźć · [werdykt](experiments/013-hierarchical-summarization/verdict.md) |
| [014](experiments/014-web-html-ops/) | Operacje web / HTML | 🧭 Granica zdolności — mechanika → regex, semantyka → Jimmy · [werdykt](experiments/014-web-html-ops/verdict.md) |
| [015](experiments/015-meta-prompting/) | Meta-prompting | ❌ **DISPOSE** — nazywa właściwe idee, nie umie spakować działającego scaffoldu · [werdykt](experiments/015-meta-prompting/verdict.md) |
| [016](experiments/016-recursive-decomposition/) | Dekompozycja rekurencyjna | ⚠️ **PARTIAL KEEP** — technika defensywna wygrywa (+35), głęboka rekursja nie · [werdykt](experiments/016-recursive-decomposition/verdict.md) |
| [017](experiments/017-steps-to-commands/) | Kroki → komendy shell | ⚠️ **KEEP dla formy, nie intencji** — 96% działa, ~20% robi nie-to · [werdykt](experiments/017-steps-to-commands/verdict.md) |
| [018](experiments/018-command-analysis/) | Analiza komend | 💡 opisz→porównaj naprawia osąd (+30); bezpośredni sędzia rubber-stampuje · [werdykt](experiments/018-command-analysis/verdict.md) |
| [019](experiments/019-logic-benchmark/) | Benchmark logiki | 🧭 Logika zdaniowa OK (0.88), kwantyfikatory/wyższe rzędy ≈ chance · [werdykt](experiments/019-logic-benchmark/verdict.md) |
| [020](experiments/020-archwiki-to-manpage/) | ArchWiki → manpage | ✅ **KEEP** — hybryda treść-Jimmy + deterministyczny troff · [werdykt](experiments/020-archwiki-to-manpage/verdict.md) |
| [021](experiments/021-manpage-to-tldr/) | Manpage → tldr | ⚠️ **PARTIAL KEEP** — działa dla `tar`, niestabilne dla `journalctl` · [werdykt](experiments/021-manpage-to-tldr/verdict.md) |
| [022](experiments/022-synthetic-training-data/) | Syntetyczne dane treningowe | ✅ **KEEP** (ostry zakres) · [werdykt](experiments/022-synthetic-training-data/verdict.md) |

## Święty Graal

Deklarowanym celem projektu była „nieskończona pętla oparta na Jimmym z właściwościami
emergentnymi". Ma konkretną, empiryczną odpowiedź — i nie tę spodziewaną: **Graal to akumulacja,
nie optymalizacja.** Emergentną pętlę warto budować *wtedy i tylko wtedy*, gdy buduje strukturę
większą niż pojedyncza generacja, trzymaną w stanie zewnętrznym (pokrycie 18% → 80%). Pełne
rozstrzygnięcie, zwalidowany przepis i nazwana otwarta granica: [`HOLY_GRAIL.md`](HOLY_GRAIL.md).

## Narzędzia

Zwalidowane wzorce spakowane jako komendy w stylu uniksowym (wejście z pliku/stdin, wynik na stdout,
diagnostyka na stderr). Zob. [`tools/README.md`](tools/README.md).

- **[`summarize.py`](tools/summarize.py)** — streszcza dokument *dowolnej długości* (map-reduce +
  hierarchiczny reduce, wykrywanie cichego obcięcia, ~20 flag). Oparte na eksperymentach
  [004](experiments/004-map-reduce-doc/verdict.md) + [013](experiments/013-hierarchical-summarization/verdict.md).

## Polityka bezpiecznego użycia — „kochamy Jimmy'ego, nie nadużywamy"

Wymuszona w [`jimmy/client.py`](jimmy/client.py), nie w intencjach: `MAX_CONCURRENCY=8` (zmierzony
punkt 0 błędów), `RPM_CEILING=2000`, retry×3 z backoffem. Narzędzia klamrują każdą nadpisaną przez
użytkownika wartość z powrotem do tych limitów.

## Dla kontrybutorów / agentów AI

[`CLAUDE.md`](CLAUDE.md) dokumentuje architekturę, konwencje i twarde ograniczenia dla każdego
(człowieka lub agenta) pracującego w tym repo.

---

<sub>Projekt badawczy. Wszystkie liczby są odtwarzalne z `run.py` w katalogu każdego eksperymentu.
Język: angielski jest kanoniczny; polskie odpowiedniki mają sufiks `-PL`.</sub>

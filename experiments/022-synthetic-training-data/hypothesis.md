# 022 — Jimmy jako generator syntetycznych danych treningowych

## Pytanie
Czy Jimmy (llama3.1-8B, głupi per-próbka, ~darmowy) potrafi wygenerować syntetyczny
**zbiór treningowy z etykietami**, który realnie **uczy** inny model? Test przez *downstream*:
nie oceniamy danych opinią, tylko mierzymy skuteczność modelu wytrenowanego wyłącznie na danych
Jimmy'ego na **prawdziwym gold test secie**.

Zgodne z tezą projektu (głupota kompensowalna wolumenem tam, gdzie weryfikacja tańsza niż generacja)
i z prawem (7): **Jimmy = PROPOSER** (generuje próbki), a jakość rozstrzyga **deterministyczny
downstream** (nie sędzia-Jimmy).

## Zadanie i dane
- **AG News** (4 klasy: World / Sports / Business / Sci-Tech), prawdziwy gold z HuggingFace
  (`fancyzhx/ag_news`). Krótkie snippety newsowe.
- **Gold test (deterministyczny student):** stratyfikowane 500/klasę = **2000** itemów z `test`.
- **Gold test (student ICL):** stratyfikowane 40/klasę = **160** itemów (limit wywołań Jimmy).
- **N treningowe (dopasowane między ramionami):** **400** = 100/klasę (reżim małych danych,
  gdzie dane syntetyczne mają największą wartość).

## Dwaj studenci (ten sam zbiór treningowy, ten sam gold test)
1. **Student A — bag-of-words** (Multinomial Naive Bayes na surowych zliczeniach + add-1, czysty
   numpy, deterministyczny). Słownik/IDF budowany **tylko na danych treningowego ramienia**.
2. **Student B — ICL** (Jimmy jako few-shot klasyfikator; k=8 egzemplarzy z danego ramienia w
   prompcie; topK=1 deterministycznie). Zamyka lukę „student to nie LLM" — mierzy wartość danych
   jako egzemplarzy in-context dla modelu językowego.

## Ramiona (źródło danych treningowych)
- **FLOOR** — klasa większościowa (brak uczenia).
- **REAL@400** — 100/klasę prawdziwych przykładów AG-News (sufit @ dopasowanym N).
- **JIMMY-IID@400** — Jimmy generuje 100/klasę naiwnie (batche bez pamięci).
- **JIMMY-NOVELTY@400** — przepis 003b: batche z **zewnętrzną pamięcią tematów + presją nowości**
  (anti-collapse). Dotyka otwartej granicy Graala (przestrzeń otwarta + miękki checker).

## Diagnostyki (bez wycieku danych realnych do treningu)
- **Różnorodność** puli Jimmy: `distinct_rate`, rozmiar słownika, per-class recall (mode collapse
  = jedna klasa kanibalizuje).
- **Style-gap vs label-noise** (tylko diagnostyka): NB trenowany na REAL przewiduje etykiety na
  puli Jimmy; zgodność z intencją. Wysoka zgodność + niski downstream = luka stylu; niska zgodność
  = szum etykiet. **Nie** używane do filtrowania (leak).
- **Forced-4-way self-check** (per 018: wymuszony wybór z 4, nie yes/no): Jimmy klasyfikuje własne
  próbki → zgodność z intencją jako sygnał jakości etykiet Jimmy'ego.

## Metryka
Macro-F1 (i accuracy, per-class recall) na gold test. Wariancja: bootstrap treningu B=20
(NB deterministyczny per zbiór → wariancja z resamplingu).

## PROGI (pre-rejestrowane, przed wynikami)
Domknięcie luki `G = (F1_jimmy − F1_floor) / (F1_real − F1_floor)`:
- **G ≥ 0.50 → „ok" (KEEP)** — Jimmy użyteczny jako generator danych treningowych dla tego
  studenta/zadania.
- **G ≥ 0.75 → „dobry"**.
- **G < 0.50 → poniżej progu** dla danego ramienia.

Dodatkowo:
- **Mode collapse:** `distinct_rate` (znormalizowany) < **0.90** → deklarujemy kolaps dla puli.
- **Wartość presji nowości:** F1(NOVELTY) − F1(IID) > suma odchyleń → presja nowości pomaga
  (rozstrzyga otwarty wątek projektu), inaczej nie dodaje.

## Zakres werdyktu (ograniczenie)
Twierdzenie SKALUJEMY do zmierzonych studentów: „dla studenta bag-of-words / ICL na 4-klasowej
klasyfikacji tematycznej". Przypadek nietestowany — **dane SFT dla dostrajanego LM** — nazwać
jawnie jako OTWARTY. SST2 (binarny) tylko jeśli AG News da czysty wynik.

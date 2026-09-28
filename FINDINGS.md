# FINDINGS — praktyczne zastosowania Jimmy'ego

Stan na 2026-09-22. Destylat z `CHARACTERIZATION.md` + eksperymentów `001`, `002`.

## Prawo projektu (potwierdzone 2× niezależnie)

> **Wolumen naprawia wariancję, nie bias.**

best-of-N / głosowanie zamienia zawodnego 8B w niezawodne narzędzie **wtedy i tylko wtedy**, gdy
błędy Jimmy'ego są losowe (rozrzut wokół prawdy) i istnieje tani weryfikator/agregator. Gdy błąd
jest **systematyczny** (Jimmy konsekwentnie źle rozumie), więcej próbek tylko utrwala złą odpowiedź.

To jest sito do oceny KAŻDEGO przyszłego pomysłu na Jimmy'ego:
1. Czy istnieje tani deterministyczny weryfikator lub sensowna agregacja? Jeśli nie → odpad.
2. Czy błędy 8B tu są losowe czy systematyczne? Systematyczne → best-of-N nie pomoże.

### Prawo drugie (003): wolumen pomaga OPTYMALIZACJI, nie EKSPLORACJI
Próbkowanie Jimmy'ego jest **zpikowane na modach**. Więcej próbek:
- ✅ dla **optymalizacji** (wybór najlepszego po skalarze / głosowanie) — 001, 002, 003B,
- ❌ dla **eksploracji** (pokrycie przestrzeni kategorialnej) — 003A: nasycenie na ~18%.

**Ale (003b):** eksplorację odblokowuje *zewnętrzny akumulujący stan + presja nowości* — pamięć
"już widziane" wstrzykiwana do promptu podnosi pokrycie z ~18% do **~80%** (3-4× przy równym
budżecie). To jest zwalidowany mechanizm anti-collapse dla pętli (006).

### Prawo trzecie (006): pętla ma sens tylko dla AKUMULACJI, nie OPTYMALIZACJI
Gdy optimum mieści się w JEDNYM wyjściu Jimmy'ego → **best-of-N wygrywa**, pętla ewolucyjna nic nie
dodaje (006/006b: ewolucja = kontrola). Gdy cel PRZEKRACZA jedno wyjście (struktura większa niż
generacja) → pętla z akumulującym stanem jest jedynym, co działa (003b). Święty Graal = akumulacja.
Pełne rozstrzygnięcie i otwarta granica: **`HOLY_GRAIL.md`**.

### Prawo czwarte (004/010/011): kiedy DEKOMPONOWAĆ pracę na kroki
Intuicja "rozbij na jak najwięcej najprostszych kroków, przetwarzaj niezależnie, potem złóż" jest
dla Jimmy'ego **zwykle błędna**. Wygrywa tylko w wąskim przypadku:

| Typ zadania | wygrywa | dowód |
|-------------|---------|-------|
| Ekstrakcja z **rozłącznych** fragmentów, reduce **deterministyczny** (unia/suma) | **map-reduce** | 004: 0→100% |
| **Klasyfikacja/gestalt** (temat, sens całości) | **pokaż Jimmy'emu CAŁOŚĆ** (bez etapu map) | 010: 54% per-item → 100% holistycznie |
| **Synteza sprzężonych części** (kod, tekst) | **best-of-N całości + weryfikator** | 011: dekompozycja 17% < best-of-N 47% |

Reguła: dekomponuj TYLKO gdy jednostki są naprawdę niezależne I rekombinacja jest arytmetyczna.
Gdy zadanie korzysta z kontekstu całości → nie dziel. Gdy wymaga inteligentnego sklejania →
best-of-N całości + deterministyczny checker (NIE reduce-przez-Jimmy'ego).
Bonus (010): głupi model jest LEPSZY na agregacie niż na części — klasyfikuj grupy, nie pojedyncze byty.

**Rozszerzenie (013): gdy reduce MUSI być przez Jimmy'ego (sumaryzacja), sam reduce trzeba pogryźć.**
Holistyczny reduce nad wieloma sekcjami łamie ograniczenia ilościowe (instruction-following pada na
dużym wejściu). **Reduce hierarchiczny** (partie → mini-podsumowania → finał, każdy poziom = MAŁE
wejście) trzyma format (adherence 1.0) i kompresję (42×). Single-shot na wielkim dokumencie CICHO
obcina (prefill 110 z 15k) — map-reduce konieczny. Twarde ograniczenia w system-prompcie rządzą
formatem (0.92-1.0 vs 0.0 dla luźnego).

### Prawo piąte (012): kontekst — RELEWANCJA bije ROZMIAR
"Duży input → mały output" (dorzuć całą dokumentację) jest **odwrotnością** tego, co działa:
- dump całości `man bash` (~98k tok, 16× limit) lub nawet 10k tok → **0%** (nad limitem niszczy output),
- generyczny dump w budżecie (4k tok) → ledwo +11 pkt (rozcieńcza sygnał),
- **mały CELNY cheatsheet (~160 tok) → +55 pkt (39%→94%)**.

Błędy Jimmy'ego to często **luki wiedzy**, nie brak rozumowania — wstrzyknięcie DOKŁADNIE właściwego
małego fragmentu je zasypuje. Reguła: **minimal relevant input**, nie big input. Inwestuj w retrieval
właściwego snippetu (wysoki S/N, grubo pod ~6k), nie w rozmiar kontekstu.

### Prawo szóste (014): mechanika → deterministyczny kod, semantyka → Jimmy
Do zadań na HTML/danych, które są **mechanicznie specyfikowalne** (ekstrakcja linków, strip tagów,
keyword-grep, parsowanie struktury) → używaj **regex/parser/grep**: perfekcyjne, natychmiastowe,
darmowe. Jimmy jest tu ściśle GORSZY (014: links F=0.64, strip F1=0.68, keyword F=0.69 vs 1.0).
Jimmy dodaje wartość TYLKO dla **semantyki bez deterministycznego odpowiednika** (filtr tematyczny
F=0.94, opis treści, tagowanie). **Wzorzec pipeline'u:** parser robi mechanikę, Jimmy dostaje tylko
podzadania semantyczne na oczyszczonym już tekście. Nie każ Jimmy'emu robić tego, co regex robi lepiej.

### Prawo dziewiąte (019): zdolności logiczne warstwowe + oceniaj balanced accuracy
Jimmy: logika zdaniowa (L0) solidna (bal_acc 0.88), ale od kwantyfikatorów/wyższych rzędów (L1-L5)
zapada do near-chance (0.62-0.75) z uporczywym biasem TRUE. Głosowanie nie ratuje (bias, nie wariancja).
**Metodologia:** dla KAŻDEGO binarnego zadania raportuj balanced accuracy + class-balance + odpowiedź-rate —
inaczej nierównowaga gold + bias modelu udają kompetencję (pierwszy bieg 019: L4 gold 6T/0F → stałe TRUE
„=1.00"). Praktyka: ufaj Jimmy'emu w prostej boolowskiej (z weryfikacją), nie w rozumowaniu kwantyfikatorowym.

### Prawo ósme (018): pośrednicz osąd przez wierny OPIS — nie pytaj wprost „czy pasuje?"
Bezpośredni Jimmy-sędzia „czy komenda pasuje do zadania?" RUBBER-STAMPUJE (018 T2: mismatch-recall 0.08,
uznaje wszystko za MATCH — bias pozytywny, głosowanie nie pomaga). ALE ta sama ocena przepuszczona przez
wierny OPIS (018 T3: „opisz co robi komenda" → „porównaj zadanie z opisem") wykrywa 100% niedopasowań
(acc 0.54→0.83, +30 pkt). Bo opisywanie to recall wiedzy, który Jimmy robi WIERNIE (T1 faithful 1.0), a
porównanie dwóch opisów omija bias sędziego. Technika: **describe→compare zamiast direct-judge**.
Niuansuje Prawo 7: Jimmy to zły DIREKTNY sędzia, ale DOBRY komparator opisów.

### Prawo siódme (015): Jimmy = PROPOSER, nigdy EVALUATOR/DISPOSER/architekt
Jimmy nie potrafi zaprojektować działającej pętli problem-solvingu (meta-prompting). Wygenerowane
scaffoldy: structural rate 60%, funkcjonalnie fitness 0 vs deterministyczny sufit 8.88. Root cause:
(a) proposer łamie własne ograniczenia (przykład 14 słów przy limicie 12), (b) evaluator napisany jak
zapieczona ODPOWIEDŹ, nie ogólna INSTRUKCJA, ocenia "vibes" nie prawdziwe kryterium. Nawet HUMAN
scaffold (2.38) ≪ deterministyczna selekcja (8.88) — **wąskim gardłem jest evaluator; soft-evaluator
(Jimmy lub człowiek) nie śledzi prawdy**. Reguła: w pętli propose/evaluate/dispose Jimmy pełni TYLKO
rolę PROPOSERA (generator różnorodności); EVALUATOR i DISPOSER muszą być deterministyczne. To znów
kanoniczny przepis: best-of-N (Jimmy proponuje) + deterministyczny weryfikator (nie Jimmy ocenia).

### Prawo dziesiąte (022): Jimmy generuje użyteczne dane treningowe; wiążą DWA deficyty — pokrycie ORAZ wierność etykiet
Downstream (AG News 4-klasy, ten sam klasyfikator na danych z różnych źródeł, macro-F1 na prawdziwym
gold test, N=400 dopasowane). **KEEP jako generator danych treningowych** dla tych studentów:
- **Student NB (bag-of-words), floor=majority:** Jimmy-IID domyka lukę floor→REAL w **0.74**.
- **Student ICL, floor=ZERO-SHOT** (uczciwy floor — Jimmy już umie klasyfikować newsy, zero-shot
  F1 0.517; majority zawyżałby G): egzemplarze Jimmy'ego realnie pomagają (wszystkie >zero-shot o
  >3 SE, G IID 0.70 / NOVELTY 0.93), ALE trzy źródła (REAL/IID/NOVELTY) są **nierozróżnialne między
  sobą** (SE≈0.033/160 itemów; IID vs NOVELTY = 1.4 SE). Pomoc największa na najtrudniejszej klasie
  Sci/Tech (zero-shot recall 0.0).

Cztery niuanse:
- **Dwa realne deficyty puli Jimmy vs REAL przy równym N:** (a) **pokrycie leksykalne** — vocab REAL
  4583 vs IID 2142 vs NOVELTY 1998 (<½ słownika; NB ignoruje OOV → wprost zasila lukę); (b)
  **wierność etykiet** — self-check forced-4way 0.83/0.74, style-gap agreement 0.94/0.83. Oba wiążą.
- **`distinct_rate` to zły przyrząd na kolaps** dla generowanej prozy (≈1.0 z konstrukcji; próg 0.90
  nie mógł się odpalić). Kolaps na poziomie dokumentu nie wystąpił, ale na poziomie SŁOWNIKA — tak.
- **Presja nowości (003b) tu SZKODZI i przegrywa na SWOIM celu:** u NB 0.617→0.429; NOVELTY gorszy
  na OBU osiach — nie kupił nawet pokrycia (vocab 1998 < IID 2142), a stracił wierność. 003b działa
  dla przestrzeni ENUMEROWALNEJ z TWARDYM checkerem; klasa semantyczna nim nie jest. Mechanizm
  skonfundowany: nowość implementowana przez wstrzykiwanie pamięci → dryf etykiet + degradacja
  długim kontekstem (urwane próbki).
- **Wartość interwencji zależy od studenta:** bag-of-words wrażliwy na szum etykiet i pokrycie; ICL
  (k=8) toleruje. Ten sam zbiór, różny werdykt. Tani proxy jakości: model-REAL→pula Jimmy
  (style-gap agreement) przewidział ranking bez sędziego-Jimmy'ego.
Przepis: IID + dedup (n-gram Jaccard) + opcjonalny filtr forced-4-way; osobno zwiększać pokrycie
leksykalne. **OTWARTE:** dane SFT dla dostrajanego LM (nietestowane; torch dostępny).

## Portfolio zastosowań

### ✅ Potwierdzone (KEEP) — działają niezawodnie
| Zastosowanie | Dowód | Wzorzec |
|--------------|-------|---------|
| **Self-consistency na zadaniach weryfikowalnych** (arytmetyka, liczby, fakty z agregacją) | 001: 64%→92% @ vote-21..31 | `sample_n(15-21) → majority_vote` |
| **Kuloodporna emisja JSON wg schematu** (tekst→struktura) | 002: 100% validity @ best-of-8, **powtórzone 2×** | `sample_n(8) → filter(validate) → pierwszy walidny` |
| **Klasyfikacja na rozłącznych, dobrze zdefiniowanych kategoriach** | 002: 91.7% / 100% (2 runy), podzbiór jednoznaczny | `sample_n(8) → majority_vote(intent)` |
| **Generacja kandydatów + selektor po skalarze** (optymalizacja) | 003B: −26.9% objektywu, best-of-20 | `sample_n(N) → scorer → argmin/argmax` |
| **Eksploracja przestrzeni z pamięcią zewnętrzną** (anti-mode, przestrzeń enumerowalna) | 003b: 18%→~80% pokrycia, 3-4× | pętla: `seen` + prompt "nie: [seen]" |
| **Przetwarzanie długich dokumentów przez map-reduce** (APLIKACJA) | 004: recall 0.00→**1.00** na dok 2.6× limitu | `chunk(≤1.2k) → map ekstrakcja → reduce unia` |
| **Jimmy jako reguła CA → emergentny porządek globalny** | 009b: szachownica antyferromagnetyczna, ściśle topologiczna | siatka + reguła voter/konsensus, aktualizacja synchroniczna |
| **Pisanie kodu (bash): celny cheatsheet + best-of-N + wykonanie** | 011: best-of-N 47%; 012: **+cheatsheet → 94%** | `RAG(mały snippet) + sample_n(k) → uruchom → pass` |
| **Wypełnianie luk wiedzy celnym mini-kontekstem** (RAG) | 012: +55 pkt z ~160 tok relewantnych | wstrzyknij DOKŁADNY fragment, grubo pod 6k |
| **Klasyfikacja holistyczna grup** (folder/zbiór, nie pojedynczy byt) | 010: 54% per-plik → **100%** per-folder | pokaż Jimmy'emu całą grupę naraz |
| **Hierarchiczna sumaryzacja wielkiego dokumentu** | 013: adherence 1.0, kompresja 42×, faith 0.9 | `chunk → map(twardy prompt) → reduce HIERARCHICZNY` |
| **Transformacja dokumentu → format** (ArchWiki→manpage) | 020: renders 0-warnings, faith 0.86, man-compatible | Jimmy=treść, Python=troff; strip→chunk→map→reduce |
| **manpage → tldr** (bogate manpage'y + precyzyjny prompt) | 021: tar renderuje w prawdziwym tldr, faith 1.0 | Jimmy=treść (prompt: "najczęstsze realne użycia"), Python=format; NIESTABILNE per-komenda |
| **Semantyczne operacje na HTML/tekście** (filtr tematyczny, opis, tagowanie) | 014: topic-filter F=0.94 | parser→mechanika, Jimmy→tylko semantyka |
| **Defensywne planowanie kroków** ("nie zakładaj nic, weryfikuj precond./sukces") | 016: defensive-ratio 0.90 vs 0.54 plain (+35 pkt) | defensywny system-prompt + płytka bounded dekompozycja |
| **Generowanie komend shell per krok** (forma) | 017: best-of-N valid 1.0, real 1.0, runnable 0.96 | `sample_n → filtr: bash -n ∧ real ∧ exec(read-only)` |
| **Logika zdaniowa L0** (tautologie, ewaluacja, entailment) | 019: balanced acc 0.88, bez biasu | best-of-N + głosowanie |
| **Opis/wyjaśnianie komend** (recall wiedzy) | 018 T1: faithful 1.0, recall 0.68 | jedno zdanie, best-of-N |
| **Weryfikacja dopasowania przez opis** (describe→compare) | 018 T3: acc 0.83, mismatch-recall 1.0 | opisz komendę → porównaj z zadaniem |
| **Generowanie alternatywnych komend** (różnorodność) | 018 T4: diverse 1.0, valid 1.0, equiv 0.58 | best-of-N + sprawdź równoważność wyjścia |
| **Generowanie danych treningowych** (klasyfikacja tematyczna) | 022: IID domyka lukę G=0.74 (NB, floor=majority) / 0.70 (ICL, floor=zero-shot) na gold AG News | IID per-klasa + dedup + filtr forced-4-way; NIE presja nowości |
| **Deterministyczna, cache'owalna funkcja** (topK=1) | Faza 0: identyczne bajty | memoizacja lokalna |
| **Masowa równoległa transformacja** (~38 req/s, conc=8; sustained 57 rps/0 błędów) | Faza 0 + sustained.py | pula async z klienta |

### ❌ Odrzucone / ograniczone (DISPOSE)
| Pomysł | Powód | Liczba |
|--------|-------|--------|
| Jimmy jako **arbiter** na nakładającej się/spornej taksonomii | tam ludzki gold też sporny; głosowanie utrwala jeden z rozsądnych wyborów | 002: 37.5% na podzbiorze dyskusyjnym (stabilne 2×) |
| **Naiwne** pokrycie przestrzeni samym wolumenem (bez pamięci) | mode-collapse: próbki pikują na kilku ulubieńcach | 003A: nasycenie ~18% (naprawione w 003b pamięcią → ~80%) |
| Sterowanie długością/stopem przez API (`max_tokens`, `stop`) | parametry ignorowane | Faza 0 |
| Wybór mocniejszego modelu (`70B`, itp.) | `selectedModel` ignorowany, jest jeden 8B | Faza 0 |
| Długi kontekst (>6-8k tok) / duży map bez chunkowania | pusta odpowiedź + spadek instruction-following | Faza 0 |
| **Otwarta akumulacja / open-ended inwencja** z miękkim checkerem | nasyca się (mody fonotaktyczne + echo okna + dziura bramki) | 007: accept-rate 0.22→0.06 |
| **Pętla krytyka** (generator↔krytyk) jako optymalizacja | krytyk dzieli bias, czasem psuje; best-of-N o równym budżecie wygrywa | 008: 4.01 vs 4.58 |
| **Dekompozycja na kroki + reduce-przez-Jimmy'ego** (codegen) | reduktor nie sklei sprzężonych/niespójnych snippetów; planowanie nie winne (C1=C2) | 011: 17% vs best-of-N 47% |
| **Dekompozycja klasyfikacji na per-item map + reduce** | etap map wyrzuca kontekst i wstrzykuje szum | 010: 54% vs 100% holistycznie |
| **"Duży input": dump całej dokumentacji do promptu** | nad limitem → 0%; generyczny dump w budżecie rozcieńcza (ledwo +11) | 012: over-limit 0%, man4k +11 vs cheatsheet +55 |
| **Mechaniczna ekstrakcja z HTML** (linki, strip, keyword) przez Jimmy'ego | regex/parser/grep perfekcyjne+darmowe; Jimmy gorszy | 014: F 0.64-0.69 vs 1.0 |
| **Jimmy jako architekt scaffoldu / soft-evaluator** (meta-prompting) | myli instrukcję z przykładem, ocenia vibes; fitness 0 vs det 8.88 | 015: structural 60%, exec 0 |
| **Głęboka rekursja do „warstwy atomowej"** | Jimmy nie osądza atomowości (nigdy ATOMIC), eksplozja + redundancja międzygałęziowa | 016: 299 liści, cap, ~20% dup |
| **Unattended wykonywanie komend Jimmy'ego** | ~20% działa-ale-błędne; emituje destrukcję (`init 6` reboot) | 017: semantyka 0.79, exec 0.96 |
| **Jimmy jako bezpośredni sędzia „czy X pasuje do Y?"** | rubber-stamp / bias pozytywny; uznaje wszystko za MATCH | 018 T2: mismatch-recall 0.08 (użyj describe→compare) |
| **Rozumowanie kwantyfikatorowe / wyższego rzędu** (L1+) | near-chance, bias TRUE; głosowanie nie ratuje | 019: bal_acc 0.62-0.75 (vs L0 0.88) |
| **Jimmy-CA → domeny przestrzenne** (klastry ferromagnetyczne) | reguła uśredniająca dyfunduje; voter daje anty-porządek nie domeny | 009: Δsim≈−0.1 |
| **Presja nowości (003b, wstrzykiwanie pamięci) do generacji danych treningowych** | brak twardego checkera klasy → dryf etykiet + degradacja długim kontekstem; przegrywa na SWOIM celu (vocab 1998 < IID 2142 — nie kupił pokrycia) | 022: NB 0.617→0.429 (G 0.74→0.47) |

> **Korekta 002:** globalne "70% intent-acc" było mylące — mianownik zawierał moje własne sporne
> etykiety. Po rozdzieleniu: jednoznaczne ≈92-100%, sporne 37.5%. Właściwy wniosek to nie "bias",
> lecz "Jimmy radzi sobie z czystymi kategoriami; granicą jest niedookreślenie taksonomii".

## Roadmap (następne hipotezy do przetestowania)
- ✅ **003 — generacja kandydatów** (ZROBIONE): B (selekcja) KEEP, A (pokrycie) DISPOSE,
  003b (anti-mode z pamięcią) KEEP — mechanizm anti-collapse zwalidowany.
- ✅ **006 + 006b — Święty Graal jako GA** (ZROBIONE): **DISPOSE** emergencji-jako-optymalizacji.
  best-of-N o równym budżecie nie do pobicia przez ewolucję (A=D). Rozstrzygnięcie: **Graal =
  akumulacja, nie optymalizacja** — patrz `HOLY_GRAIL.md`. Otwarta granica: przestrzeń otwarta + miękki checker.
- ✅ **004 — map-reduce po dokumencie** (ZROBIONE): **KEEP**, recall 0.00→1.00 na dok 2.6× limitu.
- ✅ **007 — otwarta akumulacja, miękki checker** (ZROBIONE): **DISPOSE** — nasyca się (accept 0.22→0.06);
  odpowiedź na granicę Graala: akumulacja = recall enumerowalny, nie otwarta inwencja.
- ✅ **008 — agenci asymetryczni (generator↔krytyk)** (ZROBIONE): **DISPOSE** — best-of-N wygrywa (4.58 vs 4.01).
- ✅ **009 + 009b — Jimmy jako reguła CA** (ZROBIONE): **EMERGENCJA** (009b: szachownica antyferromagnetyczna,
  topologicznie zależna); 009 (blend) → kolaps semantyczny samoreferencyjny.
- ✅ **011 — codegen bash (dekompozycja vs monolit)** (ZROBIONE): **DISPOSE** dekompozycji;
  best-of-N + wykonanie wygrywa (47% vs 17%). Planowanie nie winne (C1=C2).
- ✅ **010 — drzewo FS map-reduce** (ZROBIONE): odkrycie — dla klasyfikacji holistycznej NIE
  dekomponuj (54% per-item → 100% całość). Domyka Prawo czwarte.
- **005 — pipeline złożony:** Jimmy (ekstrakcja JSON, 100%) → deterministyczna logika → Jimmy (render). *(niewykonane)*
- **Następne otwarte wątki:** 009c (reguła reakcja-dyfuzja z hamowaniem → wzorce Turinga?);
  007b (twardszy checker: embeddingi + filtr degeneracji — czy otwarta akumulacja ruszy?);
  008b (asymetryczni agenci na zadaniu NIE-optymalizacyjnym: dialog/negocjacja jako artefakt).
- **Święty Graal:** pętla z anti-collapse. Klocki gotowe: selektor po skalarze (003B),
  **pamięć zewnętrzna + presja nowości jako anti-collapse (003b, zwalidowane empirycznie)**.
  Trzy dozwolone źródła emergencji: (a) selekcja+fitness (Jimmy = operator mutacji, 14k t/s =
  tysiące generacji), (b) akumulujący stan zewnętrzny (świat: plik/graf/siatka), (c) asymetryczni
  agenci (różne system-prompty + reguły interakcji). Wymóg: jawny mechanizm anti-collapse +
  raportowana metryka różnorodności w czasie, nie same transkrypty.
  - ✅ **Warunek wstępny (obciążenie ciągłe) SPEŁNIONY:** 800 req ciągłych conc=8 = **0 błędów**,
    57.5 rps, latencja stabilna (dryf −8%). `sustained.py`. conc=8 bezpieczne dla trwałej pętli.

## Jak dołożyć eksperyment
`experiments/NNN-slug/` z `hypothesis.md` (hipoteza + metryka + **próg** przed uruchomieniem),
`run.py` (produkuje liczbę), `verdict.md` (KEEP/DISPOSE + liczba, która zdecydowała). Wpis do `LOG.md`.

# LOG — propose / evaluate / dispose / repeat

Dziennik append-only. Każdy wpis: data · hipoteza · metryka · próg · **KEEP/DISPOSE**.
Negatywne wyniki to połowa produktu — martwe pomysły zostają z liczbą, która je zabiła.

---

## 2026-09-22 — Faza 0: charakterystyka
- **Hipoteza:** Jimmy nadaje się do abstrakcji "szybki, głupi, darmowy per-próbka".
- **Metryka/próg:** 8 sond, każda z konkretną liczbą (patrz CHARACTERIZATION.md).
- **Wynik:** determinizm@topK1 ✓, różnorodność@topK8=1.0 ✓, sufit topK=8 twardy, parametry ignorowane,
  jeden model, kontekst ~6k, budżet ~38 req/s@conc8.
- **Werdykt:** **KEEP.** Teza operacyjna potwierdzona: *dźwignia = współbieżność*, *best-of-N żywy*.

---
## 2026-09-22 — 001: głosowanie większościowe (self-consistency) na matematyce
- **Hipoteza:** głosowanie po k próbkach kompensuje głupotę per-próbka (gdy weryfikacja tania).
- **Metryka/próg:** vote-31 ≥ +15 pkt vs single ORAZ ≥70%. 24 zadania × 31 próbek.
- **Wynik:** single 64.7% → vote-21 **93.0%** (plateau), lift **+27 pkt**, 744 req/0 błędów.
- **Werdykt:** **KEEP.** Uwaga: naprawia wariancję, nie bias (2/24 zadania z błędem systematycznym
  niereparowalne). Sweet-spot k≈15-21.

## 2026-09-22 — 002: ekstrakcja strukturalna JSON (best-of-N + walidator)
- **Hipoteza:** twardy walidator + best-of-N daje niezawodny JSON w pipeline.
- **Metryka/próg:** validity@best-of-8 ≥95% ORAZ intent-accuracy(vote) ≥80%. 20 inputów × 8.
- **Wynik:** validity@best-of-8 **100%** ✅, intent-accuracy **70%** ❌. 160 req/0 błędów.
- **Werdykt:** **PARTIAL KEEP.** Format JSON rozwiązany (100%); klasyfikacja semantyczna nie
  (bias + niejednoznaczność etykiet). Potwierdza prawo: *wolumen naprawia wariancję, nie bias.*

## 2026-09-22 — 003: Jimmy jako generator kandydatów (SPLIT)
- **Hipoteza:** różnorodność=1.0 → Jimmy generuje kandydatów, selektor wybiera; różnorodność=produkt.
- **A (pokrycie):** próg ≥40% przestrzeni. Wynik 17.5%/18.1% (mode-collapse) → **DISPOSE** (lift 7-9× ale nasycenie).
- **B (selekcja):** próg ≥25% redukcji. Wynik **26.9%** → **KEEP**. best-of-N + skalarny scorer działa.
- **Meta:** wolumen pomaga OPTYMALIZACJI, nie EKSPLORACJI. Próbkowanie zpikowane na modach.

## 2026-09-22 — 003b: anti-mode z pamięcią zewnętrzną (KEEP, przełom)
- **Hipoteza:** zewnętrzny stan "seen" + presja nowości łamie mode-collapse.
- **Próg:** ≥60% przestrzeni ORAZ ≥2× kontroli (równy budżet bez feedbacku). 480 req/0 błędów.
- **Wynik:** Europa **77.3%** (3.1×), stany **80.0%** (4.4×). **KEEP.**
- **Znaczenie:** pierwszy działający klocek Świętego Graala — anti-collapse zwalidowany empirycznie.

## 2026-09-22 — 006 + 006b: Święty Graal jako GA (DISPOSE emergencji-optymalizacji)
- **Hipoteza:** Jimmy jako operator mutacji w GA — ewolucja bije best-of-N o równym budżecie.
- **Próg:** A_best ≥ D+2/3 i ≥1.25D. 4 ramiona (GA / losowa-selekcja / kolaps / kontrola). 2×1024 req.
- **006 (aliteracja):** cel nasycony w seedzie (A=D=12) → DISPOSE-z-diagnozą, przeprojektowano.
- **006b (koniunkcja, trudniejszy):** A=D=**20**, emergencja **False**. Confound: sufit seedowy,
  nieruszony przez nikogo (24 konstruowalne, nieosiągnięte) → wiąże zdolność per-wyjście, nie search.
- **Werdykt:** **DISPOSE** wariantu-optymalizacji. Selekcja tylko UTRZYMUJE jakość (B→0 bez niej).
- **Rozstrzygnięcie (HOLY_GRAIL.md):** Graal = **akumulacja** (003b: 18→80%), nie optymalizacja
  (best-of-N wygrywa gdy optimum ⊂ jedno wyjście). Otwarta granica: przestrzeń otwarta + miękki checker.

## 2026-09-22 — 004: map-reduce po długim dokumencie (APLIKACJA, KEEP)
- **Hipoteza:** równoległe chunkowanie bije limit kontekstu przy ekstrakcji z długich dokumentów.
- **Próg:** MR recall ≥0.9 i lift ≥30 pkt. Dok ~15.8k tok (2.6× limit), 24 gold, 34 req.
- **Wynik:** single-shot **0.00** (pusta odp. nad limitem) → map-reduce **1.00**, lift **+100 pkt**.
- **Werdykt:** **KEEP.** Kanoniczny wzorzec: chunk(≤1.2k) → map ekstrakcja → reduce unia.

## 2026-09-22 — 007: otwarta akumulacja z miękkim checkerem (DISPOSE otwartości)
- **Hipoteza:** akumulacja pozostaje otwarta w przestrzeni nieograniczonej z miękką bramką nowości.
- **Próg:** accept-rate ostatnia 1/3 ≥0.5. 20 rund × 16, wymyślanie stworzeń, bramka Jaccard.
- **Wynik:** accept-rate 0.22→**0.06** (nasycenie), dup-w-oknie 272 vs poza-oknem 15.
- **Werdykt:** **DISPOSE.** Mechanizm: (1) instruction-following pada (echuje okno), (2) kolaps
  fonotaktyczny/semantyczny, (3) dziura w miękkiej bramce. Akumulacja = recall enumerowalny (003b),
  NIE otwarta inwencja. Odpowiedź na nazwaną granicę Graala.

## 2026-09-22 — 008: agenci asymetryczni Generator↔Krytyk (DISPOSE, ukryty scorer)
- **Hipoteza:** miękki krytyk-w-pętli bije best-of-N o równym budżecie.
- **Próg:** refine-final ≥ +10% vs best-of-N (budżet 7 req/element). 16 elementów, 224 req.
- **Wynik:** refine 3.14→4.01 (+28% vs gen0), ale best-of-N=**4.58 > 4.01** → **DISPOSE.**
- **Znaczenie:** potwierdza prawa 1+3 na architekturze asymetrycznej. Krytyk dzieli bias, czasem
  psuje; jeśli masz jakikolwiek scorer → best-of-N wygrywa.

## 2026-09-22 — 009 + 009b: Jimmy jako reguła automatu komórkowego (EMERGENCJA)
- **Hipoteza:** z lokalnej reguły Jimmy'ego wyłania się globalna struktura przestrzenna.
- **Próg:** neighbor_sim − random_sim ≥ +0.10, zależne od topologii. Siatka 6×6, 25 kroków, 2×1800 req.
- **009 "blenduj sąsiadów":** Δsim=−0.10 → DISPOSE domen, ale ODKRYCIE: globalny kolaps semantyczny,
  samoreferencja (słowa o mieszaniu), faza ciekła.
- **009b "wybierz spośród sąsiadów" (voter/Ising):** Δsim=**−0.354**, **SZACHOWNICA** antyferromagnetyczna
  (blinker period-2); CTRL (losowi sąsiedzi) → jednorodna fiksacja (mean-field). **Emergencja
  potwierdzona** — porządek globalny ściśle zależny od topologii. Highlight projektu.

## 2026-09-22 — 011: uczenie Jimmy'ego pisać bash (dekompozycja vs monolit)
- **Hipoteza (użytkownika):** rozbicie na nieredukowalne kroki + reduce bije monolit.
- **Ramiona:** A single, B best-of-N, C1 dekompozycja z planem-danym, C2 z planem-Jimmy'ego.
  Walidacja = WYKONANIE na testach; harness zwalidowany na referencjach. 448 req.
- **Wynik:** B **46.7%** > A 30% > C1=C2 **16.7%**. Dekompozycja HURTS; C1=C2 → nie planowanie, sama
  dekompozycja. C2 miał więcej budżetu niż B i przegrał.
- **Werdykt:** **DISPOSE dekompozycji dla codegen.** Rekomendacja: best-of-N całości + wykonanie.

## 2026-09-22 — 010: analiza drzewa FS (map plik → reduce folder → reduce drzewo)
- **Hipoteza:** czy Jimmy-reduce degraduje wielopoziomowo (otwarte pytanie z 011)?
- **Wynik (ODWROTNY):** L0 map per-plik **54%**, L1 deterministyczny **50%**, L1 **Jimmy-holistyczny
  100%**, L2 drzewo recall **1.0**. Jimmy-reduce > deterministyczny o +50 pkt. 125 req.
- **Odkrycie:** dla klasyfikacji/gestalt agregat jest ŁATWIEJSZY niż części — dekompozycja per-item
  wyrzuca kontekst i wstrzykuje szum. NIE dekomponuj holistycznych osądów; pokaż Jimmy'emu całość.
- **Zunifikowana taksonomia dekompozycji (004/010/011)** — patrz FINDINGS "Prawo czwarte".

## 2026-09-22 — 012: "duży input → mały output" (dokumentacja bash do generatora)
- **Hipoteza (użytkownika):** dorzucenie dokumentacji bash do promptu pomoże generatorowi.
- **Setup:** te same 6 zadań, best-of-N stały, wariowany kontekst: NONE / cheatsheet(160 tok) /
  man bash 4k / man bash 10k(over-limit). 324 req.
- **Wynik:** NONE 38.9% → **CHEATSHEET 94.4% (+55 pkt)** → MANBASH_4K 50% (+11) → MANBASH_OVER **0%**.
- **Werdykt:** "duży input" PRZEGRYWA (dump całości=0%, generyczny 4k ledwo +11). **Mały CELNY
  cheatsheet wygrywa (+55).** Rafinacja: nie rozmiar, lecz RELEWANCJA przy minimalnej wielkości.
  Zwycięski przepis na kod: RAG(celny) + best-of-N + wykonanie = 94%.

## 2026-09-22 — 013: hierarchiczna sumaryzacja wielkiego artykułu (Wikipedia ML, ~15k tok)
- **Hipoteza (użytkownika):** chunk po sekcji + twarde ograniczenia w system-prompcie = dobre streszczenie.
- **Arms:** NAIVE (single-shot), MR_HARD (reduce holistyczny), MR_LOOSE (luźny), MR_HIER (reduce 2-poziomowy). 173 req.
- **Wynik:** NAIVE cicho obcina (prefill=110 z 15k, recall 7%). Map niezawodny (faith ~0.9). Holistyczny
  reduce łamie limity (498-962 sł); **MR_HIER naprawia: adherence 1.0, 269 sł, kompresja 42×**. HARD ≫ LOOSE
  na formacie (0.92-1.0 vs 0.0). Tradeoff kompresja↔pokrycie (recall ~1/3 głównych tematów).
- **Werdykt:** **PARTIAL KEEP.** Pipeline działa; twarde ograniczenia rządzą formatem (potwierdza pomysł
  użytkownika); ale REDUCE też trzeba pogryźć (hierarchicznie). Rozszerza prawo czwarte.

## 2026-09-22 — 014: zadania okołointernetowe na surowym HTML (curl → chunki → operacje)
- **Hipoteza:** Jimmy na chunkach HTML robi ekstrakcję linków/tekstu/keywordów + filtr tematyczny + opis.
- **Oś:** mechaniczne (jest deterministyczny baseline) vs semantyczne (brak). Strona HN. 31 req.
- **Wynik:** mechaniczne — Jimmy PRZEGRYWA z regex/parser/grep (links F=0.64, strip F1=0.68, keyword F=0.69
  vs deterministyczne 1.0). Semantyczne — Jimmy DODAJE WARTOŚĆ (topic_filter P/R/F=1.0/0.89/**0.94**,
  opis poprawny) — brak deterministycznego odpowiednika.
- **Werdykt:** granica zdolności → **mechanika: deterministyczny kod; semantyka: Jimmy.** W pipeline
  parser robi mechanikę, Jimmy tylko podzadania semantyczne. (Prawo szóste.)

## 2026-09-22 — 015: meta-prompting / problem-solving (Jimmy generuje scaffold propose/dispose/evaluate)
- **Hipoteza:** Jimmy dostaje przykład problemu, generuje 3 prompty; ocena FUNKCJONALNA (wykonaj scaffold).
- **Setup:** PTASK (dyskryminujące, deterministyczny fitness) + MATH (null). Arms: JIMMY_BEST/WORST, HUMAN,
  BESTOFN_DET. Structural vs execution rozdzielone. 552 req.
- **Wynik:** structural_rate 0.60; PTASK fitness JIMMY=0, HUMAN=2.38, **BESTOFN_DET=8.88** (predykcja
  Jimmy≤HUMAN≤DET potwierdzona). MATH 100%=100% (null). eval-parse 1.0.
- **Diagnoza (artefakty):** proposer Jimmy'ego daje przykład 14-słowny przy limicie 12; evaluator
  napisany jak zapieczona ODPOWIEDŹ, nie ogólna INSTRUKCJA, ocenia vibes nie fitness. Glimmer: worst-
  evaluator nazwał mechaniczne kryterium, ale jako przykład nie prompt.
- **Werdykt:** **DISPOSE.** Jimmy artykułuje idee, nie pakuje ich w działający scaffold. Wąskie gardło =
  evaluator; soft-evaluator bezużyteczny do selekcji. Rekomendacja: Jimmy=proposer, evaluator/disposer
  deterministyczne. (Prawo siódme.)

## 2026-09-22 — 016: rekurencyjna defensywna dekompozycja zadania (orkiestrowana deterministycznie)
- **Hipoteza (użytkownika):** rekurencyjnie rozkładaj do atomowej warstwy + defensywne kroki (verify preconditiony) = kuloodporny plan.
- **Setup:** orchestrator Python (drzewo/cap/dedup), Jimmy 1 krok/węzeł. Arms: RECURSIVE_DEFENSIVE/PLAIN, SINGLESHOT, bounded depth-2. ~200 req.
- **Wynik:** technika defensywna DZIAŁA: defensive-ratio **0.90 (DEFENSIVE) vs 0.54 (PLAIN)**, +35 pkt.
  ALE rekursja eksploduje (299 liści, trafia cap), Jimmy NIGDY nie mówi ATOMIC (brak samo-terminacji),
  redundancja międzygałęziowa ~20%. Depth-2 (49 liści, 0.78) = użyteczny sweet-spot.
- **Werdykt:** **PARTIAL KEEP.** Defensywne kroki: KEEP (mocno). Głęboka rekursja do „warstwy atomowej":
  DISPOSE (Jimmy nie zna dna → wyznacza je orchestrator). Przepis: płytko+defensywnie+deterministyczny dedup.

## 2026-09-22 — 017: generowanie prawdziwych komend dla kroków z 016 (planner→executor)
- **Hipoteza:** Jimmy generuje realne komendy shell dla ~34 defensywnych kroków (depth-2).
- **Setup:** read-only wykonywane w sandboxie (allowlist+blocklist), mutujące statycznie. SINGLE vs BEST-of-N. 246 req.
- **Wynik:** BEST-of-N: bash -n **1.0**, real-command **1.0**, exec-ok **0.96** (SINGLE: 1.0/0.85/0.65).
  ALE dopasowanie semantyczne tylko **0.79** — ~20% działa-ale-błędne (echo-cheat, zły pkg-manager rpm/apt).
  Jimmy wyemitował `init 6` (REBOOT) dla kroku „verify" — allowlist NIE wykonał (sandbox się obronił).
- **Werdykt:** **KEEP dla FORMY (valid/real/runnable), nie dla INTENCJI** (0.79). best-of-N+exec-filter znów
  wygrywa. Output = przeglądalna draft-automatyzacja; nigdy unattended (Jimmy wstawia destrukcję).

## 2026-09-22 — 018: cztery meta-analityczne testy na komendach (describe/judge/compare/regenerate)
- **Setup:** bank 12 znanych komend read-only z twardym goldem (przeznaczenie, poprawne/błędne zadanie). 216 req.
- **T1 describe:** recall 0.68, faithful **1.0** — KEEP (recall wiedzy).
- **T2 match-judge (bezpośredni):** acc 0.54, mismatch-recall **0.08** — RUBBER-STAMP (bias pozytywny, głosowanie
  nie pomaga). DISPOSE, potwierdza Prawo 7.
- **T3 „opisz→porównaj opisy":** acc **0.83**, differs-recall **1.0** — NAPRAWA +30 pkt; pośredniczenie osądu
  przez wierny opis omija rubber-stamp bias. KEEP (technika).
- **T4 regenerate:** diverse 1.0, valid+real 1.0, output-equiv 0.58 — forma mocna, intencja umiarkowana.
- **Highlight:** T2 vs T3 — ta sama ocena, +30 pkt z przeformułowania „match?" → „describe then compare".

## 2026-09-22 — 019: benchmark logiczny L0-L5 (read/evaluate/validate/analyze)
- **Setup:** instancje generowane programowo, GOLD brute-force w Pythonie. Balanced accuracy (chance=0.5),
  gold zbalansowany 8T+8F/poziom. Głosowanie-5. 720 req (2 biegi).
- **Krzywa (bal_acc):** L0 **0.88** → L1 0.62, L2 0.75, L3 0.69, L4 0.62, L5 0.75 (n=8). READ 0.75.
- **Wynik:** logika zdaniowa (L0) solidna bez biasu; od kwantyfikatorów (L1+) zapada do near-chance (0.6-0.75)
  z uporczywym biasem TRUE (recall_False<recall_True). Głosowanie nie ratuje (bias, Prawo 1).
- **Samo-korekta:** pierwszy bieg dał pozorne L3=1.0/L4=0.83 — ARTEFAKT nierównowagi gold (L4=6T/0F →
  stałe TRUE=1.0). Balanced accuracy + class-balance + true_rate to skorygowały. (Prawo dziewiąte.)
- **Werdykt:** ufaj Jimmy'emu w prostej logice boolowskiej, NIE w kwantyfikatorowej/wyższego rzędu.

## 2026-09-23 — 020: ArchWiki → manpage kompatybilny z man (APLIKACJA)
- **Zadanie:** systemd ArchWiki (~12k tok stripped) → strona man. Arms: A (Jimmy emituje troff), B (Jimmy-treść
  + deterministyczny troff). Walidacja: groff/man renderuje. 11 req.
- **Wynik:** ARM B: renders ✅, **0 warnings**, sekcje NAME/DESC/SEE ALSO, NAME valid, faithfulness 0.86,
  20 komend, 12 SEE ALSO (regex). `man ./systemd.1` otwiera poprawnie. ARM A: renders ale 15 warnings +
  złamany NAME format.
- **Werdykt:** **KEEP** — działające narzędzie. Architektura Praw 6+7: Jimmy=treść, Python=troff/formatowanie;
  chunk→map→reduce hierarchiczny (013). Artefakt: experiments/020.../systemd.1. Jimmy-wprost-troff gorszy fallback.

## 2026-09-23 — 021: manpage → dokumentacja tldr (kompatybilna z `tldr --render`)
- **Zadanie:** man tar / journalctl → strona tldr (Client Spec 2.3). Arms: A (Jimmy wprost md), B (Jimmy
  treść + Python format). Walidacja: tldr --render, checker formatu, faithfulness, coverage vs kanoniczna.
- **Wynik:** tar ARM B: renderuje w PRAWDZIWYM tldr, compliant, faithful 1.0, idiomatyczne przykłady.
  journalctl ARM B: 0 przykładów (niestabilne) → niecompliant. ARM A: zawsze niecompliant (zła struktura).
- **Kluczowe:** jakość SILNIE prompt-zależna — "extract examples" → płytka enumeracja opcji; "najczęstsze
  realne użycia, imperatywne, krótkie flagi" → dobra tldr. Metryka coverage zawiodła (łapała ścieżki).
  Nawet det-URL błędny dla journalctl.
- **Werdykt:** **PARTIAL KEEP** — draft-generator dla bogatych manpage'y (tar) + precyzyjny prompt + hybrid;
  niestabilny per-komenda, wymaga human-review. Forma OK, kuracja/intencja słaba i prompt-zależna.

## 2026-09-28 — 022: Jimmy jako generator syntetycznych danych treningowych (dowód downstream)
- **Zadanie:** AG News 4-klasy. Ten sam klasyfikator trenowany na danych z różnych źródeł, mierzony
  macro-F1 na PRAWDZIWYM gold test. Dwaj studenci: A=Multinomial NB (numpy, deterministyczny bag-of-words,
  gold 2000), B=ICL (Jimmy few-shot, gold 160). N=400 (100/klasę) dopasowane. Ramiona: FLOOR / REAL /
  JIMMY-IID / JIMMY-NOVELTY (003b: pamięć+presja nowości).
- **Próg (pre-rejestrowany):** domknięcie luki G=(F1_j−F1_floor)/(F1_real−F1_floor) ≥0.50 ok, ≥0.75 dobry;
  mode collapse gdy distinct<0.90.
- **Wynik:** NB (floor=majority 0.10) — REAL 0.796, IID 0.617 (**G=0.74**), NOVELTY 0.429 (G=0.47).
  ICL (floor=ZERO-SHOT 0.517, bo Jimmy już umie klasyfikować newsy) — REAL 0.729, IID 0.665 (**G=0.70**),
  NOVELTY 0.713 (G=0.93); trzy źródła nierozróżnialne między sobą (SE≈0.033, IID vs NOVELTY 1.4 SE), ale
  wszystkie >zero-shot o >3 SE (egzemplarze niosą sygnał, głównie na Sci/Tech: zero-shot recall 0.0).
  NOVELTY rozjeżdża studentów: u NB gorszy (delta 0.188 ≫ std 0.018), u ICL ≈ IID. Dwa realne deficyty
  puli Jimmy vs REAL @N: pokrycie (vocab 2142/1998 vs 4583) ORAZ wierność etykiet (self-check 0.83/0.74,
  style-gap 0.94/0.83) — NOVELTY gorszy na OBU (nie kupił pokrycia). distinct_rate=1.0 = zły przyrząd.
- **Werdykt:** **KEEP** (Jimmy = użyteczny generator danych treningowych dla studentów bag-of-words/ICL na
  klasyfikacji tematycznej) + **DISPOSE presji nowości bez twardego checkera** (dryf etykiet + degradacja
  przy długim kontekście pamięci). Przepis: IID + deterministyczny dedup + opcjonalny filtr forced-4-way.
  **OTWARTE:** dane SFT dla dostrajanego LM (nietestowane; torch dostępny).

<!-- następne wpisy poniżej -->

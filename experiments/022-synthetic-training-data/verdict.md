# 022 — werdykt: KEEP (z ostrym zakresem)

**Jimmy potrafi wygenerować użyteczny zbiór treningowy** dla klasyfikacji tematycznej 4-klasowej —
mierzone downstreamem na prawdziwym gold test AG News (nie opinią). Najlepszy przepis to
**naiwna generacja IID + deterministyczny dedup**, a NIE presja nowości.

## Liczby (N=400, 100/klasę, dopasowane; próg G: ok≥0.50, dobry≥0.75)

| Student | floor | REAL (sufit) | JIMMY-IID | JIMMY-NOVELTY |
|---|---|---|---|---|
| **A: NB (bag-of-words, gold 2000)** | majority F1 0.10 | **0.796** | 0.617 → **G=0.74** | 0.429 → G=0.47 ❌ |
| **B: ICL (Jimmy few-shot, gold 160)** | **zero-shot F1 0.517** | 0.729 | 0.665 → **G=0.70** | 0.713 → **G=0.93** |

**Uwaga o floorach.** Dla NB floor = klasa większościowa (nieuczony bag-of-words nic nie wie). Dla
ICL floor = **zero-shot** (Jimmy już umie klasyfikować newsy: zero-shot F1 0.517), bo majority
byłby nieuczciwy — zawyżałby G. Bootstrap SE po 160 itemach ICL ≈ **0.033** na ramię.

## Co mówią liczby
1. **NB — czyste KEEP dla IID.** IID domyka lukę floor→REAL w 0.74; delta IID−NOVELTY = 0.188 ≫
   łączne std 0.018 (istotne). NOVELTY poniżej progu.
2. **ICL — egzemplarze Jimmy'ego realnie pomagają, ale źródło danych nie różnicuje.** Wszystkie
   ramiona > zero-shot o >3 SE (IID +0.148, NOVELTY +0.196), więc syntetyczne egzemplarze niosą
   sygnał (G 0.70–0.93). ALE między sobą REAL/IID/NOVELTY są **statystycznie nierozróżnialne**
   (IID vs NOVELTY = 0.048 ≈ 1.4 SE). Egzemplarze pomagają najbardziej na najtrudniejszej klasie
   Sci/Tech (zero-shot recall **0.0** → REAL 0.45 / NOVELTY 0.25 / IID 0.175).

## NOVELTY (003b) rozjeżdża studentów — i przegrywa na własnym celu
- **U NB znacząco GORSZY** (0.429 vs IID 0.617); u ICL nierozróżnialny od IID.
- **Dwa realne deficyty puli Jimmy vs REAL przy równym N, NOVELTY gorszy na OBU:**
  - **pokrycie leksykalne:** vocab REAL **4583** vs IID **2142** vs NOVELTY **1998**. Pule Jimmy mają
    <½ słownika realnych danych; NB ignoruje OOV przy predykcji → deficyt wprost zasila lukę
    downstream. **NOVELTY nie kupił nawet pokrycia** (1998 < 2142) — 003b zawiódł na SWOIM celu.
  - **wierność etykiet:** self-check forced-4way 0.83 (IID) vs 0.74 (NOVELTY); style-gap agreement
    (model-REAL→pula) 0.94 vs 0.83 → dryf etykiet.
- **`distinct_rate` był złym przyrządem:** ≈1.0 z konstrukcji dla generowanej prozy, próg 0.90 nie
  mógł się odpalić. Kolaps na poziomie *dokumentu* nie wystąpił, ale kolaps na poziomie *słownika*
  (pokrycie) — owszem. Nie czytać nie-odpalenia progu jako „pokrycie OK".
- **Mechanizm (skonfundowany):** presja nowości była **implementowana przez wstrzykiwanie pamięci
  tematów do promptu** → dwa efekty naraz: (a) pogoń za „innymi tematami" = dryf ku treści
  granicznej (label noise), (b) dłuższy prompt = degradacja generacji (późne próbki urwane:
  „…partners with UK-based airline;"), zgodne z charakterystyką *instruction-following pada przy
  długim kontekście*. DISPOSE dotyczy tej implementacji.

## Dlaczego studenci się rozjeżdżają
Bag-of-words uczy się wprost słowo→klasa → szum etykiet i braki słownika zatruwają statystyki
(recall Sports 0.21, Business 0.32 w NOVELTY). ICL używa tylko k=8 egzemplarzy + własnej
generalizacji Jimmy'ego → kilka zaszumionych/wąskich przykładów waży mniej. **Wartość interwencji na
danych zależy od wrażliwości studenta na szum etykiet i pokrycie.**

## Tani deterministyczny proxy jakości
Diagnostyka **style-gap** (model trenowany na REAL przewiduje etykiety puli Jimmy: IID 0.94 vs
NOVELTY 0.83) przewidziała ranking downstream **bez** sędziego-Jimmy'ego.

## Zakres (nie przekraczać)
- Twierdzenie: „Jimmy = użyteczny generator danych treningowych **dla studentów bag-of-words / ICL
  na 4-klasowej klasyfikacji tematycznej**".
- **OTWARTE (nietestowane):** dane **SFT dla dostrajanego LM** (prawdziwy fine-tuning) — inny reżim,
  inny student. torch+transformers dostępne → osobny eksperyment.
- **DISPOSE:** presja nowości implementowana przez wstrzykiwanie pamięci do promptu — na tym zadaniu
  szkodzi (dryf etykiet, brak zysku pokrycia, degradacja długim kontekstem).

## Rekomendowany przepis produkcyjny
Jimmy generuje IID per-klasa (batch, bez pamięci) → **deterministyczny dedup (n-gram Jaccard)** →
opcjonalnie **filtr forced-4-way self-classification** (usuń próbki, które Jimmy sam wrzuca do innej
klasy) jako tani gate wierności etykiet. Liczy się wolumen + gate wierności; osobno warto zwiększać
pokrycie leksykalne (np. seedowanie tematami), bo to drugi wiążący deficyt.

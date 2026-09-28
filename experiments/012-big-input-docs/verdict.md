# 012 — WERDYKT: **relewancja i zwięzłość biją rozmiar** — "duży input" przegrywa, celny mały wygrywa

324 requesty, 0 błędów. Baza: best-of-N (jak zwycięskie ramię 011), wariowany tylko kontekst.

## Wyniki (pass-rate przez wykonanie, M=3)
| kontekst | ~tok | sequence | pipeline | overall | vs NONE |
|----------|------|----------|----------|---------|---------|
| NONE | 0 | 44.4 | 33.3 | 38.9 | — |
| **CHEATSHEET (celny)** | 160 | **100.0** | **88.9** | **94.4** | **+55.5** |
| MANBASH_4K (generyczny, pod limitem) | 4000 | 44.4 | 55.6 | 50.0 | +11.1 |
| MANBASH_OVER (nad limitem) | 10000 | 0.0 | 0.0 | **0.0** | −38.9 |

## Odpowiedź na "dorzuć całą dokumentację bash"
1. **Naiwny dump całości → 0%.** `man bash` = ~98k tok (16× limit ~6k); nawet 10k tok niszczy output
   (instruction-following kolapsuje / brak sensownej odpowiedzi). Dosłowny "duży input" **PRZEGRYWA**.
2. **Duży generyczny dump w budżecie (4k) ledwo pomaga (+11 pkt).** Irrelewantny kontekst rozcieńcza
   sygnał; ryzyko degradacji instruction-following z Fazy 0. Niewart 4000 tokenów.
3. **Mały CELNY cheatsheet (~160 tok) = przełom: 39%→94% (+55 pkt).** Pierwsza interwencja, która
   radykalnie przebiła sam best-of-N (011: ~47%).

## Właściwy wniosek (odwrotność intuicji "big input")
Wygrywa nie ROZMIAR wejścia, lecz **RELEWANCJA przy minimalnej wielkości**. Błędy Jimmy'ego w bashu to
w dużej mierze **luki wiedzy** (jak zrobić X), nie brak rozumowania — wstrzyknięcie DOKŁADNIE właściwego
snippetu je zasypuje. Ale kontekst musi (a) zmieścić się grubo pod ~6k, (b) mieć wysoki stosunek
sygnału do szumu (generyczny man bash rozcieńcza).

**Strategia dla Jimmy'ego: inwestuj w RETRIEVAL właściwego małego fragmentu, nie w dump dużego
kontekstu.** Zwycięski przepis na kod: **celny cheatsheet (RAG) + best-of-N + weryfikator wykonania**
(94%).

## Uczciwa uwaga o górnej granicy
Cheatsheet był dopasowany do tych 6 zadań (≈ "oracle RAG", perfekcyjny retrieval) → 94% to GÓRNA
granica. Realny RAG (retrieval per zadanie z korpusu) byłby między CHEATSHEET a MANBASH_4K. Ale
kontrast oracle(+55) vs generyczny-dump(+11) vs over-limit(0) jest jednoznaczny: **jakość retrievalu
dominuje; rozmiar szkodzi.** To rafinuje "big input → small output" na **"minimal relevant input →
small output"**.

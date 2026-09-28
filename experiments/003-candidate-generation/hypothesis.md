# 003 — Jimmy jako generator kandydatów dla mądrzejszego konsumenta

## Hipoteza
Najlepszy fit dla profilu "szybki, głupi, darmowy": Jimmy generuje wiele *zróżnicowanych*
kandydatów (różnorodność=1.0 z Fazy 0), a deterministyczny selektor wybiera. **Różnorodność jest
produktem; jakość per-próbka jest nieistotna.** To także rdzeń mechanizmu Świętego Graala
(Jimmy = operator wariacji, selektor = presja selekcyjna).

## Część A — Pokrycie (diversity → coverage)
Zadanie: "wymień jeden element ze zbioru X" (kraje Europy, stany USA). Checker = przynależność
do zbioru (samowystarczalny, hardkodowany). Metryka: **distinct-valid coverage vs N**.
- **Próg KEEP:** coverage(N=40) ≥ 3× coverage(N=1) ORAZ ≥ 40% przestrzeni pokryte.
- Sens: single-shot pokrywa ~1 punkt; wolumen ma odblokować dużą część przestrzeni.

## Część B — Zysk z selekcji (smarter consumer picks)
Zadanie: "napisz najkrótsze zdanie zawierające słowa {A,B,C}". Scorer (deterministyczny):
walidne iff zawiera wszystkie 3 słowa → objektyw = liczba słów (minimalizuj). best-of-N = min.
Metryka: **best-of-20 vs średnia single-shot** (długość walidnego zdania).
- **Próg KEEP:** best-of-20 skraca objektyw o ≥25% vs średnia single-shot, przy zachowanej
  walidności (≥1 walidny kandydat w każdym zadaniu).

## Wspólne
topK=8, retry, conc=8. Coverage estymowany bootstrapem z puli ~60 próbek/prompt.

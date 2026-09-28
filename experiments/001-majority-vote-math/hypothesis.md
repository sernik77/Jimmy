# 001 — Głosowanie większościowe na zadaniach matematycznych (self-consistency)

## Hipoteza
Głupota Jimmy'ego per-próbka jest kompensowalna wolumenem. Konkretnie: na zadaniach
arytmetyczno-słownych, gdzie odpowiedź (liczba) jest **darmowa do zweryfikowania**,
głosowanie większościowe po k niezależnych próbkach (topK=8, różnorodność=1.0) podniesie
accuracy istotnie ponad single-shot.

## Metryka i próg
- `accuracy@1` — pojedyncza próbka (baseline).
- `accuracy@vote-k` dla k ∈ {1,3,7,15,31} — większość z wyekstrahowanych odpowiedzi liczbowych.
- **Próg KEEP:** vote-31 daje wzrost ≥ +15 punktów procentowych względem @1
  ORAZ osiąga ≥ 70% absolutnie. Inaczej DISPOSE (voting nie ratuje 8B na tej klasie).

## Setup
- 24 zadania arytmetyczno-słowne / logiczne z jednoznaczną odpowiedzią liczbową (gold).
- System prompt wymusza format `FINAL: <liczba>`; ekstrakcja regexem, głos na liczbę.
- topK=8, ~31 próbek/zadanie (współbieżnie), retry na błędy.

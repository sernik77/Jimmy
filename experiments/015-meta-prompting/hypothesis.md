# 015 — Problem-solving / meta-prompting: Jimmy generuje scaffold propose/dispose/evaluate

## Pytanie
Jimmy dostaje przykład problemu i ma wygenerować trzy prompty (PROPOSER / EVALUATOR / DISPOSER).
Czy potrafi zaprojektować DZIAŁAJĄCE rusztowanie problem-solvingu? Ocena = FUNKCJONALNA: uruchamiamy
wygenerowany scaffold na zadaniu z obiektywnym goldem i mierzymy wynik.

## Dwie osobne miary (advisor)
- **Structural success:** czy z M meta-generacji wychodzą 3 różne, parsowalne, niepuste prompty
  (kontrakt delimitera `=== PROPOSER/EVALUATOR/DISPOSER ===`). BEZ ręcznej naprawy.
- **Execution success:** warunkowo na sparsowaniu — czy pętla rozwiązuje zadanie.

## Zadania
- **PTASK (dyskryminujące):** zdanie zawierające quantum/velvet/zebra, maksymalizuj słowa na 'p',
  ≤12 słów, distinct. Sprawdzanie TRYWIALNE (fitness deterministyczny, ukryty przed scaffoldem),
  generacja trudna → kompetentny evaluator POWINIEN pomóc. Tu scaffold ma pole do popisu.
- **MATH (null-check):** zadania arytmetyczne z 001. Evaluator nie zweryfikuje arytmetyki
  (sprawdzanie≈rozwiązywanie) → przewidziany null (jak 008).

## Ramiona (parytet budżetu: scaffold = N proposer + N evaluator + 1 disposer ≈ 2N+1)
- JIMMY_BEST — najlepszy strukturalnie scaffold Jimmy'ego.
- JIMMY_WORST — najgorszy strukturalnie (wariancja to wynik).
- HUMAN — moje prompty (baseline kompetencji).
- BESTOFN_DET — 2N+1 kandydatów, wybór DETERMINISTYCZNYM checkerem (PTASK) / większością (MATH) = sufit.

## PRE-REJESTROWANA predykcja
**Jimmy-scaffold ≤ HUMAN-scaffold ≤ BESTOFN_DET.** Jeśli ta kolejność się utrzyma: "meta-prompting daje
rusztowanie wykonywalne-ale-nie-lepsze; deterministyczny weryfikator pozostaje sufitem" (spójne z 003/008).
KEEP "Jimmy projektuje działające scaffoldy" jeśli JIMMY_BEST ≥ 0.8×HUMAN ORAZ ≥ BESTOFN_DET − 15%.

## Co byłoby ZASKOCZENIEM (flagować)
Jeśli evaluator Jimmy'ego zakoduje MECHANICZNY check (np. "sprawdź, czy zdanie zawiera wszystkie 3
wymagane słowa") zamiast vibes — to realna meta-zdolność (rozpoznanie struktury weryfikacji).

Prompty wygenerowane pokazać DOSŁOWNIE (artefakt = połowa dostawy).

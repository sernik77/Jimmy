# 008 — WERDYKT: **DISPOSE** — krytyk poprawia draft, ale przegrywa z best-of-N o równym budżecie

224 requesty, 0 błędów. Forma z ukrytym scorerem (krytyk nie znał funkcji konkretności).

## Wynik
| | średni ukryty score |
|---|---------------------|
| refine gen0 (naiwny draft) | 3.14 |
| **refine final** (gen + 3× krytyka/rewizja) | **4.01** (+28% vs gen0) |
| **best-of-N** (równy budżet = 7 próbek) | **4.58** |

- Krytyk-w-pętli POPRAWIA nad pojedynczym draftem (3.14→4.01). Pętla nie jest bezwartościowa.
- Ale **best-of-N o TYM SAMYM budżecie bije ją** (4.58 > 4.01) → **KEEP=False.**

## Dlaczego (potwierdza prawa 1 i 3 na nowej architekturze — agenci asymetryczni)
- **Prawo 1:** krytyk dzieli wagi (i bias) generatora → nie widzi więcej niż generator; jego
  miękkie wskazówki bywają NIEZGODNE z prawdziwym celem. Widać per-element: wieloryb 1.91→**0.69**,
  nurek utknął 1.85 gdy próbkowanie dało 5.00 — krytyk czasem AKTYWNIE psuje, sterując "ku żywości"
  własnej definicji, nie ku ukrytemu score.
- **Prawo 3:** to pętla OPTYMALIZACJI (jeden output, iterowana poprawa) → próbkowanie wygrywa,
  bo 7 niezależnych zróżnicowanych próbek gęściej trafia w cel niż 3 skorelowane rewizje.

## Wniosek praktyczny
**Jeśli masz JAKIKOLWiEK scorer → best-of-N bije pętlę krytyka przy równym budżecie.** Pętla
generator↔krytyk uzasadniona tylko gdy NIE MASZ żadnego sposobu oceny outputu — i nawet wtedy daje
tylko poprawę nad jednym draftem, nie przewagę nad próbkowaniem. Asymetryczni agenci jako źródło
emergencji: na zadaniu optymalizacyjnym — nie. (Ich nisza to prawdopodobnie zadania nie-optymalizacyjne,
np. generowanie dialogu/negocjacji jako artefaktu — nietestowane.)

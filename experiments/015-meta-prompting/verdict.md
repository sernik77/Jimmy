# 015 — WERDYKT: **DISPOSE** — Jimmy artykułuje właściwe idee, ale nie umie ich spakować w działający scaffold

552 requesty, 0 błędów. Predykcja pre-rejestrowana potwierdzona.

## Wyniki
| miara | wynik |
|-------|-------|
| **Structural rate** (3 parsowalne, różne prompty z M=5) | **0.60** (2/5 malformed) |
| PTASK fitness — JIMMY_BEST | **0.00** |
| PTASK fitness — JIMMY_WORST | 0.00 |
| PTASK fitness — HUMAN scaffold | 2.38 |
| PTASK fitness — **BESTOFN_DET (sufit)** | **8.88** |
| eval-parse-rate (evaluator produkuje SCORE:) | 1.00 |
| MATH null-check: JIMMY_BEST vs MAJVOTE | 100% = 100% |

**Kolejność Jimmy(0) ≤ HUMAN(2.38) ≤ BESTOFN_DET(8.88): POTWIERDZONA.** KEEP=False.

## Diagnoza z artefaktów (dlaczego fitness=0)
Wygenerowany PROPOSER (best) — restytuuje ograniczenia, ALE jego własny przykład ma **14 słów**
przy limicie ≤12 → prowadzi model do zdań NIEWALIDNYCH (fitness 0):
> *"...the zebra painted a pocket with a precious plastic purse"* (14 słów)

Wygenerowany EVALUATOR (best) — **zepsuty jako system-prompt**: napisany jak konkretna ODPOWIEDŹ z
zahardkodowanymi przykładami ("Please score the following sentences: 1... 2... 3..."), nie jak ogólna
INSTRUKCJA oceniania DOWOLNEGO kandydata. Kryteria: "coherence, creativity, relevance" — NIE prawdziwy
fitness (liczba słów na 'p' + obecność wymaganych). Więc selekcja na szumie.

DISPOSER — mętny ("choose the sentence with the highest score").

## Glimmer meta-zdolności (flaga advisora)
EVALUATOR z WORST-scaffoldu pokazał quasi-MECHANICZNE rozumowanie:
> *"Includes all required words 'quantum','velvet','zebra'. 6/12 words start with 'p'..."*

Jimmy POTRAFI nazwać właściwe kryterium weryfikacji — ale piecze je jako jednorazowy PRZYKŁAD, nie
jako reużywalny prompt. Rozpoznanie struktury jest, pakowanie w funkcjonujący prompt — nie ma.

## Wniosek
**Meta-prompting = open-ended generation (słabość z Prawa 2) + zrozumienie abstrakcji
"instrukcja-szablon vs przykładowa-odpowiedź", którego Jimmy nie ma.** Skutek: scaffold zepsuty na
każdym etapie subtelnie (proposer łamie własne ograniczenia, evaluator to zapieczony przykład na złych
kryteriach, disposer mętny). Nawet mój HUMAN scaffold (2.38) ≪ deterministyczna selekcja (8.88), bo
KAŻDA selekcja przez soft-evaluatora (Jimmy'ego lub człowieka) nie śledzi prawdy — **wąskim gardłem
jest evaluator, a soft-evaluator jest bezużyteczny do selekcji** (spójne z 008).

**Deterministyczny weryfikator (8.88) pozostaje sufitem — nieosiągalnym przez żaden generowany/soft
scaffold.** MATH null potwierdzony (100%=100%: na łatwych evaluator ani pomaga, ani szkodzi).

## Rekomendacja
Nie każ Jimmy'emu PROJEKTOWAĆ pętli problem-solvingu. Sam scaffold (proposer/evaluator/disposer)
autoruj deterministycznie/człowiekiem; Jimmy używaj tylko jako PROPOSERA (generator różnorodności),
a EVALUATOR/DISPOSER trzymaj deterministyczne. To dokładnie zwycięski przepis całego projektu:
best-of-N (Jimmy proponuje) + deterministyczny weryfikator (nie Jimmy ocenia).

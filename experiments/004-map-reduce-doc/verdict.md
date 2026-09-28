# 004 — WERDYKT: **KEEP** (aplikacja) — map-reduce bije limit kontekstu 100→0

34 requesty, 0 błędów.

## Wynik
| | recall | uwaga |
|---|--------|-------|
| single-shot (cały dok ~15.8k tok) | **0.00** (0/24) | prefill=None → PUSTA odpowiedź (>limit ~6k) |
| **map-reduce** (33 chunki × ~250 słów, równolegle) | **1.00** (24/24) | 34 req łącznie, ~1 s |

Lift **+100 pkt**. Próg (MR≥0.9 i lift≥30): **spełniony maksymalnie.** Nic nie pominięto.

## Znaczenie
Dokument 2.6× powyżej limitu kontekstu Jimmy'ego. Single-shot zwraca PUSTKĘ (efekt z Fazy 0:
≥8k tok → brak odpowiedzi) — czyli zadanie, którego Jimmy **dosłownie nie potrafi** wykonać wprost.
Map-reduce (podziel ≤~1.2k tok → ekstrakcja per chunk równolegle → unia) daje **100% recall** za
cenę 33 równoległych requestów (~1 s przy conc=8).

To kanoniczna, produkcyjna aplikacja: **przetwarzanie długich dokumentów przez równoległe
chunkowanie**. Łączy trzy potwierdzone własności: limit kontekstu (Faza 0), niezawodną ekstrakcję
(002) i przepustowość ~38 req/s (dźwignia = równoległość). Reużywalny wzorzec:
`chunk(≤1.2k tok) → map_prompts(ekstrakcja) → reduce(unia/dedup)`.

## Granica
Zadanie było ekstrakcją faktów lokalnych w chunku (recall). Reduce = prosta unia. Zadania wymagające
rozumowania PONAD chunkami (agregacja, korelacje między odległymi fragmentami) potrzebowałyby
wielopoziomowego reduce — nietestowane tu, ale wzorzec się skaluje.

# 006 — ŚWIĘTY GRAAL: Jimmy jako operator mutacji w algorytmie genetycznym

## Teza emergencji
Jimmy karmiony własnym outputem kolapsuje (fixed-point/cykl). ALE w pętli z (a) skalarnym fitnessem,
(b) selekcją i (c) presją różnorodności — struktura akumuluje się w POPULACJI, nie w wagach.
Właściwość emergentna = best-fitness rośnie przez generacje i **bije kontrolę o równym budżecie**
(czyste próbkowanie bez ewolucji). To znaczy: pętla odkrywa to, czego samo próbkowanie nie znajduje.

## Zadanie i fitness (PRE-REJESTRACJA — zamrożone przed uruchomieniem)
Ewoluować zdanie maksymalizujące aliterację na literze docelowej T='p'.
```
words = alfabetyczne tokeny, lowercase
fitness = 0  jeśli NIE (3 <= len(words) <= 12)          # ograniczenie długości
fitness = 0  jeśli są powtórzone słowa (len(set)<len)   # zabija degenerację
fitness = liczba słów zaczynających się na T            # max = 12
```
Niewalidne potomstwo → fitness 0, ZOSTAJE w populacji (ginie przez selekcję), nie odrzucane po cichu.
**Ryzyko gamingu:** wysoki fitness może = word-salad. Dlatego werdykt MUSI zawierać top-5 championów
dosłownie — czytelnik ocenia jakość. "Fitness 3→9 do gibberish" to uczciwe DISPOSE, nie ukrywamy.

## Cztery ramiona (identyczny budżet requestów: seed P + G×P)
- **A — pełny GA:** przeżywalność = top-P wg fitness (elityzm) + dedup + wstrzyknięcie losowych
  seedów gdy różnorodność spada (anti-collapse z 003b).
- **B — losowa selekcja:** ta sama pętla/budżet, ale przeżywalność LOSOWA (bez fitness).
  Izoluje: czy wygrywa presja selekcyjna, czy samo iterowane przepisywanie?
- **C — baseline kolapsu:** potomstwo zastępuje rodziców 1:1, BEZ selekcji/dedup/restartu.
  Mierzy generację kolapsu (czyste karmienie się własnym outputem).
- **D — kontrola best-of-N:** R = tyle samo requestów co jedno ramię, single-shot promptu z
  JASNO postawionym celem (jak mutacja), max fitness. "Próbkowanie bez ewolucji".

Parametry: P=16, G=15, T='p'. Budżet/ramię = 16 + 15×16 = 256 req; ×4 ≈ 1024 req.

## Progi KEEP (zamrożone)
1. **Emergencja:** A_best ≥ D_best + 2 ORAZ A_best ≥ 1.25 × D_best.
2. **Selekcja ma znaczenie:** A_best > B_best.
3. **Anti-collapse działa:** C kolapsuje (distinct_rate < 0.3 do końca) PODCZAS GDY A trzyma
   distinct_rate ≥ 0.6 przez cały bieg.

Jeśli 1 nie przejdzie → **DISPOSE** ("Jimmy jako operator mutacji nie bije próbkowania o równym
budżecie") — to publikowalny wynik, nie iterujemy fitnessu aż da wygraną.

## Raportowane per generacja per ramię
best_fitness, mean_fitness, distinct_rate(pop), offspring_validity_rate. + top-5 championów (tekst).

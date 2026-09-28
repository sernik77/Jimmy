# 001 — WERDYKT: **KEEP** (zdecydowanie)

## Wynik
744 requesty, 0 błędów. Krzywa accuracy@vote-k (bootstrap B=300, losowanie ze zwracaniem, 24 zadania):

| k | accuracy | ± std |
|---|----------|-------|
| 1 | 64.2% | 8.4 |
| 5 | 81.2% | 6.1 |
| 11 | 88.6% | 4.3 |
| 21 | 91.3% | 3.4 |
| 31 | **92.0%** | 2.9 |

Próg (vote-31 ≥ +15 pkt i ≥70%): **spełniony** — lift +28 pkt, monotoniczny wzrost, plateau ~92% @ k≈21-31.
(Wcześniejsza wersja miała artefakt: `sample` bez zwracania degenerował k=31 do std=0; poprawione na `choices`.)

## Wnioski
- **Teza projektu potwierdzona:** głupota kompensowalna wolumenem, gdy weryfikacja tania.
  65% → 93% samym głosowaniem, koszt ~21 równoległych próbek ≈ 0.5 s wall.
- **Głosowanie naprawia wariancję, nie bias.** 2/24 zadania zawodzą, bo Jimmy *konsekwentnie*
  źle je rozumie (np. "pays double each of the others" → większość głosuje 60 zamiast 45).
  Systematyczny błąd 8B jest niereparowalny głosowaniem — to twardy sufit metody.
- **Plateau przy k≈15-21.** Powyżej brak zysku. To praktyczny sweet-spot: ~15 próbek.
- std maleje z k → więcej próbek = nie tylko lepiej, ale i stabilniej.

## Wykorzystanie
Wzorzec produkcyjny: **best-of-N z deterministycznym weryfikatorem/głosowaniem** dla każdego
zadania, gdzie (a) odpowiedź da się tanio sprawdzić lub zagregować, (b) błędy 8B są losowe, nie
systematyczne. Reużywalne w `jimmy/eval.py::majority_vote`.

## Następny krok
Czy działa też tam, gdzie weryfikator jest *twardy* (nie głosowanie, lecz walidator schematu)?
→ eksperyment 002: ekstrakcja strukturalna JSON z best-of-N + walidator.

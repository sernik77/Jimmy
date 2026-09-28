# 019 — WERDYKT: logika zdaniowa OK (0.88), kwantyfikatory/wyższe rzędy ≈ chance

720 requestów (2 biegi), 0 błędów. Gold liczony w Pythonie (brute-force). Metryka: **balanced accuracy**
(chance = stała odpowiedź = 0.50), gold zbalansowany 8T+8F/poziom (L5: 4T+4F ręczne).

## Krzywa logiczna (balanced acc, chance=0.50)
| poziom | bal_acc | recall_True | recall_False | true_rate | n |
|--------|---------|-------------|--------------|-----------|---|
| **L0 propositional** | **0.88** | 0.88 | 0.88 | 0.50 | 16 |
| L1 first-order | 0.62 | 0.75 | 0.50 | 0.62 | 16 |
| L2 second-order | 0.75 | 0.88 | 0.62 | 0.62 | 16 |
| L3 third-order (funkcje) | 0.69 | 0.62 | 0.75 | 0.44 | 16 |
| L4 fourth-order (właściwości podzbiorów) | 0.62 | 0.75 | 0.50 | 0.62 | 16 |
| L5 fifth-order (ręczne) | 0.75 | 0.75 | 0.75 | 0.50 | 8 |
| READ (parsowanie strukturalne) | 0.75 | — | — | — | 4 |
| per-op: evaluate 0.71, validate 0.75 | | | | | |

## Wnioski
1. **Logika zdaniowa (L0): naprawdę sprawny — 0.88, bez biasu klasowego** (true_rate 0.50). Jimmy
   ogarnia rachunek zdań (tautologie, ewaluacja pod wartościowaniem) solidnie.
2. **Od kwantyfikatorów w górę (L1-L5): mierny, 0.62-0.75 — ledwo ponad chance.** Wielki spadek z L0.
   Krzywa NIE jest gładko monotoniczna (L2>L1, przy n=8-16 to szum), ale sygnał jest jasny: gdy
   wchodzą ∀/∃ i typy wyższego rzędu, rozumowanie zapada się w pasmo „ledwo lepiej niż rzut monetą".
3. **Utrzymujący się bias TRUE** (true_rate 0.62 na L1/L2/L4, recall_False < recall_True) — Jimmy
   skłania się ku „prawda", myląc połowę przypadków FALSE. Ta sama skłonność rubber-stamp co 018 T2.
4. To wyniki @vote-5 — głosowanie nie ratuje wyższych rzędów, bo to BIAS/niezdolność, nie wariancja
   (Prawo 1: wolumen naprawia wariancję, nie bias).
5. READ (parsowanie strukturalne: liczba kwantyfikatorów, rząd) 0.75 — Jimmy w miarę parsuje formuły,
   nie doskonale.

## Samo-korekta metodologiczna (ważne)
Pierwszy bieg dał pozornie „L3=1.00, L4=0.83" — ARTEFAKT nierównowagi gold: L4 miał 6T/0F, więc stała
odpowiedź „TRUE" dawała 1.00, a Jimmy i tak był poniżej. To ta sama pułapka co rubber-stamp 018 T2.
**Balanced accuracy + zbalansowany gold + pomiar true_rate** to skorygowały. Bez tego benchmark
kłamałby. (Lekcja ogólna dla oceny każdego binarnego zadania: raportuj balanced accuracy i class-balance.)

## Podsumowanie
Zdolności logiczne Jimmy'ego są **ostro warstwowe: solidne na poziomie zdaniowym (L0≈0.88), zapadają
do near-chance przy logice kwantyfikatorowej i wyższych rzędach (L1-L5≈0.6-0.75)**, z uporczywym
biasem ku „prawda". Praktycznie: ufaj Jimmy'emu w prostej logice boolowskiej (z best-of-N/weryfikacją),
NIE w rozumowaniu kwantyfikatorowym/wyższego rzędu — tam jest niewiele lepszy niż losowo.

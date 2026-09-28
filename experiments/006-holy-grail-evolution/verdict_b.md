# 006b — WERDYKT: **DISPOSE emergencji-jako-optymalizacji** (potwierdzone na trudnym celu)

1024 requesty, 0 błędów. Cel nienasycalny-w-założeniu (koniunkcja: 3 rzadkie słowa + aliteracja 'p').

## Wyniki vs progi (pre-rejestrowane)
| | wynik | |
|---|-------|---|
| Emergencja: A_best ≥ D+3 i ≥1.25D | A=20, **D(kontrola)=20** → False | ❌ |
| Selekcja ma znaczenie: A>B | **20 ≫ 0** → True | ✅ (silnie) |

Championi A: `[20] "Physicists pondered the quantum properties of zebra's unusual velvet paw patterns."`
Kontrola D top: `[20] "The puzzled physicist precisely painted pictures of a zebra on velvet quantum."` (+ 4 kolejne ≥19)

## Właściwy wniosek (kluczowy dla całego projektu)
**best-of-N o równym budżecie to skrajnie silny baseline — i ewolucja go nie bije** (A=D=20 dwa razy).

ALE uwaga na confound (weryfikacja offline z results_b.json): ramię A miało 20 **już w seedzie
(gen 0)** i **żadne potomstwo nigdy nie przebiło 20** przez 15 generacji — elityzm trzymał wartość
seedową, nic lepszego nie powstało. Kontrola też 20. A konstruowalne max = 24 (9 słów na 'p' +
3 wymagane×5), **nieosiągnięte przez ŻADNĄ metodę.** Zatem sufit ustawiony w punkcie startowym i
nieruszony przez nikogo → wiążącym ograniczeniem jest **zdolność Jimmy'ego per-wyjście** (nie umie
spełnić pełnej koniunkcji), NIE strategia przeszukiwania. Obie metody stoją pod tą samą ścianą.

**Czego NIE wolno twierdzić:** że próbkowanie "gęsto pokrywa przestrzeń" — nie pokrywa, bo istnieją
rozwiązania 24, których nie znalazło. Uczciwa, węższa teza: *ewolucja nie pobiła próbkowania na
żadnym z celów, ale sufit był seedowy i nieruszony, więc wiązała zdolność per-wyjście, nie search.
Test, w którym ewolucja MOGŁABY wygrać, wymaga celu z optimum poza zasięgiem jednego wyjścia — a
żaden z tych nim nie był.*

**Emergencja-jako-optymalizacja nie zmaterializowała się w tym reżimie.** Wariant GA Świętego Graala
zamknięty: gdy optimum mieści się w jednym wyjściu, pętla nic nie dodaje.

## Co ramiona nauczyły (pozytyw)
- **Selekcja jest konieczna do UTRZYMANIA jakości, nie do jej przekroczenia.** A=20 ≫ B=0:
  bez presji fitness populacja dryfuje w niewalidność (potomstwo ~6-38% walidne, 003A) i kolapsuje
  do 0. Selekcja tylko utrzymuje poziom, który próbkowanie i tak osiąga.
- **C (czyste przepisywanie) ≈ 0** — błądzenie losowe, sporadyczne trafienia.

## Rozstrzygnięcie Świętego Graala (patrz HOLY_GRAIL.md)
Emergentna pętla NIE ma sensu jako optymalizacja (próbkowanie wygrywa). Ma sens tam, gdzie
**rozwiązanie NIE mieści się w jednym wyjściu** — gdy trzeba AKUMULOWAĆ strukturę większą niż
pojedyncza generacja, w stanie zewnętrznym. To dokładnie 003b (pokrycie 44 krajów: żadne wyjście
nie zawiera 34 krajów; struktura powstała przez akumulację między rundami). **Graal to akumulacja,
nie optymalizacja** — i on już działa (003b).

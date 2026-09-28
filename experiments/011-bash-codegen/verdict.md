# 011 — WERDYKT: **DISPOSE dekompozycji dla codegen** — best-of-N wygrywa, reduce-przez-Jimmy'ego psuje

448 requestów, 0 błędów. Harness zwalidowany na 6 skryptach referencyjnych (wszystkie pass) PRZED biegiem.

## Wyniki (pass-rate %, M=5 powtórzeń/zadanie)
| ramię | sequence | pipeline | overall | avg_req/zadanie |
|-------|----------|----------|---------|-----------------|
| A single-shot | 46.7 | 13.3 | 30.0 | 1 |
| **B best-of-N** (k+2) | **53.3** | **40.0** | **46.7** | 4.5 |
| C1 dekompozycja, PLAN DANY | 20.0 | 13.3 | 16.7 | 3.5 |
| C2 dekompozycja, Jimmy planuje | 33.3 | 0.0 | 16.7 | 5.9 |

Kategorie: głównie exec_fail; extract_fail 1, blocked 1 (Jimmy raz emitował groźny token) — instrument czysty.

## Wnioski
1. **Wygrywa best-of-N + wykonanie jako weryfikator** (46.7%). Czwarty raz w projekcie: masa całych
   prób + tani deterministyczny checker bije wszystko. To jest sposób na kod z Jimmym.
2. **Dekompozycja na nieredukowalne kroki HURTS** (16.7% < nawet single-shot 30%). Hipoteza użytkownika
   — DISPOSE dla bash.
3. **Planowanie NIE jest wąskim gardłem.** C1 (idealny plan ode mnie) = C2 (Jimmy planuje) = 16.7%.
   Winna jest SAMA dekompozycja, nie plan. (Po to rozbito C na C1/C2.)
4. **To nie kwestia budżetu.** C2 dostał WIĘCEJ requestów niż B (5.9 vs 4.5) i przegrał 3×.
5. **Split kształtu potwierdzony:** dekompozycja katastrofalna na pipeline'ach sprzężonych (0-13%),
   tylko zła na rozdzielnych sekwencjach (20-33%). Sprzężenie krokow przez stdin/stdout uniemożliwia
   niezależne pisanie i spójne składanie.

## Rafinacja prawa map-reduce (dlaczego 004 wygrał, a 011 przegrał)
| | 004 (KEEP) | 011 dekompozycja (DISPOSE) |
|---|-----------|----------------------------|
| reduce | **deterministyczny** (unia w Pythonie) | **Jimmy składa kod** |
| kroki map | naprawdę niezależne (rozłączne chunki) | sprzężone (konwencje snippetów) |

**Prawo (rafinowane): map-reduce z Jimmym działa ⟺ REDUCE jest deterministyczny, a jednostki map
naprawdę niezależne.** Gdy reduce wymaga, by głupi model SYNTETYZOWAŁ/sklejał sprzężone części —
zawodzi (reduktor nie pogodzi niespójnych konwencji, błędy się kompoundują). Dekompozycja pomaga
tylko, gdy rekombinacja jest arytmetyczna (unia/suma/zliczenie), nie inteligentna.

## Jak NAPRAWDĘ uczyć Jimmy'ego kodu (rekomendacja z danych)
Nie dekomponuj na kroki do sklejenia przez Jimmy'ego. Zamiast tego: **best-of-N całego skryptu +
wykonanie na testach jako filtr** (arm B). Deterministyczny weryfikator (uruchom + porównaj wyjście)
robi całą robotę selekcji; Jimmy tylko dostarcza różnorodność prób. To skaluje się z jego prędkością.

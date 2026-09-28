# 010 — WERDYKT: **kontr-intuicyjne odkrycie** — dla klasyfikacji holistycznej NIE dekomponuj

125 requestów, 0 błędów. (Uwaga: 4 foldery — mała N na poziomie reduce; kluczowy sygnał to kontrast
map vs holistyczny, który jest duży.)

## Wyniki
| poziom | metoda | wynik |
|--------|--------|-------|
| L0 map — klasyfikacja POJEDYNCZYCH plików (vote-5) | Jimmy per plik | **54.2%** |
| L1 reduce folderowy — DETERMINISTYCZNY (większość predykcji) | z zaszumionego map | **50.0%** |
| L1 reduce folderowy — **JIMMY** (pokaż nazwy całego folderu) | holistycznie | **100.0%** |
| L2 reduce drzewa — JIMMY (na podsumowaniach folderów) | holistycznie | **recall 1.0** |

**Jimmy-reduce (100%) > deterministyczny-reduce (50%) o +50 pkt** — ODWROTNIE niż przewidywało prawo
z 011.

## Dlaczego odwrotnie (i co to znaczy)
- Deterministyczny reduce operuje na **zaszumionych** predykcjach map (54%) → garbage-in-garbage-out,
  nie przebije jakości wejścia.
- Jimmy folder-reduce dostał **surowe nazwy całego folderu naraz** (`main.py, app.js, build.sh,
  util.py, server.go, README.md`) i osądził **holistycznie** → trywialne "code", mimo że mylił się na
  pojedynczych plikach w izolacji.
- **Agregat jest ŁATWIEJSZY niż suma części.** Etap map WYRZUCA kontekst i wstrzykuje szum. Dla
  zadania gestalt-owego dekompozycja na per-item map + reduce jest DOMINOWANA przez pokazanie
  Jimmy'emu całości.

## Zunifikowana taksonomia dekompozycji (004 + 010 + 011)
| Typ zadania | reduce | wygrywa | dowód |
|-------------|--------|---------|-------|
| **Ekstrakcja z rozłącznych fragmentów** (fakty lokalne) | deterministyczny (unia) | **map-reduce** | 004: 0→100% |
| **Klasyfikacja/gestalt** (temat, sens całości) | — | **pokaż Jimmy'emu CAŁOŚĆ** (bez map) | 010: 54% part → 100% whole |
| **Synteza sprzężonych części** (kod) | — | **best-of-N całości + weryfikator** | 011: dekompozycja 17% < best-of-N 47% |

**Prawo (finalne) o dekompozycji:** rozbijaj na kroki TYLKO gdy jednostki są naprawdę niezależne
I rekombinacja jest deterministyczna (arytmetyczna). Gdy zadanie korzysta z kontekstu całości
(klasyfikacja) → pokaż całość. Gdy wymaga inteligentnej syntezy (kod) → best-of-N całości + checker.
Intuicja "rozbij na jak najwięcej najprostszych kroków" jest dla Jimmy'ego **zwykle błędna** — wygrywa
tylko w wąskim przypadku ekstrakcji z niezależnych fragmentów z arytmetycznym reduce.

## Bonus (capability): Jimmy lepszy na agregacie niż na części
54% per plik → 100% per folder. Głupi model zyskuje na kontekście: klasyfikacja zbioru jest
łatwiejsza niż pojedynczego elementu. Praktyczne: klasyfikuj grupy, nie pojedyncze byty, gdy się da.

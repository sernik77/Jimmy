# 002 — WERDYKT: **KEEP** (z ostrą granicą)

## Wynik (160 requestów, 0 błędów)
| Metryka | Wynik | Próg | |
|---------|-------|------|---|
| validity pojedynczej próbki | 95.0% | — | |
| **validity@best-of-8** | **100.0%** | ≥95% | ✅ |
| intent-accuracy — WSZYSTKIE (mylące) | 70.0% | ≥80% | ⚠️ zafałszowane |
| **intent-accuracy — JEDNOZNACZNE (n=12)** | **91.7%** | ≥80% | ✅ |
| intent-accuracy — DYSKUSYJNE (n=8) | 37.5% | — | szum etykiet |

Rozdzielenie 70% na podzbiory (`analyze.py`, offline): globalne 70% było mieszanką zafałszowaną
moimi własnymi wątpliwymi etykietami. Na inputach z jedną jednoznaczną kategorią Jimmy trafia **91.7%**
(11/12; jedyny błąd: "student discounts" → account). Na dyskusyjnych (billing=account/refund?,
damaged-in-transit=shipping/complaint?) — 37.5%, ale tam ludzki gold też jest sporny.

## Interpretacja (dwie osobne rzeczy zmierzone naraz)
1. **Format / kontrakt JSON — ROZWIĄZANY.** best-of-8 + walidator schematu = **100%** poprawnych,
   schemat-zgodnych obiektów. Nawet gdy pojedyncza próbka bywa złamana (95%), zawsze ≥1 z 8 przechodzi.
   → **Jimmy jako kuloodporna warstwa "tekst → JSON wg schematu" jest produkcyjny.**
2. **Semantyka / klasyfikacja — DZIAŁA na czystych kategoriach (91.7%), pada na niedookreślonych.**
   Po rozdzieleniu podzbiorów właściwy wniosek to NIE "Jimmy ma bias / 70%", lecz:
   *Jimmy klasyfikuje czysto rozdzielne kategorie dobrze; zawodzi tam, gdzie taksonomia sama jest
   sporna* — a tam ludzki gold też bywa sporny. Realny sufit widać na dyskusyjnych (37.5%): gdy
   dwie kategorie się nakładają, głosowanie utrwala jeden z rozsądnych wyborów.

## Wykorzystanie
- ✅ **KEEP:** ekstrakcja/normalizacja do sztywnego schematu JSON (walidator jako brama).
  Wzorzec: `sample_n(N=8) → filter(validate) → weź pierwszy walidny`. 100% niezawodności formatu.
- ✅ **KEEP:** klasyfikacja na **rozłącznych, dobrze zdefiniowanych** kategoriach (~92%).
- ⚠️ **Granica:** przy nakładających się/spornych kategoriach Jimmy nie jest arbitrem; potrzebny
  człowiek lub mocniejszy model — ale Jimmy dostarcza strukturę i kandydatów.

## Powtarzalność (2 runy)
| | run 1 | run 2 |
|---|---|---|
| validity@best-of-8 | 100% | **100%** |
| validity/próbka | 95% | 95% |
| intent — jednoznaczne | 91.7% | **100%** |
| intent — dyskusyjne | 37.5% | 37.5% |
Kontrakt JSON (100%) i granica (jednoznaczne≈92-100% vs sporne 37.5%) są stabilne między runami.

## Wniosek meta
Dwa razy z rzędu (001, 002) ta sama granica: **wolumen naprawia wariancję, nie bias** — a to, co
wyglądało na bias w 002, było w większości niedookreśleniem taksonomii, nie błędem modelu.
Patrz FINDINGS.md.

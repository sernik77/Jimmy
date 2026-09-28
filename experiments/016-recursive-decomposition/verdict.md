# 016 — WERDYKT: **technika defensywna WYGRYWA, głęboka rekursja NIE** (PARTIAL KEEP)

~200 requestów, 0 błędów. Zadanie: instalacja+weryfikacja PostgreSQL na świeżym Linuksie.
Rekursja orkiestrowana deterministycznie (Python: drzewo/terminacja/dedup; Jimmy: 1 krok/węzeł).

## Wyniki
| arm | liście | defensive-ratio | avg słów | terminacja |
|-----|--------|-----------------|----------|------------|
| RECURSIVE_DEFENSIVE (depth≤4) | 299 (240 efekt.) | **0.90** | 8.5 | ❌ trafił node-cap |
| RECURSIVE_PLAIN (depth≤4) | 273 | 0.54 | 9.5 | ❌ cap |
| SINGLESHOT_DEFENSIVE | 18 | 0.39 | 10.8 | — |
| BOUNDED depth-2 DEFENSIVE | 49 | 0.78 | 13.1 | ❌ cap (mniejszy) |

## 1. Technika defensywna: **KEEP (mocno)** — to jest sedno Twojego pomysłu
System-prompt „nie zakładaj nic; weryfikuj preconditiony, identyfikuj środowisko/narzędzia, potwierdzaj
sukces" podnosi defensive-ratio z **0.54 → 0.90** (+35 pkt). Liście są dokładnie kuloodporne:
`Check available package managers` · `Verify presence of package manager` · `Check if postgresql already
installed` · `Confirm postgresql runs`. Jimmy PATRAFI generować obronne, weryfikujące kroki gdy mu się to
jawno zada. Działa przy każdej głębokości (0.78-0.90). **To realna, powtarzalna sztuczka.**

## 2. Rekursja do „nieredukowalnej warstwy": **DISPOSE**
- **Jimmy nie osądza atomowości** — prawie nigdy nie mówi ATOMIC, dekomponowałby w nieskończoność.
  „Fundamentalna warstwa" nie jest wykrywana przez model; zatrzymuje go WYŁĄCZNIE deterministyczny cap.
- **Eksplozja:** 299 „fundamentalnych kroków" na instalację jednej bazy — przerost, nie minimalny zbiór.
- **Redundancja międzygałęziowa ~20%** (koncept „check package manager version" ×5, „verify environment
  type" ×4) — mode-collapse z Prawa 2 objawia się jako re-odkrywanie tych samych checków w różnych gałęziach.
- **Płytko mimo wszystko:** BFS wyczerpał budżet węzłów na depth 3 (szerokie rozgałęzienie), nie sięgnął
  głęboko — „coraz głębsze warstwy" to iluzja; dostajemy szeroki, płytki, redundantny wachlarz.

## 3. Sweet-spot: płytko + defensywnie
BOUNDED depth-2 defensive (49 kroków, 0.78) daje UŻYTECZNY plan pokrywający realny workflow (verify OS →
identify pkg manager → check installed → install → configure → create db/user → confirm) — bez przerostu
299. Single-shot (18, 0.39) jest zwięzły ale mniej obronny. Kompromis: **płytka ograniczona dekompozycja
+ defensywny prompt.**

## Przepis (rekomendacja z danych)
`deterministyczny orchestrator (depth-cap 1-2, node-cap, dedup SEMANTYCZNY między gałęziami) → Jimmy
dekomponuje 1 krok/węzeł z DEFENSYWNYM system-promptem → deterministyczna konsolidacja`. Nie licz na to,
że Jimmy sam wykryje „warstwę atomową" (nie wykryje) ani że głębsza rekursja da lepszy plan (da redundantny
przerost). Spójne z Prawem 7 (Jimmy=proposer, kontrola deterministyczna) i Prawem 4 (bounded reduce/dedup).

**Podsumowanie:** Twoja intuicja o defensywnych, weryfikujących krokach jest TRAFNA i mierzalnie działa
(+35 pkt); ograniczeniem jest sama rekursja — Jimmy nie zna dna, więc dno musi wyznaczyć orchestrator.

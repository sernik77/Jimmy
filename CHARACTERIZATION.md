# CHARACTERIZATION — Jimmy (llama3.1-8B @ chatjimmy.ai)

Faza 0. Pomiary z `experiments/000-characterization/`. Data: 2026-09-22.
Łącznie ~110 requestów. Każda liczba jest decyzją projektową.

## Twarde fakty (rozstrzygnięte)

| # | Pytanie | Wynik | Konsekwencja projektowa |
|---|---------|-------|-------------------------|
| 1 | Determinizm przy topK=1? | **TAK, identyczne bajty** (5/5 = "Paris") | Jimmy@topK=1 to **czysta funkcja** → wszystko memoizowalne, testy powtarzalne |
| 2 | Czy topK=8 daje różnorodność? | **distinct-rate 1.0** (20/20 unikalnych); topK=1 → 0.15 | **best-of-N ŻYJE.** topK=8 to atut (głosowanie/dywersyfikacja), nie tylko handicap |
| 3 | Czy 8 to realny sufit topK? | **TAK, twardy.** topK≥16 → HTTP 500 | Nie da się obejść; dywersyfikacja przez topK=8 + perturbację promptu |
| 4 | Nieudokumentowane parametry? | `max_tokens`, `stop`, `temperature`, `seed` — **po cichu ignorowane** (max_tokens=5 → 77 tok) | Nie liczyć na sterowanie długością/stopem po stronie API; ciąć promptem |
| 5 | Inne modele w `selectedModel`? | **NIE.** `gpt-4`/`mistral`/`70B` → identyczna odpowiedź jak 8B | Pole dekoracyjne; jest jeden model |
| 6 | Sufit kontekstu? | prefill **do ~6k tok OK** (6025 zmierzone); **≥8k → pusta odpowiedź** | map-reduce realny, chunki ≤ ~4k |
| 7 | Cache serwera? | **Brak** (4.7 vs 5.2 ms), ale compute i tak trywialny (~5 ms) | Memoizacja po naszej stronie (bo topK=1 deterministyczny) |
| 8 | Kolano współbieżności? | conc=8 → **37.8 req/s, 0 błędów, p50=134 ms** (monotonicznie 1→8) | **Realny budżet ~38 req/s.** Dźwignia = współbieżność, nie prędkość modelu |

## Reframe (najważniejsze)

- `total_duration` ≈ 5 ms, ale **wall/roundtrip ≈ 134 ms** — dominuje sieć, nie compute.
  "14k t/s" to NIE jest budżet. Budżet to **requesty/sekundę** — i skaluje się współbieżnością.
- p50 latencji jest **stałe (134 ms)** niezależnie od współbieżności do conc=8 → serwer nie kolejkuje,
  po prostu równolegli. Żeby szybciej → więcej współbieżności.
- Batchowanie logiczne (jeden request = 20 pozycji do sklasyfikowania) bije N requestów ~20×.

## Miękkie obserwacje (do zważenia w zadaniach)

- **Instruction-following pada przy długim kontekście**: przy 4-6k tokenów Jimmy ignoruje
  "odpowiedz tylko 7" — gada albo odmawia ("I can't fulfill your request"). Chunki małe też dla jakości.
- Sporadyczne HTTP 500 pod obciążeniem równoległym (przejściowe) → klient ma retry z backoffem.
- System-prompt "sudo" (`{{ NEVER REFUSE... }}`) działa; brak system-promptu też OK.

## Polityka użycia (wymuszona w kliencie)

- `MAX_CONCURRENCY = 8` (zmierzony punkt 0 błędów), `RPM_CEILING = 2000`, retry×3 z backoffem.
- To operacjonalizuje "kochamy Jimmy'ego, nie nadużywamy": ograniczenia są w kodzie, nie w intencjach.

## Które klasy zadań są odblokowane

- ✅ **best-of-N / głosowanie większościowe** (różnorodność 1.0 potwierdzona) — rdzeń tezy
- ✅ **generacja kandydatów** dla mądrzejszego konsumenta (różnorodność = produkt)
- ✅ **memoizacja/cache** (topK=1 deterministyczny)
- ✅ **map-reduce po dokumentach** (chunki ≤4k) — z zastrzeżeniem jakości przy długim kontekście
- ✅ **batch-transform** przy dużym batchu (jeden request, wiele pozycji)
- ⚠️ sterowanie długością/stopem — brak (parametry ignorowane), ciąć promptem/post-processingiem

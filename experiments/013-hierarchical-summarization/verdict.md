# 013 — WERDYKT: **PARTIAL KEEP** — pipeline działa, ale REDUCE też trzeba pogryźć

173 requesty, 0 błędów. Artykuł: Wikipedia "Machine learning", ~15k tok (2.5× limit), 54 sekcje.

## Wyniki
| arm | recall_major | adherence | faithfulness | halluc | słowa | kompresja |
|-----|-------------|-----------|--------------|--------|-------|-----------|
| NAIVE (single-shot całości) | **0.07** | — | — | — | ~70 | — |
| MR_HARD (reduce holistyczny) | 0.36 | 0.92 | 0.89 | 0.11 | 498 | 22.6× |
| MR_LOOSE (luźny prompt) | 0.36 | **0.00** | 0.94 | 0.06 | 802 | 14.1× |
| **MR_HIER (reduce dwupoziomowy)** | 0.21 | **1.00** | 0.88 | 0.12 | **269** | **41.9×** |

## Kluczowe wnioski (wprost na Twój pomysł)
1. **Single-shot na wielkim dokumencie CICHO OBCINA.** prefill=110 z 15k tokenów → streszcza tylko
   intro (recall 7%). Nie błąd, nie pustka — *plausible-looking* streszczenie pokrywające ~nic.
   **Groźny failure mode.** Map-reduce jest KONIECZNY, nie opcjonalny.
2. **Map (streszczanie po sekcji z twardym system-promptem) jest NIEZAWODNY** — faith 0.88-0.94,
   ~10% "halucynacji" to głównie parafraza. Chunkowanie „od-do" + twarde reguły = solidne notatki.
3. **REDUCE to wąskie gardło — i też trzeba go pogryźć.** Holistyczny reduce nad 54 sekcjami jest
   niestabilny (498-962 słów między runami, łamie „max 10 bulletów" — instruction-following pada na
   dużym wejściu, jak Faza 0). **Dwupoziomowy reduce (partie po 8 → mini → finał) NAPRAWIA to:**
   adherence **1.00**, 269 słów, kompresja **42×** — realne zwięzłe streszczenie. To rozszerza lekcję
   „gryzienia na kawałki" na sam reduce.
4. **TWARDE ograniczenia w system-prompcie biją luźne DECYDUJĄCO na formacie** (adherence 0.92-1.0
   vs 0.00 — bullety vs proza). Twój nacisk na precyzyjny system-prompt: **potwierdzony** (dla formatu).
5. **Tradeoff kompresja↔pokrycie.** Ciaśniejsze streszczenie (MR_HIER) pokrywa mniej tematów. Sufit
   pokrycia ~1/3-1/2 głównych tematów dla zwięzłego streszczenia.

## Uwaga o metryce (uczciwość)
recall_major = substring-match 14 tytułów sekcji → **zaniża** pokrycie konceptualne. Artefakt MR_HIER
(w results.json) pokrywa rdzeń ML: definicja, paradygmaty (supervised/unsupervised/RL), teoria PAC,
overfitting, halucynacje, adversarial — pomija peryferia (Applications, Ethics, Hardware, Journals).
To rozsądny priorytet streszczenia (rdzeń > peryferia), nie czysta porażka.

## Werdykt: PARTIAL KEEP
✅ Architektura DZIAŁA: map niezawodny+ugruntowany; hierarchiczny reduce daje zwięzłe, sformatowane,
   wierne streszczenie dokumentu, którego single-shot CICHO psuje. Twarde ograniczenia rządzą formatem.
⚠️ Granica: pokrycie tematów ograniczone przy silnej kompresji (tradeoff), map faith ~0.9 (nie 1.0).
❌ Nie stawiaj na holistyczny reduce nad wieloma sekcjami (łamie ograniczenia ilościowe) ani na
   single-shot (ciche obcięcie).

## Przepis (rekomendacja z danych)
`chunk sekcyjny → map(twardy system-prompt, ugruntuj) → reduce HIERARCHICZNY (partie → mini → finał
z twardym limitem)`. Każdy poziom karmiony MAŁYM wejściem → instruction-following trzyma. Łączy prawo
czwarte (dekomponuj z bounded reduce) i piąte (twarde, celne instrukcje).

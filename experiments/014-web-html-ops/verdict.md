# 014 — WERDYKT: **granica zdolności** — mechanika→regex, semantyka→Jimmy

31 requestów, 0 błędów. Strona: Hacker News front page (~8.5k tok, 3 chunki). M=3.

## Wyniki
### MECHANICZNE (istnieje deterministyczny baseline) — Jimmy PRZEGRYWA
| operacja | Jimmy P/R/F | deterministyczny | werdykt |
|----------|-------------|------------------|---------|
| ekstrakcja linków http(s) | 0.80 / 0.54 / **0.64** | regex = 1.0/1.0/1.0 | ❌ Jimmy gubi 46%, halucynuje 20% |
| strip HTML → tekst | content-F1 **0.68**, tag-leak 0 | parser = perfekcyjny | ❌ Jimmy traci 1/3 treści |
| fragmenty ze słowem kluczowym | 0.63 / 0.83 / **0.69** | grep = 1.0/1.0/1.0 | ❌ Jimmy gorszy |

Deterministyczne narzędzia są **perfekcyjne, natychmiastowe, darmowe**. Jimmy jest ściśle gorszy
I kosztuje requesty. **DISPOSE Jimmy dla mechanicznie-specyfikowalnej ekstrakcji HTML.**

### SEMANTYCZNE (brak deterministycznego odpowiednika) — Jimmy DODAJE WARTOŚĆ
| operacja | Jimmy P/R/F | werdykt |
|----------|-------------|---------|
| filtr po TEMACIE (space vs food) | 1.0 / 0.89 / **0.94** | ✅ czego regex NIE potrafi |
| "czym jest ta strona" (opis) | poprawnie zidentyfikował HN (news/tech/stories/score) | ✅ semantyczne |

`topic_filter`: Jimmy bezbłędnie oddzielił tytuły o kosmosie od kulinarnych (P=1.0), pominął 1/6.
Żaden regex nie odróżni tematu bez zahardkodowanych słów. Tu Jimmy **zarabia na siebie**.

## Wniosek (granica zdolności — kiedy używać Jimmy'ego do HTML)
- **Mechanika** (linki, strip, keyword-grep, parsowanie struktury) → **deterministyczny kod**
  (regex/BeautifulSoup/grep). Jimmy jest gorszy, wolniejszy, zbędny.
- **Semantyka** (relewancja tematyczna, klasyfikacja treści, opis, „o czym to jest") → **Jimmy**,
  bo brak taniego deterministycznego odpowiednika.

**Wzorzec pipeline'u web:** parser robi mechanikę (wyciągnij linki/tekst/strukturę deterministycznie),
Jimmy dostaje TYLKO podzadania semantyczne na już-oczyszczonym tekście (filtr tematyczny, opis,
tagowanie). Nie każ Jimmy'emu robić tego, co regex robi lepiej.

## Uczciwa uwaga
`topic_filter` testowano na czystym skonstruowanym snippecie (gold znany) — realny zaszumiony HTML
byłby trudniejszy. Ale kontrast jest jednoznaczny: mechanika 0.64-0.69 (dominowana) vs semantyka
0.94 (unikalna wartość). Chunkowany map po surowym HTML działa, lecz ma sens tylko gdy operacja
per-chunk jest SEMANTYCZNA.

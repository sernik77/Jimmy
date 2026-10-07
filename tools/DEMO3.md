# Demonstracja v3: TOP 10 zastosowań sumaryzacji Jimmym
*2026-10-08 · ranking „według mnie”, każda pozycja ZADEMONSTROWANA na żywo (`tools/summarize.py`, llama3.1-8B)*

## Kryterium rankingu
Kolejność wg dopasowania do profilu Jimmy'ego — **głupi, ale prawie darmowy per próbka**. Dobre zastosowanie spełnia trzy warunki:

1. **Wolumen/równoległość coś daje** (dużo jednostek, ~38 req/s @ conc 8).
2. **Weryfikacja tańsza niż generacja** (tani checker/wzrok potwierdza wynik).
3. **Toleruje głupotę per-sample** (błąd jednej próbki nie psuje całości).

> 🔑 **Najważniejsza obserwacja z v1–v3:** jakość streszczenia jest **doskonała na wejściach mieszczących się w kontekście** (<~1,2k tok, tryb single-shot — patrz wyniki niżej), a psuje się dopiero w reżimie **długiego map-reduce** (gubienie instrukcji, niezbieżność reduce). Wniosek projektowy: tnij na kawałki, które indywidualnie są w sweet-spocie, i agreguj tanio.

## Ranking
| # | Zastosowanie | Dlaczego Jimmy | Oparcie |
|---|--------------|----------------|---------|
| 1 | Synteza wielu recenzji / opinii → werdykt | Najczystsze dopasowanie: wolumen JEST sensem (N recenzji równolegle), weryfikacja trywialna (czy werdykt zgadza się z większością?), a głupota pojedynczej próbki uśrednia się. | Prawo 1: *wolumen naprawia wariancję*; majority/agregacja jako tani weryfikator (`jimmy/eval |
| 2 | Długi dokument → TL;DR (map-reduce) | Flagowe KEEP: mapą bijesz sufit kontekstu ~6k tok, redukcją domykasz. | exp 004 (recall 0→100) |
| 3 | Wiele dokumentów → jeden brief | Każdy dokument to niezależny map (idealnie równoległy, 38 req/s), tani finalny reduce. | Prawo 2 (map-reduce) + budżet ~38 req/s @ conc 8 |
| 4 | Log / alert / stacktrace → diagnoza | Operacyjne: logów są tony (wolumen), a weryfikacja jest banalna — albo nazwał błąd i komponent, albo nie. | Granica z exp 014: mechanika→regex, semantyka→Jimmy |
| 5 | Transkrypcja spotkania → decyzje + action items | Ekstrakcja strukturalna z weryfikacją wobec źródła (czy właściciel/termin są w tekście?). | Ekstrakcja faktów z checkerem; `is_usable` łapie ciche porażki |
| 6 | Wątek e-mail → co ustalono + co dalej | Jak spotkanie: dużo wątków, każdy krótki (sweet-spot single-shot), wynik łatwo sprawdzić wzrokiem. | Sweet-spot <~1,2k tok, gdzie instruction-following jest mocny |
| 7 | Gęsty dokument (ToS / umowa) → kluczowe punkty | Kompresja gęstego tekstu do punktów kontrolnych; każdy punkt weryfikowalny wobec oryginału. | Kompresja↔pokrycie (v1): zwięzłość gubi peryferie; do pełni użyj `--map-only` |
| 8 | Tabela / dane → proza narracyjna | Odwrotność klasyki: struktura→NL. | Transform semantyczny na krótkim wejściu — stabilny |
| 9 | Diff / kod → nota do changeloga | OPISYWANIE zmian (nie generowanie kodu!) jest bezpieczne i trafne. | exp 011 ostrzega: GENEROWANIE kodu ryzykowne; opis/streszczenie — bezpieczne (exp 020 hybryda) |
| 10 | Tekst z żargonem → plain language (ELI5) | Użyteczne, ale najmniejsza dźwignia weryfikacji: parafraza może subtelnie przekłamać, a to trudno wykryć automatem. | Ryzyko wierności bez taniego checkera — stąd niżej w rankingu |

---

## #1 — Synteza wielu recenzji / opinii → werdykt
**Dlaczego pasuje do Jimmy'ego:** Najczystsze dopasowanie: wolumen JEST sensem (N recenzji równolegle), weryfikacja trywialna (czy werdykt zgadza się z większością?), a głupota pojedynczej próbki uśrednia się. To teza projektu wcielona.  
**Oparcie w findings:** Prawo 1: *wolumen naprawia wariancję*; majority/agregacja jako tani weryfikator (`jimmy/eval.py`).  
**Komenda:**
```bash
summarize reviews.txt --style prose --focus 'overall verdict: most praised vs most criticised'
```
**Wynik na żywo (wejście reprezentatywne):**
```
The phone's battery life is a major highlight, with most reviewers praising its ability to last all day. However, it overheats under heavy use, including gaming. The camera is a mixed bag, with some reviewers finding it mediocre in low-light conditions and others experiencing noise in night photos. The screen is generally well-regarded, with many calling it "gorgeous." Overall, the phone offers great value at its price, but has some notable drawbacks.
```

## #2 — Długi dokument → TL;DR (map-reduce)
**Dlaczego pasuje do Jimmy'ego:** Flagowe KEEP: mapą bijesz sufit kontekstu ~6k tok, redukcją domykasz. Działa tam, gdzie pojedynczy prompt nie wejdzie.  
**Oparcie w findings:** exp 004 (recall 0→100). Uwaga: trzymaj reżim „mało dużych chunków + jeden reduce” (patrz v1).  
**Komenda:**
```bash
summarize book.txt --chunk-words 2400 --style tldr --max-words 80
```
**Wynik na żywo (wejście reprezentatywne):**
```
Machine learning is a field of study that combines statistics and mathematical optimization methods to enable computers to learn from data and make predictions or classifications. It has its roots in the 1950s and 1960s, with early researchers such as Donald Hebb and Walter Pitts and Warren McCulloch contributing to the development of neural networks. The field has since grown and evolved, with advances in deep learning and the introduction of new algorithms and techniques.
```

## #3 — Wiele dokumentów → jeden brief
**Dlaczego pasuje do Jimmy'ego:** Każdy dokument to niezależny map (idealnie równoległy, 38 req/s), tani finalny reduce. Skaluje się liniowo z liczbą źródeł.  
**Oparcie w findings:** Prawo 2 (map-reduce) + budżet ~38 req/s @ conc 8.  
**Komenda:**
```bash
summarize a.txt b.txt c.txt --style bullets --focus 'combined executive brief'
```
**Wynik na żywo (wejście reprezentatywne):**
```
• Quarterly sales rose 12% to $4.2M, driven by APAC region and new subscription tier.
• Churn fell to 3.1%.
• Support ticket volume dropped 20% after self-service portal launch, with avg resolution time now 4.2 hours.
• Top complaint shifted from billing to onboarding confusion.
• Marketing spend reallocated from paid search to content and community, with organic traffic growing 34% QoQ.
• Webinar series generated 1,100 qualified leads at half the previous cost-per-lead.
```

## #4 — Log / alert / stacktrace → diagnoza
**Dlaczego pasuje do Jimmy'ego:** Operacyjne: logów są tony (wolumen), a weryfikacja jest banalna — albo nazwał błąd i komponent, albo nie. Dumb-but-cheap triage.  
**Oparcie w findings:** Granica z exp 014: mechanika→regex, semantyka→Jimmy. Tu Jimmy robi semantykę („co się zepsuło”).  
**Komenda:**
```bash
cat error.log | summarize --style tldr --max-words 40 --focus 'root cause and failing component'
```
**Wynik na żywo (wejście reprezentatywne):**
```
A slow query on the "events" table caused a batch flush to fail due to a UniqueViolation error, where a duplicate key value violates the "events_pkey" constraint, causing worker 3 to exit.
```

## #5 — Transkrypcja spotkania → decyzje + action items
**Dlaczego pasuje do Jimmy'ego:** Ekstrakcja strukturalna z weryfikacją wobec źródła (czy właściciel/termin są w tekście?). Wysoka wartość, niska cena.  
**Oparcie w findings:** Ekstrakcja faktów z checkerem; `is_usable` łapie ciche porażki.  
**Komenda:**
```bash
summarize transcript.txt --style bullets --focus 'decisions and action items with owners'
```
**Wynik na żywo (wejście reprezentatywne):**
```
* Decision: Launch on the 22nd.
* Bartek: Payment testing by the 18th, will send build to QA on Friday.
* Celina: Update press release and brief sales team by the 22nd.
* Anna: Owns overall launch decision.
* Bartek: Owns payment testing.
* Celina: Owns external comms.
```

## #6 — Wątek e-mail → co ustalono + co dalej
**Dlaczego pasuje do Jimmy'ego:** Jak spotkanie: dużo wątków, każdy krótki (sweet-spot single-shot), wynik łatwo sprawdzić wzrokiem.  
**Oparcie w findings:** Sweet-spot <~1,2k tok, gdzie instruction-following jest mocny.  
**Komenda:**
```bash
summarize thread.txt --style bullets --focus 'what was decided and what each person must do next'
```
**Wynik na żywo (wejście reprezentatywne):**
```
• Dave: Moved the vendor demo to Thursday.
• Priya: Available on Thursday at 2pm for the demo.
• Dave: Needs the updated requirements doc by Wednesday noon from Priya.
• Priya: Will finalize and send the requirements doc by Wednesday noon.
• Sam: Wants the SSO requirement included in the updated doc.
• Dave: Confirmed the demo time and date with the vendor.
```

## #7 — Gęsty dokument (ToS / umowa) → kluczowe punkty
**Dlaczego pasuje do Jimmy'ego:** Kompresja gęstego tekstu do punktów kontrolnych; każdy punkt weryfikowalny wobec oryginału. Nie porada prawna — triage.  
**Oparcie w findings:** Kompresja↔pokrycie (v1): zwięzłość gubi peryferie; do pełni użyj `--map-only`.  
**Komenda:**
```bash
summarize tos.txt --style bullets --focus 'obligations, costs, termination, data sharing'
```
**Wynik na żywo (wejście reprezentatywne):**
```
• You grant us a worldwide, royalty-free licence to host and display content you upload.
• Subscriptions renew automatically; cancel at least 48 hours before renewal to avoid charges.
• We may terminate accounts for breach without notice.
• We share data with third-party processors for analytics and payment.
• You are liable for all activity under your account.
• We may change these terms with 30 days notice.
```

## #8 — Tabela / dane → proza narracyjna
**Dlaczego pasuje do Jimmy'ego:** Odwrotność klasyki: struktura→NL. Tanie „wyjaśnij dane” do raportu; liczby łatwo zweryfikować.  
**Oparcie w findings:** Transform semantyczny na krótkim wejściu — stabilny.  
**Komenda:**
```bash
summarize table.txt --style prose --focus 'the story the numbers tell'
```
**Wynik na żywo (wejście reprezentatywne):**
```
The company's revenue from the APAC region increased by 31% to $1.8M, while the EMEA region saw a 4% growth to $1.2M. The NA region experienced a 6% decline to $1.1M, and LATAM reported a 12% increase to $0.3M, with margins ranging from 14% to 25% across the regions.
```

## #9 — Diff / kod → nota do changeloga
**Dlaczego pasuje do Jimmy'ego:** OPISYWANIE zmian (nie generowanie kodu!) jest bezpieczne i trafne. Weryfikacja: czy nota zgadza się z diffem.  
**Oparcie w findings:** exp 011 ostrzega: GENEROWANIE kodu ryzykowne; opis/streszczenie — bezpieczne (exp 020 hybryda).  
**Komenda:**
```bash
git diff | summarize --style prose --focus 'changelog entry: what changed and why'
```
**Wynik na żywo (wejście reprezentatywne):**
```
The `login` function now checks if a user has failed to log in 5 times, raising a `LockedOut` exception if so, and logs the successful login attempt. The token's time to live (TTL) is set to 1 hour.
```

## #10 — Tekst z żargonem → plain language (ELI5)
**Dlaczego pasuje do Jimmy'ego:** Użyteczne, ale najmniejsza dźwignia weryfikacji: parafraza może subtelnie przekłamać, a to trudno wykryć automatem. Dlatego #10.  
**Oparcie w findings:** Ryzyko wierności bez taniego checkera — stąd niżej w rankingu.  
**Komenda:**
```bash
summarize paper.txt --style prose --focus 'explain in plain language, no jargon'
```
**Wynik na żywo (wejście reprezentatywne):**
```
The transformer uses a multi-head attention mechanism that considers all token positions, with sinusoidal encodings added to the token embeddings. It has residual connections and layer normalization to help gradients flow smoothly through the model, and a feed-forward network applies a non-linearity. The model is trained using a teacher forcing method with the Adam optimizer, and its learning rate is adjusted over time.
```

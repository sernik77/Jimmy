# 006 — WERDYKT: **DISPOSE (z diagnozą)** — cel nasycalny, instrument bez zakresu

1024 requesty, 0 błędów. Wszystkie progi pre-rejestrowane sprawdzone.

## Wyniki vs progi
| Próg | Wynik | |
|------|-------|---|
| 1. Emergencja: A_best ≥ D+2 i ≥1.25D | A=12, **D(kontrola)=12** → False | ❌ |
| 2. Selekcja ma znaczenie: A>B | 12 > 11 → True | ✅ (słabo) |
| 3. Anti-collapse: C kolapsuje, A trzyma | C_distinct_end=1.0 (NIE skolapsował) | ❌ nietestowalne |

## Diagnoza (dlaczego DISPOSE nie jest tu porażką ewolucji)
**Cel był nasycalny w punkcie startowym.** Max fitness=12; Jimmy ma silny priors na aliterację 'p'
i produkuje zdania 12/12 **w pojedynczym strzale** — kontrola D znalazła 12 od razu
("Passionate pandas passionately played peaceful piano pieces perfectly pleasing puzzled people
peacefully."). Skoro próbkowanie maksuje cel w pierwszej partii, **ewolucja nie ma headroomu** by
cokolwiek pokazać. A=D=12 nie znaczy "ewolucja=próbkowanie" jako prawo — znaczy "ten cel nie
rozróżnia metod".

**Gaming potwierdzony (predykcja advisora):** championi to gramatyczny word-salad —
`"Playful pandas passionately purchased pleasingly patterned plush pastel pink perfectly
proportioned pillows."` (12/12). Fitness wysoki, sens znikomy. Dlatego artefakt jest w werdykcie.

**Anti-collapse nietestowalny:** distinct_rate=1.0 we wszystkich ramionach (nawet C — czyste
iterowane przepisywanie — nie skolapsował w 15 gen). Rewrite'y Jimmy'ego są zbyt różnorodne na tym
zadaniu, by fixed-point pojawił się szybko. Brak kontrastu = nie ma czego mierzyć.

**Uboczny fakt:** offspring validity ~6-38%/gen (jak przewidziano z 003A) — populacja żyje z
nielicznych walidnych, reszta ginie z fitness=0. Mechanika działa; zadanie nie dyskryminuje.

## Wniosek i następny krok
Aby UCZCIWIE przetestować "ewolucja > próbkowanie o równym budżecie", potrzebny cel **nienasycalny
single-shotem** — taki, gdzie seed-fitness jest niski, a poprawa wymaga REKOMBINACJI. 002 pokazał,
że Jimmy pada na KONIUNKCJI ograniczeń. Stąd 006b: fitness = aliteracja 'p' ORAZ obecność 3
narzuconych rzadkich słów spoza tematu w ≤12 słowach. Single-shot rzadko spełni wszystko →
krzyżowanie (połącz aliteracyjnego rodzica z tym, co ma wymagane słowa) ma realną robotę.

**Dyscyplina (za advisorem):** 006b to JEDNA przeprojektowana próba z celem dobranym a priori pod
"nienasycalność", z pre-rejestrowanym progiem, i raportuję wynik NIEZALEŻNIE od tego czy wygra.
To naprawa zdiagnozowanej awarii instrumentu, nie dobieranie celu pod tezę.

# 018 — WERDYKT: opis DZIAŁA, bezpośredni sędzia RUBBER-STAMPUJE, ale „opisz→porównaj" to NAPRAWA (+30 pkt)

216 requestów, 0 błędów. Bank 12 znanych komend read-only z twardym goldem.

## Wyniki
| test | metryka | wynik | werdykt |
|------|---------|-------|---------|
| **T1 describe/explain** | key-concept recall / faithful | 0.68 / **1.00** | ✅ KEEP |
| **T2 match-judge (bezpośredni)** | accuracy / mismatch-recall | 0.54 / **0.08** | ❌ DISPOSE |
| **T3 compare via opis→differ** | accuracy / differs-recall | **0.83** / **1.00** | ✅ KEEP (technika) |
| **T4 re-generate alternatywy** | diverse / valid+real / output-equiv | 1.0 / 1.0 / **0.58** | ✅ forma / ⚠️ intencja |

## T1 — Describe: MOCNE (zadanie wiedzowe)
Faithful 1.00 (zawsze właściwe narzędzie, zero halucynacji), recall 0.68. Opisy trafne:
*"dpkg -l lists all installed packages, grep postgresql..."*, *"df displays disk space used..."*.
Wyjaśnianie popularnych komend to recall wiedzy — forte 8B.

## T2 — Bezpośredni sędzia match: KATASTROFA (bias pozytywny/sykofancki)
Accuracy 0.54 (≈ losowo na zbalansowanym zbiorze). match-recall 1.0, ale **mismatch-recall 0.08** —
Jimmy uznaje za MATCH niemal WSZYSTKO, łącznie z parą "check disk space" ↔ `whoami`. **Rubber-stamp.**
Głosowanie-5 nie pomaga (to BIAS, nie wariancja — Prawo 1). Potwierdza Prawo 7: Jimmy = zły DIREKTNY sędzia.

## T3 — „Opisz → porównaj opisy": NAPRAWA (highlight eksperymentu)
Ta SAMA ocena task↔command, ale przepuszczona przez wierny OPIS komendy (z T1): accuracy 0.54→**0.83**,
**mismatch-recall 0.08→1.00**. Wykrył WSZYSTKIE niedopasowania. Mechanizm:
- opisywanie to zadanie wiedzowe, które Jimmy robi wiernie (T1 faithful 1.0),
- porównanie dwóch OPISÓW tekstowych jest łatwe i omija rubber-stamp bias bezpośredniego "match?".

**Technika:** nie pytaj „czy komenda pasuje do zadania?" (rubber-stamp) — pytaj „opisz co robi komenda"
(wiernie), potem „porównaj zadanie z opisem" (wykrywa różnice). +30 pkt z samego przeformułowania.
Niuansuje Prawo 7: Jimmy to zły direktny sędzia, ale DOBRY komparator opisów (i sam produkuje opisy).

## T4 — Re-generate: forma MOCNA, intencja UMIARKOWANA
Zawsze (1.0) produkuje INNĄ, poprawną (valid+real 1.0) alternatywę — różnorodność to siła Jimmy'ego.
Output-equivalence 0.58: `df -h`→`df -k` (≡), `free -m`→`free -h` (≡), ale `lsb_release -a`→`lsb_release -i`
(≠, mniej info), `systemctl status`→`systemctl show` (≠, inny format). ~połowa to prawdziwe
alternatywy tego-samego, reszta „ta sama domena, inny wynik". Forma ✓, równoważność intencji ~połowa.

## Wniosek
Powtarza się oś FORMA vs INTENCJA. Jimmy dobry tam, gdzie to recall wiedzy (opis T1) lub różnorodność
(alternatywy T4); słaby jako direktny sędzia (T2 rubber-stamp). **Najcenniejsze: pośredniczenie osądu
przez wierny opis (T3) obchodzi bias sędziego** — konkretna, przenośna technika dla zadań weryfikacji
dopasowania.

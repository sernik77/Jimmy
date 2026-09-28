# 003 — WERDYKT: **SPLIT** — B: KEEP (selekcja), A: DISPOSE (pokrycie)

280 requestów, 0 błędów.

## Część A — Pokrycie: **DISPOSE** (z ważnym niuansem)
| Zbiór | coverage@N=1 | coverage@N=40 | lift | % przestrzeni | próg 40% |
|-------|--------------|---------------|------|---------------|----------|
| Europa (44) | 1.0 | 7.7 | **7.7×** | 17.5% | ❌ |
| Stany USA (50) | 1.0 | 9.06 | **9.0×** | 18.1% | ❌ |

Próg (≥3× ORAZ ≥40%): lift przechodzi z zapasem, **pokrycie absolutne nie**. Krzywa wyraźnie się
nasyca (Europa: 6.85→7.7 od N=20→40). Dominujące mody: `greece(15), france(10), italy(9)...` /
`oklahoma(16), hawaii(15)...` — próbkowanie jest **zpikowane na kilku ulubieńcach**.

**Wniosek:** różnorodność=1.0 z Fazy 0 (otwarte zdania) NIE przekłada się na pokrycie przy
**recall kategorialnym**. Wolumen kupuje głowę rozkładu (7-9×), ale ogon jest praktycznie
nieosiągalny. **Różnorodność ≠ pokrycie.**

## Część B — Zysk z selekcji: **KEEP**
"Najkrótsze zdanie z {A,B,C}", scorer = liczba słów (min). best-of-20 vs średnia single-shot:
- **średnia redukcja 26.9%** (próg ≥25% ✅), zakres 5-47% po 8 zadaniach.
- walidność zachowana: każde zadanie ≥6 walidnych kandydatów z 20.

**Wniosek:** wzorzec "Jimmy generuje N kandydatów → deterministyczny scorer wybiera max/min po
**skalarnym objektywie**" działa. To trzeci raz, gdy wolumen wygrywa przez OPTYMALIZACJĘ.

## Meta-odkrycie (najważniejsze dla Świętego Graala)
**Próbkowanie Jimmy'ego jest zpikowane na modach.** Wolumen pomaga:
- ✅ OPTYMALIZACJI — wybór najlepszego po skalarze / głosowanie (001, 002, 003B),
ale NIE:
- ❌ EKSPLORACJI — pokryciu/enumeracji przestrzeni kategorialnej (003A).

**Implikacja dla pętli (006):** loop oparty na Jimmym jako eksploratorze **skolapsuje do garstki
modów**. Anti-collapse musi być KONKRETNY: zewnętrzna pamięć "już odwiedzone" + jawna kara za
powtórki (novelty reward) wstrzykiwana do promptu. Sam Jimmy nie zwiększy pokrycia.

## 003b — Łamanie mode-collapse pamięcią zewnętrzną: **KEEP (zdecydowanie)**
Pętla z zewnętrznym stanem "seen" + anti-mode prompt ("wymień element spoza: [...]"), 15 rund × 8.
Kontrola: równy budżet (120 próbek) BEZ feedbacku — izoluje mechanizm.

| Zbiór | anti-mode | kontrola (równy budżet) | lift |
|-------|-----------|-------------------------|------|
| Europa (44) | **77.3%** (34) | 25.0% (11) | **3.1×** |
| Stany USA (50) | **80.0%** (40) | 18.0% (9) | **4.4×** |

Próg (≥60% ORAZ ≥2× kontroli): **spełniony z zapasem.** Krzywa: szybki wzrost → nasycenie
(Europa plateau 34 @ runda 11), bo głęboki ogon (~20%: San Marino, Liechtenstein, Vatican...)
jest ledwo reprezentowany w wagach 8B — twardy sufit nawet z anti-mode.

**To jest pierwszy działający klocek Świętego Graala.** Empiryczny dowód: *zewnętrzny akumulujący
stan + presja nowości* zamienia zpikowany sampler w eksploratora (~80% przestrzeni, 3-4× vs sam
wolumen). Anti-collapse przestaje być teorią — mam działający mechanizm.

# 009 — WERDYKT: **DISPOSE hipotezy przestrzennej, ale ODKRYCIE emergentne**

1800 requestów, 0 błędów, parse-failure 0% (brak confoundu zamrożenia).

## Pre-rejestrowany próg: NIESPEŁNIONY
| | REAL (2. poł) | CTRL | próg |
|---|---------------|------|------|
| Δsim (neighbor − random) | **−0.103** | −0.013 | ≥ +0.10 ❌ |
| activity | 0.998 | — | 0.1–0.9 ❌ (nie zamiera) |
| walidność | 1.00 | — | ≥0.6 ✅ |

Struktura przestrzenna (domeny/klastry) **się NIE wyłoniła** — przeciwnie, sąsiedzi są *mniej*
podobni niż pary losowe. "Jimmy-CA tworzy mapę domen" → **DISPOSE**.

## Ale wyłoniły się TRZY nieoczekiwane zjawiska emergentne
1. **Globalny kolaps do atraktora semantycznego.** Entropia 4.59→3.16; cała siatka 36 komórek
   zbiegła do jednej domeny. Finalny stan (dosłownie):
   ```
   sparkle    blend    shine    blend  shining     meld
     merge  sparkle    merge    shine    merge  glitter
   sparkle   amalga    shine    blend glitter    blend
     merge glitter   amalgam glitter    merge  glitter
   sparkle    merge   sparks    blend glitter    blend
     merge glitter    blend  twinkle     meld  sparkle
   ```
2. **Samoreferencja.** Reguła brzmiała "daj słowo oddające *blend/theme* sąsiadów" — Jimmy zbiegł
   do słów opisujących samo MIESZANIE (`merge, blend, meld, amalgam`) + błysk. **Automat opisał
   własną regułę.** Atraktor to fixpunkt operatora, wyrażony w jego własnym języku.
3. **Lokalna anty-korelacja + niezamierająca aktywność.** Reguła "zblenduj sąsiadów" gwarantuje, że
   komórka RÓŻNI się od tego, co przeczytała → sąsiedzi rozjeżdżają się lokalnie (Δsim<0), a activity
   trzyma ~1.0 mimo niskiej entropii. Faza "ciekła": globalnie skupiona, lokalnie wiecznie tasowana.

## Wpływ topologii: ISTNIEJE (wbrew "worek niezależnych przepisań")
REAL Δsim=−0.103 vs CTRL≈0 — prawdziwe sąsiedztwo produkuje anty-korelację, której losowe nie ma.
Topologia coś robi — tylko przeciwnie do hipotezy (dyfuzja rozpraszająca, nie skupiająca).

## Wniosek
"Blend the neighbors" to operator UŚREDNIANIA → dyfuzja do globalnego konsensusu, nie wzorce
Turinga. Aby dostać strukturę przestrzenną (domeny, glidery) potrzebna reguła z **lokalnym
kontrastem/hamowaniem** (reakcja-dyfuzja: "bądź jak sąsiedzi, ALE nie identyczny; unikaj dominującego
motywu"). To następny wariant. Mimo DISPOSE progu — bogaty, powtarzalny obraz emergentny: Jimmy jako
reguła CA daje **samoreferencyjny kolaps semantyczny w fazie ciekłej**, nie martwotę i nie chaos.

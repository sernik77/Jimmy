# 007 — WERDYKT: **DISPOSE otwartości** — akumulacja nasyca się też w przestrzeni otwartej

320 requestów, 0 błędów.

## Wynik vs próg
| | wartość | próg |
|---|---------|------|
| accept-rate pierwsza 1/3 | 0.219 | — |
| **accept-rate ostatnia 1/3** | **0.062** | ≥0.5 dla "otwarte" ❌ |
| |Σ| unikalnych | ~33 (efektywnie ~22 po odsianiu śmieci) | — |
| różnorodność opisów (oś niezależna) | 0.533, ale top zdominowany | — |

**Acceptance-rate zanika do ~6%** → przestrzeń otwarta, a mimo to akumulacja **saturuje**. DISPOSE
hipotezy "otwarta akumulacja pozostaje otwarta".

## Mechanizm (potrójny — rozbicie odrzuceń rozstrzyga)
**dup-w-oknie = 272 vs dup-poza-oknem = 15** (96% odrzuceń to echo okna):
1. **Instruction-following pada:** Jimmy POWTARZA nazwy pokazane w oknie "unikaj tych", zamiast ich
   unikać. To nie wyczerpanie modów (dup-poza-oknem tylko 15) — to nieposłuszeństwo względem instrukcji.
2. **Kolaps fonotaktyczny/semantyczny:** ukute nazwy klastrują w z/x/k-egzotyce
   (`zhilakian→zhilixi→zhathik→zhilakion`), opisy w `iridescent`(×14)/`bioluminescent`/`crystalline`.
   Nawet szczere próby są leksykalnie bliskie → miękka bramka (Jaccard≥0.5) je odrzuca.
3. **Dziura w miękkiej bramce:** zdegenerowane długie stringi przechodzą jako "nowe" — kilka
   "stworzeń" to wyciekły reasoning Jimmy'ego (`hereisanewcreature`, `zhilakionisoneofthenames...`).
   Miękki checker leksykalny nie odróżnia inwencji od śmieci.

## Próbka artefaktu (dosłownie — advisor: pokaż, nie licz)
Czyste: `gleeblox: iridescent skin membranes` · `xylonix: bioluminescent shell that glows blue` ·
`kaelmoxon: iridescent crystalline carapace` · `kraelor: crystalline exoskeleton, iridescent wings` ·
`borvus: towering iridescent crystalline flying creature`. Śmieci: `hereisanewcreature:` (puste).
Widać gołym okiem: wszystko iridescent+crystalline, nazwy z tego samego kubła fonetycznego.

## Odpowiedź na nazwaną granicę Świętego Graala
**Akumulacja działa dla RECALL po przestrzeni enumerowalnej (003b: kraje, 80%), NIE dla otwartej
INWENCJI.** Struktura modów 8B, która capowała 003b na ~80%, capuje otwarte ukuwanie znacznie
mocniej (~22 byty, potem stall) — bo:
- otwarta inwencja wymaga UCIECZKI z własnych modów fonotaktycznych, czego Jimmy nie potrafi,
- a miękki checker wtedy głoduje (near-dupy odrzucane) LUB przyjmuje śmieci (dziura w bramce).

**Wniosek dla pętli:** stan zewnętrzny + nowość działa, gdy ważność jest TWARDA i przestrzeń
przywoływalna. Otwarta pętla generatywna z Jimmym potrzebowałaby (a) twardszego checkera nowości
(embeddingi + filtr degeneracji), (b) mechanizmu wymuszającego ucieczkę z modów silniejszego niż
prompt "unikaj" (Jimmy go ignoruje). To realne następne kroki, nie ślepa uliczka — ale "za darmo"
otwarta emergencja NIE wychodzi.

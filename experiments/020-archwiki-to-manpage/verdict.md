# 020 — WERDYKT: **KEEP** — ArchWiki → manpage DZIAŁA (hybrid Jimmy-treść + deterministyczny troff)

11 requestów, 0 błędów. Źródło: ArchWiki systemd (~12k tok stripped), 5 chunków. Artefakt: `systemd.1`
(otwiera się w `man ./systemd.1`).

## Wyniki
| ramię | renders | groff warnings | NAME valid | sekcje | faithfulness |
|-------|---------|----------------|-----------|--------|--------------|
| **ARM B — hybrid (Jimmy-treść + det-troff)** | ✅ | **0** | ✅ | NAME/DESCRIPTION/SEE ALSO | **0.86** |
| ARM A — Jimmy emituje troff wprost | ✅ | **15** | ❌ | 3 | — |

Weryfikacja prawdziwym `man ./systemd.1` → renderuje poprawnie (SYSTEMD(1), NAME, DESCRIPTION, COMMANDS,
SEE ALSO). 20 komend wydobytych, 12 refs SEE ALSO (regex, deterministycznie).

## Architektura (potwierdza Prawa 6 + 7)
Pipeline: `strip HTML→txt (deterministycznie) → chunk (≤3.5k tok) → Jimmy wydobywa treść per sekcja man
→ deterministyczny asembler troff + regex SEE ALSO`.
- **Jimmy = treść semantyczna** (NAME phrase, DESCRIPTION przez map→reduce hierarchiczny à la 013,
  COMMANDS jako 'cmd :: desc').
- **Python = formatowanie** (.TH/.SH/.TP, escaping troff, SEE ALSO z regexa) → gwarantuje
  man-compatibility (0 warnings).
- **ARM A (Jimmy wprost troff): działa, ale niechlujnie** — 15 groff-warnings, ZŁAMANY format NAME
  (nie `systemd \- ...`), mniej sekcji. Jimmy potrafi emitować troff, ale z błędami składni/formatu.

## Jakość treści
- **DESCRIPTION: bardzo dobra** — spójna, ugruntowana (faithfulness 0.86, mało halucynacji); hierarchiczny
  reduce z 013 sprawdza się na realnym dokumencie.
- **NAME: dobra** — "Linux system and service manager for the entire system".
- **COMMANDS: dobra po oczyszczeniu** — prawdziwe komendy: `systemctl list-units`, `systemctl edit --full`,
  `systemd-analyze`... z trafnymi opisami. (Uwaga: Jimmy dodawał markdown-numerację wbrew instrukcji —
  deterministyczne czyszczenie parsera to naprawiło; instruction-following na formatowaniu bywa luźne.)
- **SEE ALSO: perfekcyjny** — deterministyczny regex `\w+\(\d\)`, 12 realnych refs.

## Wniosek
**Praktyczne, działające narzędzie: ArchWiki → man page.** Produkuje prawdziwą, man-renderowalną,
wierną stronę (draft-quality, wartą przeglądu, ale użyteczną). Zwycięska architektura raz jeszcze:
mechanika/formatowanie deterministycznie, Jimmy tylko treść semantyczna; chunk→map→reduce hierarchiczny
dla dokumentu > limit kontekstu. Łączy Prawa 4 (bounded reduce), 6 (mechanika→kod), 7 (Jimmy=treść).
Jimmy-wprost-troff to gorszy fallback (warnings, złamany format).

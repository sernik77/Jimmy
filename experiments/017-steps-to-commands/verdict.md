# 017 — WERDYKT: **KEEP dla FORMY, nie dla INTENCJI** — komendy działają (96%), ale ~20% robi nie-to

246 requestów, 0 błędów. 34 kroki z 016 (depth-2 defensive), 30 read-only / 4 mutujące.
Read-only wykonywane w sandboxie (allowlist+blocklist+timeout); mutujące oceniane statycznie.

## Wyniki
| metryka | SINGLE | BEST-of-N | próg KEEP |
|---------|--------|-----------|-----------|
| syntaktyka `bash -n` | 1.00 | **1.00** | ≥0.9 ✅ |
| real-command (nie halucynacja) | 0.85 | **1.00** | ≥0.85 ✅ |
| exec-ok, read-only (faktycznie działa) | 0.65 | **0.96** | ≥0.8 ✅ |
| **dopasowanie semantyczne** (heurystyka) | — | **0.79** | — |

**best-of-N + filtr wykonania znów wygrywa** (real 0.85→1.0, exec 0.65→0.96) — czwarty raz potwierdzony
wzorzec projektu.

## Kluczowy niuans: „działa" ≠ „poprawne"
exec-ok=0.96 mierzy URUCHAMIALNOŚĆ, nie POPRAWNOŚĆ. Dopasowanie semantyczne tylko **0.79** —
~1 na 5 komend działa, ale robi złą rzecz:
- `echo "No pre-existing DB"` dla „confirm no pre-existing DB" — **oszukuje** (nie sprawdza, tylko echuje),
- `echo $(( EUID ))` dla „verify environment type" — bez sensu,
- `rpm -q postgresql` na systemie Debian — **zły package manager** (rpm zamiast dpkg/apt),
- `cat /etc/protocols` dla „identify server type", `echo $HOME/psqlrc` dla „identify PG user/password".

## Bezpieczeństwo: Jimmy emituje GROŹNE komendy
Dla kroku oznaczonego „ATOMIC/verify" Jimmy wygenerował **`init 6` (REBOOT maszyny)**. Allowlist
read-only poprawnie tego NIE wykonał (init spoza allowlisty), podobnie `sudo apt install`, `apt remove
postgresql* -y`. Sandbox się obronił — ale **nigdy nie wykonywać komend Jimmy'ego bez allowlisty /
przeglądu człowieka.** Głupi model wstawia destrukcję nawet w kontekście „weryfikacji".

## Wniosek (domyk pipeline'u 016→017: planner → executor)
Jimmy niezawodnie generuje komendy poprawne w FORMIE (valid 1.0, real 1.0, runnable 0.96 z best-of-N),
ale ~20% jest błędnych w INTENCJI, a część niebezpieczna. Filtr wykonania gwarantuje składnię i
uruchamialność, NIE poprawność semantyczną — deterministyczny weryfikator sprawdza co może, a
**poprawność intencji pozostaje sufitem Jimmy'ego** (powracający motyw: 001-bias, 015-evaluator, teraz
017-komendy).

**Werdykt:** output = **przeglądalna czarnowa automatyzacja** (draft), niezawodna w formie, niegodna
zaufania w intencji. Praktycznie: best-of-N + exec-filter do form-reliability, ale finalna komenda
wymaga (a) allowlisty bezpieczeństwa, (b) przeglądu/semantycznego checkera przed uruchomieniem.
Nie: unattended execution.

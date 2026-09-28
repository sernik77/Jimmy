# 021 — WERDYKT: **PARTIAL KEEP** — działa dla tar (renderuje w prawdziwym tldr), niestabilne dla journalctl

~24 requesty (2 biegi), 0 błędów. Źródła: `man tar`, `man journalctl`. Format tldr Client Spec 2.3.

## Wyniki
| komenda / ramię | renders (tldr) | compliant | n_przykł. | faithfulness |
|-----------------|----------------|-----------|-----------|--------------|
| **tar — ARM B (hybrid)** | ✅ | ✅ | 6 | 1.0 |
| journalctl — ARM B | ✅ (pusto) | ❌ (0 przykł.) | 0 | — |
| tar/journalctl — ARM A (Jimmy wprost md) | ✅ | ❌ (0.0) | 0 | 1.0 |

`tar_B.md` renderuje przez PRAWDZIWY `tldr --render` jak autentyczna strona:
```
- Create an archive:            tar -czf {{archive.tar}}
- Extract a file from an archive: tar -xvf {{archive.tar}} {{file.tar}}
- List the contents of an archive: tar -tvf {{archive.tar}}
```

## Wnioski
1. **Format przez hybrid DZIAŁA gdy przykłady się wyekstraktują** (tar: compliant + renderuje w
   prawdziwym tldr + faithful 1.0), ale **NIESTABILNE między komendami**: journalctl dał 0 przykładów
   (ekstrakcja nie sparsowała linii `journalctl ...`) → niecompliant. Compliance 0.5 na 2 komendach.
2. **ARM A (Jimmy emituje markdown tldr wprost): konsekwentnie NIECOMPLIANT (0.0)** — nie trafia w
   ścisłą strukturę bloków (`- opis:` + pusta + backtick). Jak w 020 (troff): Jimmy-wprost-format zawodzi.
3. **Jakość treści SILNIE zależy od precyzji promptu** (powtórka 012/016): "extract usage examples"
   (mgliste) → płytka enumeracja opcji (`- --create:`, coverage 0); "give the MOST COMMON real-world
   usages, imperative descriptions, prefer short combined flags" (precyzyjne) → idiomatyczna tldr w
   stylu kanonicznej (Create/Extract/List z `tar -czf`). Sam prompt zmienił bezużyteczne w dobre.
4. **Faithfulness perfekcyjny** (1.0) gdy przykłady powstają — brak halucynowanych flag.
5. **Nawet część deterministyczna bywa błędna:** regex URL (pierwszy http w manpage) złapał zły adres
   dla journalctl (spec partycji ≠ homepage). Mechanika też wymaga uwagi.
6. **Metryka coverage-vs-canonical zawiodła** (sygnatura łapała tokeny ścieżek, nie tylko flagi) →
   niekonkluzywna; jakościowo tar pokrywa rdzeń operacji kanonicznej.

## Wniosek
Manpage→tldr działa jako **draft-generator dla dobrze ustrukturyzowanych, bogatych w przykłady
manpage'y** (tar), z precyzyjnym promptem i hybrid-formatowaniem — produkuje prawdziwą, tldr-renderowalną,
wierną stronę. Ale jest **niestabilny per-komenda** (journalctl padł), a jakość zależy od promptu.
Powtarza się: FORMA rozwiązywalna deterministycznie/hybrid; INTENCJA/kuracja (które przykłady są
"najczęstsze") — słaba i prompt-zależna; Jimmy-wprost-format zawodzi. Praktycznie: hybrid + precyzyjny
prompt + human-review, nie w pełni automatycznie.

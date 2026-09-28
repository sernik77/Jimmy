# 009 — Jimmy jako reguła przejścia automatu komórkowego (max abstrakcja)

## Pomysł
Siatka R×C komórek, każda trzyma jedno słowo. Co krok każda komórka pyta Jimmy'ego:
"twoi sąsiedzi to {słowa} — daj jedno słowo najlepiej oddające ich wspólny motyw".
Stan zewnętrzny = siatka. Reguła przejścia = skojarzenia Jimmy'ego. Pytanie: czy z lokalnej
reguły wyłania się GLOBALNA struktura (domeny tematyczne, wzorce), czy to tylko worek niezależnych
przepisań?

## Obserwable (pre-rejestrowane, wszystkie falsyfikowalne)
1. **Activity** — frakcja komórek zmieniających słowo/krok. →0 zamrożenie, →1 chaos,
   stabilne pośrednie = reżim ciekawy.
2. **Entropia** rozkładu słów w siatce w czasie + detekcja cyklu globalnej konfiguracji.
3. **Korelacja przestrzenna** — podobieństwo par SĄSIEDNICH vs par LOSOWYCH (Jaccard na char-3gramach).
   Struktura ⟺ neighbor_sim > random_sim. Jeśli równe → worek niezależnych przepisań, nie CA.
4. **Parse-failure rate/krok** — raportowane OBOK activity (zamrożenie-przez-błąd ≠ atraktor).

## Ramiona (równy budżet requestów)
- **REAL** — sąsiedztwo von Neumanna na torusie (prawdziwa topologia).
- **CTRL** — "sąsiedzi" = 4 LOSOWE komórki z siatki (ta sama liczba requestów).
  To arm-B-analog: jeśli krzywe entropii i korelacji nieodróżnialne → topologia nic nie robi.

## Próg (co uznajemy za "emergencję struktury")
- KEEP: w REAL neighbor_sim − random_sim ≥ +0.10 (utrzymane w 2. połowie biegu) ORAZ różnica
  ta jest ISTOTNIE większa w REAL niż w CTRL (CTRL powinno mieć ~0 z definicji).
- Activity w reżimie pośrednim (0.1–0.9), nie zamrożone przez parse-failure (walidność ≥ 0.6).
- Inaczej DISPOSE: "Jimmy-CA to worek niezależnych przepisań, topologia bez wpływu".

## Parametry
Siatka 6×6=36, kroki=25, 2 ramiona → ~1800 req. Ekstrakcja: pierwszy token alfabetyczny,
lowercase. Niewalidne → zachowaj poprzedni stan (log rate). Init: 36 różnych rzeczowników (hardcode).

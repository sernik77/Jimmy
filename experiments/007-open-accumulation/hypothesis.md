# 007 — Otwarta akumulacja z MIĘKKIM checkerem (nazwana granica Graala)

## Pytanie
003b dowiódł akumulacji nad przestrzenią SKOŃCZONĄ z TWARDYM checkerem (44 kraje, przynależność do
zbioru; nasycenie ~80% = ogon wag 8B). Otwarta granica: czy akumulacja pozostaje otwarta, gdy
przestrzeń jest NIEOGRANICZONA, a checker MIĘKKI (próg dystansu, nie członkostwo)?

Zadanie: wymyślać stworzenia — "Nazwa: cecha". Bramka nowości = leksykalna: kandydat przyjęty, jeśli
max podobieństwo char-3gram jego NAZWY do wszystkich dotychczasowych < 0.5 (łapie warianty
morfologiczne, nie tożsamość). Przestrzeń nazw jest nieskończona.

## Metryka (per advisor — rozmiar zbioru NIE falsyfikuje, rośnie z definicji)
- **PRIMARY: acceptance-rate per runda w czasie.** Zanik →0 = nasycenie mimo rosnącego zbioru.
  Płaski/wysoki = genuinnie otwarte.
- **Odrzucenia rozbite:** dup-wewnątrz-okna (Jimmy widział i powtórzył) vs dup-poza-oknem
  (nie widział, wpadł w mode) — inaczej krzywa zaniku nieinterpretowalna.
- **Różnorodność na osi NIEZALEŻNEJ od bramki:** bramka na char-3gram NAZWY → różnorodność mierzę
  na słowach treści OPISU (nie nazwy). + 15-20 bytów wklejonych dosłownie do werdyktu.

## Próg
- **Otwarte (KEEP):** acceptance-rate w ostatniej 1/3 ≥ 0.5 ORAZ różnorodność opisów nie kolapsuje.
- **Nasycone (DISPOSE):** acceptance-rate zanika < 0.2 → mode-peaking 8B ogranicza też otwartą coinage.

## Parametry
R=20 rund × K=16 kandydatów = 320 req. Okno w promptcie = 25 losowych dotychczasowych nazw.
Bramka globalna (vs cały zbiór, nie tylko okno).

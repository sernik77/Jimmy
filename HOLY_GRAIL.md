# ŚWIĘTY GRAAL — rozstrzygnięcie

> Cel projektu: "nieskończona pętla oparta na Jimmym z właściwościami emergentnymi".

Po eksperymentach 003b, 006, 006b Graal ma konkretną, empiryczną odpowiedź — i to NIE tę, której
się spodziewaliśmy.

## Rozstrzygnięcie: Graal to AKUMULACJA, nie OPTYMALIZACJA

Jedyny wymiar, na którym nasze wyniki faktycznie się różnią, to czy **optimum mieści się w jednym
wyjściu Jimmy'ego**:

| | reżim | kontrola (best-of-N, równy budżet) | pętla | werdykt |
|---|-------|-----------------------------------|-------|---------|
| **006 / 006b** | optimum ⊂ jedno wyjście (GA po skalarze) | znajduje optimum od razu (A=D=20/12) | nic nie dodaje | pętla ZBĘDNA |
| **003b** | cel > jedno wyjście (pokrycie 44 krajów) | **18-25%** (mode-collapse) | **77-80%** (akumulacja) | pętla JEDYNE co działa |

**Wniosek:** emergentna pętla ma sens wtedy i tylko wtedy, gdy buduje strukturę **większą niż
pojedyncza generacja**, w stanie zewnętrznym. Żadne pojedyncze wyjście Jimmy'ego nie zawiera 34
krajów — ta struktura powstała przez akumulację między rundami + presję nowości. To jest
"właściwość emergentna": artefakt, którego model sam z siebie nie wyprodukuje.

Gdy zaś rozwiązanie mieści się w jednym wyjściu, **best-of-N wygrywa** — bo Jimmy jest tak szybki i
różnorodny, że setki próbek znajdują optimum bez żadnej maszynerii ewolucyjnej. Selekcja w pętli
tylko UTRZYMUJE jakość (bez niej: kolaps do niewalidności, 006b arm B: 20→0), nie przekracza jej.

## Ważne zastrzeżenie do confoundu (006/006b)
W obu biegach sufit fitness był ustawiony **w seedzie** i nieruszony przez żadne ramię (ani kontrolę):
konstruowalne 24 nie zostało osiągnięte przez nikogo. Więc 006/006b dowodzą "ewolucja nie bije
próbkowania", ale wiążącym ograniczeniem była **zdolność Jimmy'ego per-wyjście**, nie strategia
przeszukiwania. NIE twierdzimy, że próbkowanie "gęsto pokrywa przestrzeń" — nie pokrywa (24 istnieje,
nieznalezione). To wzmacnia kontrast z 003b, gdzie cel PROWADZALNIE przekracza jedno wyjście.

## Przepis na działającą pętlę emergentną (zwalidowany rdzeń)
1. **Stan zewnętrzny** akumulujący wynik (zbiór / graf / plik / świat).
2. **Jimmy jako operator** generujący kandydatów rozszerzenia stanu (topK=8, różnorodność 1.0).
3. **Presja nowości**: wstrzykuj do promptu "już masz: [próbka stanu], daj COŚ INNEGO".
4. **Deterministyczny filtr** ważności kandydata (checker/walidator) przed dodaniem do stanu.
5. **Metryka różnorodności/wzrostu w czasie** jako raport (nie transkrypty).
→ To dokładnie pętla z 003b (pokrycie 18%→80%).

## Otwarta granica (nazwana, NIEzbadane — następny eksperyment dla kontynuatora)
003b akumuluje nad **skończoną, zewnętrznie-enumerowalną** przestrzenią (44 kraje) z **twardym
checkerem, który zahardkodowałem**. "Nieskończona pętla" implikuje przestrzeń **otwartą**, gdzie
nie da się pre-enumerować poprawnych stanów, a checker jest miękki. Czy akumulacja działa, gdy:
- przestrzeń jest nieograniczona (brak "ogona wag" do nasycenia — 003b nasyciło się na ~80% bo
  trafiło w granicę reprezentacji 8B; przestrzeń otwarta takiej granicy nie ma),
- ważność kandydata ocenia miękki sędzia (np. sam Jimmy albo mocniejszy model), nie zbiór?

To jest prawdziwe następne pytanie Graala — np. otwarte budowanie grafu wiedzy / mapy świata /
rosnącego korpusu, gdzie nowość ocenia embedding-dystans, a nie przynależność do zbioru.
**Status: nierozstrzygnięte.** "Graal = akumulacja" jest udowodnione dla przestrzeni skończonej z
twardym checkerem; dla otwartej — hipoteza.

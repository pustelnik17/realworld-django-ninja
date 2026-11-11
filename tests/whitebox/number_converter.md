Ponizsza analiza pokrycia kodu wykonana była przy uzyciu narzędzia coverage.py. Jedyną zmianą w pliku z testami number_converter_tester.py względem jego poprzedniego stanu była aktualizacja przypadków zwracających "tysiąc",
dodając mozliwość obsługiwania "jeden tysiąc", co nie było jednoznacznie pewne podczas przeprowadzania testów czarnoskrzynkowych.

## Pokrycie kodu funkcji convert_to_polish_name

Pokrycie kodu wynosi 97%, jedna instrukcja nie została pokryta:

| Name | Stmts | Miss | Branch | BrPart | Cover | Missing |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `number_converter_whitebox.py` | 37 | 1 | 22 | 1 | 97% | 45 |
| **TOTAL** | **37** | **1** | **22** | **1** | **97%** | |


## Testy o największym pokryciu

Ponizej znajduje się tabela z procentowymi pokryciami trzech testów o największym pokryciu:

| ID testu | Dane wejściowe | Pokrycie instrukcji i gałęzi |
|---|---:|---:|
| **TC36** | **205020** | **74,58%** |
| TC29 | 10101 | 72,88% |
| TC03 | 999998 | 69,49% |

Największe pokrycie instrukcji i gałęzi łącznie uzyskał TC36, czyli test odpowiedzialny za wejście 205020.
Wynika to z tego, że w jednym wywołaniu funkcja przetwarza zarówno część tysięczną, jak i resztę liczby, a zawarte
w nich zera wymuszają różne ścieżki wykonania warunków. W pomiarze uzyskano 30/37 wykonanych instrukcji oraz 14/22
pokrytych gałęzi dla tego testu, co daje 74,58%.

## Niepokryte linie kodu

Linijka 45 pozostała niepokryta przez przypadki testowe:

```python
if n == 0:      # linia 44
    return ""    # linia 45 — niewykonana
```
Z analizy kodu wynika, że funkcja three_digits_to_words() jest wywoływana wyłącznie dla dodatnich wartości thousands lub remainder.
Dla liczby 0 funkcja convert_to_polish_name() wcześniej zwraca "zero", a zatem nie wywołuje funkcji three_digits_to_word().

## Wnioski

Przeprowadzone testy pozwoliły uzyskać 97% pokrycia kodu, przy czym niepokryty fragment kodu dotyczy warunku nieosiągalnego przez główną funkcję przy poprawnych danych wejściowych, co wskazuje na wysoką skuteczność przygotowanych przypadków testowych. Analizując kod dostarczonej funkcji względem ustalonych testów czarnoskrzynkowych wykryto  rozbieżność w zapisie liczby 1000 – funkcja zwraca „jeden tysiąc”, podczas gdy test oczekuje „tysiąc”, co pokazuje, że wysokie pokrycie kodu nie gwarantuje pełnej poprawności działania programu, a wyniki zależą również od precyzyjnego określenia wymagań.


# Testy białoskrzynkowe - realworld-django-ninja

## 1. Pokrycie kodu
Dla utworzonych wcześniej testów sprawdzone zostało pokrycie kodu, przy użyciu narzędzia coverage.py.
Pomijając pliki testowe i migracyjne aplikacji, uzyskano:

Name                        Stmts   Miss Branch BrPart  Cover   Missing
-----------------------------------------------------------------------
apps/accounts/__init__.py       0      0      0      0   100%
apps/accounts/admin.py          0      0      0      0   100%
apps/accounts/api.py           62      5     16      5    87%   77, 98, 100, 111, 113
apps/accounts/apps.py           4      0      0      0   100%
apps/accounts/models.py        38     12      6      1    61%   13, 18-26, 48, 51, 54
apps/accounts/schemas.py      125      6     12      3    92%   46, 100, 152, 165-167
apps/articles/__init__.py       0      0      0      0   100%
apps/articles/admin.py          8      0      2      0   100%
apps/articles/api.py           91      7     14      2    90%   22, 82-86, 126
apps/articles/apps.py           4      0      0      0   100%
apps/articles/models.py        35      2      2      0    95%   18, 59
apps/articles/schemas.py       55      2      4      2    93%   52, 70
apps/comments/__init__.py       0      0      0      0   100%
apps/comments/admin.py          0      0      0      0   100%
apps/comments/api.py           39      2      6      2    91%   24, 64
apps/comments/apps.py           4      0      0      0   100%
apps/comments/models.py         9      0      0      0   100%
apps/comments/schemas.py       28      0      2      0   100%
helpers/empty.py                5      0      0      0   100%
helpers/exceptions.py          23      4      4      2    78%   26, 29-31
helpers/jwt_utils.py           76     12     18      6    81%   56, 59-60, 65->68, 72-73, 80, 87-88, 90, 95-96, 106
-----------------------------------------------------------------------
TOTAL                         606     52     86     23    88%

Jak widać powyzej 52 linie kodu nie zostały pokryte. Natomiast jeżeli skupimy się wyłącznie na endpointach
w apps/accounts/api.py, apps/articles/api.py i apps/comments/api.py, to w tych trzech plikach niepokrytych jest 14 instrukcji.

## 1.1 Galęzie

Scenariusze testowe i warianty działania
Tabela przedstawia dwa warianty zachowania dla poszczególnych funkcji API i przypisane do nich przypadki testowe.
Warianty opisują sytuacje sprawdzane przez testy, ale nie zawsze odpowiadają odrębnym gałęziom instrukcji warunkowych w kodzie Pythona.

| Funkcja / warunek | Wariant A – testy | Wariant B – testy | Interpretacja |
| :--- | :--- | :--- | :--- |
| Rejestracja: konto może zostać utworzone / konflikt unikalności | TC-01, TC-02 – utworzenie konta | TC-06a (e-mail), TC-06b (nazwa użytkownika) – duplikat | TC-06a/b nie przechodzą, bo API zwraca 409 zamiast 422; to jednak nie wyklucza wykonania ścieżki konfliktu |
| Rejestracja: poprawność pól wejściowych | TC-01 – poprawny zestaw | TC-03, TC-04, TC-05, TC-06c – błędny zestaw | Błędne dane mogą być odrzucane przez schemat zanim wywołany zostanie endpoint |
| Logowanie: użytkownik uwierzytelniony / nieuwierzytelniony | TC-07, TC-10b – poprawne dane | TC-08, TC-09 – błędne hasło lub nieznany e-mail | TC-10 dotyczy brakującego hasła i najpewniej kończy się na walidacji |
| Bieżący użytkownik: token prawidłowy / brak lub błąd tokenu | TC-11, TC-13, TC-13b | TC-12a, TC-12b, TC-15 | Odmowa dostępu przebiega przez kod uwierzytelniania, niekoniecznie przez funkcję `/user`; dwa warianty TC-12b powodują 500 |
| Aktualizacja użytkownika: pole podane / pominięte | TC-13 – `bio`, `image`; TC-13b – aktualizacje częściowe | TC-13b – zachowanie pól pominiętych | Nie ma osobnego testu aktualizacji hasła i jego ograniczeń długości; TC-14 dotyczy konfliktu e-maila |
| Profil: istnieje / nie istnieje | TC-16 | TC-17 | Ścieżka wyszukiwania i 404 w `get_or_404` |
| Follow: rozpoczęcie / zakończenie obserwowania | TC-18a – `POST .../follow` | TC-18a – `DELETE .../follow` | Dwa stany relacji są wywoływane kolejno w jednym teście |
| Follow: żądanie poprawne / nieautoryzowane lub obiekt nieznany | TC-18a | TC-18b (bez tokenu), TC-18c (404) | Brak testów `follow` samego siebie i podwójnego `follow` |
| Tworzenie artykułu: tagi przekazane / pominięte | TC-19 – `tagList=["a","b"]` | TC-19b – brak `tagList` | Rozgałęzienie związane z tworzeniem i przypisywaniem tagów |
| Tworzenie artykułu: poprawne / niepoprawne dane | TC-19, TC-19b | TC-20 (brak pola), TC-21 (brak autoryzacji) | TC-20 i TC-21 mogą kończyć się przed właściwą funkcją widoku |
| Slug artykułu: brak kolizji / kolizja | TC-19, TC-19b | TC-23 – dwa identyczne tytuły | Test TC-23 dopuszcza zarówno skuteczne utworzenie, jak i odpowiedź 422; wynik ścieżki zależy od implementacji |
| Odczyt artykułu: istnieje / brak | TC-22a | TC-22b | Wyszukanie po `slug` lub 404 |
| Aktualizacja artykułu: autor / osoba nieuprawniona | TC-24a | TC-24b | TC-24c bada brak tokenu; TC-24d – nieznany `slug` |
| Aktualizacja artykułu: zmieniane / niezmieniane pola | TC-24a – `body` i `description` | TC-24a – zachowany `title` | Nieprzetestowane są m.in. modyfikacja tytułu i aktualizacja listy tagów |
| Usuwanie artykułu: autor / nie-autor | TC-25a | TC-25b | TC-25c – anonim, TC-25d – nieznany artykuł |
| Lista artykułów: filtr `author` aktywny / brak filtra | TC-26b, TC-26c, TC-26e–TC-26h | TC-26a, TC-26d, TC-26i, TC-26j | Zależność od parametru zapytania |
| Lista artykułów: filtr `tag` aktywny / brak filtra | TC-26d | TC-26a–TC-26c, TC-26e–TC-26j | Testuje gałęzie wyboru zapytania filtrowanego i niefiltrowanego |
| Lista artykułów: filtr `favorited` aktywny / brak filtra | TC-26i | Pozostałe warianty TC-26 | Testuje filtr ulubionych konkretnego użytkownika |
| Paginacja: wynik niepusty / pusty po przesunięciu | TC-26e, TC-26f | TC-26g | Są to stany danych i wynik zapytania, niekoniecznie jawne `if` w Pythonie |
| Feed: obserwowani autorzy / brak obserwowanych | TC-27c | TC-27b, TC-27d | TC-27a sprawdza blokadę bez tokenu; podobnie jak paginacja, różne wyniki mogą przechodzić przez tę samą ścieżkę Pythona |
| Favorite: pierwszy zapis / ponowny zapis | TC-28a, TC-28b | Brak testu ponownego polubienia przez tego samego użytkownika | TC-28b polubia różnymi kontami; nie sprawdza kolizji ponownego polubienia |
| Favorite: polubienie / cofnięcie polubienia | TC-28a, TC-28b | TC-28c | TC-28d sprawdza zależność `favorited` od użytkownika oglądającego |
| Favorite: istniejący / nieistniejący artykuł | TC-28a | TC-28f | TC-28e obejmuje nieautoryzowane żądanie |
| Komentarze: poprawny / błędny komentarz | TC-29a | TC-29b, TC-29c (walidacja), TC-29d (brak tokenu), TC-29e (brak artykułu) | Odmowy z walidacji mogą nie przechodzić przez funkcję `create_comment` |
| Lista komentarzy: lista niepusta / pusta | TC-30a | TC-30b | TC-30c – artykuł nie istnieje; brak odrębnego testu listowania z ważnym tokenem użytkownika |
| Usunięcie komentarza: autor komentarza / autor artykułu | TC-31a – autor komentarza | TC-31b – autor artykułu, lecz nie autor komentarza | TC-31b otrzymał 204 zamiast oczekiwanego 403: badana implementacja dopuszcza tę operację |
| Usunięcie komentarza: osoba całkowicie postronna | Brak implementacji TC-31e | — | Scenariusz opisany w `blackbox.md`, ale nieobecny w `blackbox.py`; trzeba go dodać, aby sprawdzić ścieżkę 403 dla osoby niebędącej autorem komentarza ani artykułu |
| Tagi: użyty tag występuje / brak duplikatów | TC-32a | TC-32b | Dwa warianty danych dla tej samej funkcji pobierania tagów; niekoniecznie osobne gałęzie Pythona |

W 23 miejscach testy wykonały warunek, ale nie przeszły przez wszystkie możliwe ścieżki.
Zapis A ↛ B oznacza niewykonane przejście z linii A do B. Najczęstsze luki dotyczą walidacji danych, nietypowych operacji na relacjach, autoryzacji i obsługi tokenów.
| Plik | Brakujące przejście | Niepokryty wariant / funkcja | Przykład dodatkowego scenariusza |
|---|---|---|---|
| `accounts/api.py` | `76 ↛ 77` | `put_user`: zapis nowego hasła | Aktualizacja `PUT /user` z poprawnym nowym hasłem |
| `accounts/api.py` | `97 ↛ 98` | `follow_profile`: odmowa obserwowania samego siebie | `POST /profiles/{własna_nazwa}/follow` |
| `accounts/api.py` | `99 ↛ 100` | `follow_profile`: odpowiedź 409 przy ponownym follow | Dwukrotny follow tego samego profilu |
| `accounts/api.py` | `110 ↛ 111` | `unfollow_profile`: odmowa unfollow siebie | `DELETE /profiles/{własna_nazwa}/follow` |
| `accounts/api.py` | `112 ↛ 113` | `unfollow_profile`: odpowiedź 409 bez istniejącej relacji | Unfollow bez uprzedniego follow |
| `accounts/models.py` | `10 ↛ 13` | `create_user`: ustawienie hasła jako nieużywalnego | Bezpośrednie wywołanie `create_user` bez hasła; poza poprawną rejestracją RealWorld |
| `accounts/schemas.py` | `45 ↛ 46` | `resolve_following`: ponowna serializacja obiektu `ProfileSchema` | Bezpośrednia ponowna walidacja/serializacja modelu schematu |
| `accounts/schemas.py` | `99 ↛ 100` | `UserInLoginSchema`: odrzucenie pustego loginu/hasła | `POST /users/login` z pustym polem |
| `accounts/schemas.py` | `151 ↛ 152` | `UserInPartialUpdateInSchema`: odrzucenie pustego emailu, username lub hasła | `PUT /user` z pustym `username` |
| `articles/api.py` | `21 ↛ 22` | `favorite`: ponowne polubienie, odpowiedź 409 | Dwukrotne `POST .../favorite` z tym samym tokenem |
| `articles/api.py` | `125 ↛ 126` | `update`: aktualizacja listy tagów | `PUT /articles/{slug}` z `tagList` |
| `articles/schemas.py` | `51 ↛ 52` | `ArticleInCreateSchema`: odrzucenie pustego pola | Tworzenie artykułu z pustym `title`/`description`/`body` |
| `articles/schemas.py` | `69 ↛ 70` | `ArticleInPartialUpdateSchema`: odrzucenie pustego pola | Aktualizacja artykułu z pustym `title` |
| `comments/api.py` | `23 ↛ 24` | `_annotate_author_following`: lista komentarzy dla zalogowanego użytkownika | `GET /articles/{slug}/comments` z ważnym tokenem |
| `comments/api.py` | `63 ↛ 64` | `delete_comment`: odmowa, gdy żądający nie jest autorem komentarza ani artykułu | Usuwanie komentarza przez trzecią osobę (TC-31e, brak w `blackbox.py`) |
| `helpers/exceptions.py` | `25 ↛ 26` | Rozpoznanie błędu unikalności PostgreSQL (`UniqueViolation`) | Test pomocnika dla odpowiedniego backendu/wyjątku |
| `helpers/exceptions.py` | `27 ↛ 29` | Inny rodzaj przyczyny wyjątku niż SQLite i PostgreSQL | Test `clean_integrity_error` z innym `__cause__` |
| `helpers/jwt_utils.py` | `55 ↛ 56` | Akceptowanie nagłówka `Authorization: Bearer …` | Użycie poprawnego tokenu z prefiksem `Bearer` |
| `helpers/jwt_utils.py` | `58 ↛ 59` | Nieznany schemat Authorization przy `pass_even=True` | Odczyt publicznego profilu z nietypowym nagłówkiem |
| `helpers/jwt_utils.py` | `65 ↛ 68` | `authenticate()` zwraca falsy zamiast `AuthDetails` | Wywołanie kontrolowane / sprawdzenie kontraktu biblioteki |
| `helpers/jwt_utils.py` | `70 ↛ 72` | Niepoprawny token na opcjonalnie autoryzowanej trasie | `GET /profiles/...` z niepoprawnym tokenem |
| `helpers/jwt_utils.py` | `89 ↛ 90` | Sesja istnieje, ale wygasła | Ustawienie przeszłej daty ważności sesji |
| `helpers/jwt_utils.py` | `105 ↛ 106` | `create_jwt_token` z przekazanym obiektem `request` | Bezpośrednie wywołanie pomocnika z `request` |

Konteksty coverage.py pozwalają wskazać, które testy wykonały linię zawierającą dany warunek. Nie oznacza to, że te testy wykonały również brakujące przejście;
tabela ułatwia wybór przypadków, które warto rozszerzyć.
| Linia decyzji | Przejście niewykonane | Liczba testów na warunku | Testy z przypisaną linią decyzji |
|---|---|---:|---|
| `apps/accounts/api.py:76` | `76 ↛ 77` | **3** | TC-13, TC-13b, TC-14 |
| `apps/accounts/api.py:97` | `97 ↛ 98` | **3** | TC-18a, TC-27c, TC-27d |
| `apps/accounts/api.py:99` | `99 ↛ 100` | **3** | TC-18a, TC-27c, TC-27d |
| `apps/accounts/api.py:110` | `110 ↛ 111` | **2** | TC-18a, TC-27d |
| `apps/accounts/api.py:112` | `112 ↛ 113` | **2** | TC-18a, TC-27d |
| `apps/accounts/models.py:10` | `10 ↛ 13` | **62** | TC-01, TC-02, TC-06a, TC-06b, TC-07 i 57 pozostałych |
| `apps/accounts/schemas.py:45` | `45 ↛ 46` | **40** | TC-16, TC-18a, TC-19, TC-19b, TC-22a i 35 pozostałych |
| `apps/accounts/schemas.py:99` | `99 ↛ 100` | **5** | TC-07, TC-08, TC-09, TC-10, TC-10b |
| `apps/accounts/schemas.py:151` | `151 ↛ 152` | **1** | TC-14 |
| `apps/articles/api.py:21` | `21 ↛ 22` | **5** | TC-26i, TC-28a, TC-28b, TC-28c, TC-28d |
| `apps/articles/api.py:125` | `125 ↛ 126` | **1** | TC-24a |
| `apps/articles/schemas.py:51` | `51 ↛ 52` | **41** | TC-19, TC-19b, TC-20[body], TC-20[description], TC-20[title] i 36 pozostałych |
| `apps/articles/schemas.py:69` | `69 ↛ 70` | **3** | TC-24a, TC-24b, TC-24d |
| `apps/comments/api.py:23` | `23 ↛ 24` | **3** | TC-30a, TC-30b, TC-31a |
| `apps/comments/api.py:63` | `63 ↛ 64` | **2** | TC-31a, TC-31b |
| `helpers/exceptions.py:25` | `25 ↛ 26` | **2** | TC-06a, TC-06b |
| `helpers/exceptions.py:27` | `27 ↛ 29` | **2** | TC-06a, TC-06b |
| `helpers/jwt_utils.py:55` | `55 ↛ 56` | **1** | TC-12b[] |
| `helpers/jwt_utils.py:58` | `58 ↛ 59` | **1** | TC-12b[] |
| `helpers/jwt_utils.py:65` | `65 ↛ 68` | **53** | TC-10b, TC-11, TC-13, TC-13b, TC-14 i 48 pozostałych |
| `helpers/jwt_utils.py:70` | `70 ↛ 72` | **2** | TC-12b[abc], TC-12b[x.y.z] |
| `helpers/jwt_utils.py:89` | `89 ↛ 90` | **53** | TC-10b, TC-11, TC-13, TC-13b, TC-14 i 48 pozostałych |
| `helpers/jwt_utils.py:105` | `105 ↛ 106` | **62** | TC-01, TC-02, TC-06a, TC-06b, TC-07 i 57 pozostałych |


Osiem niewykonanych przejść pochodzi z czterech warunków, do których testy w ogóle nie dotarły.
Dotyczą one tworzenia superużytkownika, walidacji długości nowego hasła oraz obsługi wyjątku przy tworzeniu artykułu.
| Plik i linia decyzji | Brakujące przejścia | Dlaczego decyzja nie była oceniona? |
|---|---:|---|
| `apps/accounts/models.py:22` | 2 | Warunek `is_staff` w nieuruchomionym `create_superuser()` |
| `apps/accounts/models.py:24` | 2 | Warunek `is_superuser` w nieuruchomionym `create_superuser()` |
| `apps/accounts/schemas.py:165` | 2 | Walidator minimalnej długości nowego hasła podczas aktualizacji profilu nie został uruchomiony |
| `apps/articles/api.py:84` | 2 | Decyzja `if field == "slug"` znajduje się wewnątrz niewykonanego `except IntegrityError` podczas tworzenia artykułu |
| **Łącznie** | **8** |


## 1.2 Testy wykonujące te same fragmenty kodu
Testy obejmują większość typowych ścieżek realizowanych przez endpointy, ale w gałęziach obsługi tokenów,
aktualizacji wybranych pól, duplikatów relacji oraz szczególnych warunków autoryzacji pozostały luki.

| Liczba wspólnych instrukcji na test | Liczba testów w grupie | Testy o identycznym pokryciu |
|---:|---:|---|
| **69** | 5 | TC-26b, TC-26e, TC-26f, TC-26g, TC-26h |
| **7** | 5 | TC-05[@no-local.com], TC-05[a b@c.com], TC-05[a@], TC-05[no-at.example.com], TC-05[plainaddress] |
| **65** | 4 | TC-24c, TC-25c, TC-28e, TC-29d |
| **5** | 4 | TC-12a, TC-15, TC-21, TC-27a |
| **70** | 3 | TC-26a, TC-26d, TC-26j |
| **40** | 3 | TC-20[body], TC-20[description], TC-20[title] |
| **69** | 2 | TC-28a, TC-28b |
| **64** | 2 | TC-32a, TC-32b |
| **27** | 2 | TC-06a, TC-06b |
| **20** | 2 | TC-01, TC-02 |
| **15** | 2 | TC-12b[abc], TC-12b[x.y.z] |
| **6** | 2 | TC-04[password], TC-04[username] |
| **5** | 2 | TC-03[password], TC-03[username] |

Zauważalne są m.in. pary TC-28a/TC-28b (po 69 instrukcji), TC-06a/TC-06b (po 27) oraz grupa TC-26b/TC-26e/TC-26f/TC-26g/TC-26h (po 69). Grupy z niewielką liczbą instrukcji (np. warianty błędnego e-maila) oznaczają przede wszystkim wspólną ścieżkę walidacji, a nie redundantność asercji.

## 1.3 Nieosiągalne fragmenty kodu

Ponizej znajdują się fragmenty kodu nieosiągalne przez prawidłowe wywołania publicznego API RealWorld, zgodne ze specyfikacją:

| Plik | Linie | Fragment kodu | Powód nieosiągalności dla danych zgodnych ze specyfikacją |
| :--- | :--- | :--- | :--- |
| `apps/accounts/models.py` | 13 | `user.set_unusable_password()` | Poprawna rejestracja użytkownika wymaga podania hasła. |
| `apps/accounts/models.py` | 18–26 | `UserManager.create_superuser()` | Specyfikacja API nie przewiduje tworzenia superużytkowników. |
| `apps/accounts/models.py` | 48 | `User.get_full_name()` | Publiczne API nie wywołuje tej metody. |
| `apps/accounts/models.py` | 51 | `User.get_short_name()` | Publiczne API nie wywołuje tej metody. |
| `apps/accounts/models.py` | 54 | `User.is_following()` | Endpointy sprawdzają relacje obserwowania bez wywoływania tej metody. |
| `apps/articles/models.py` | 18 | `Tag.__str__()` | Publiczne API zwraca nazwy tagów bez korzystania z tej metody. |
| `apps/articles/models.py` | 59 | `Article.as_markdown()` | Publiczne API zwraca treść artykułów w JSON i nie wywołuje tej metody. |
Łącznie: 14 niepokrytych instrukcji należących do fragmentów nieosiągalnych przez prawidłowe operacje publicznego API.

## 2 Zmiany w badanych funkcjach

## Przebieg bazowy

Przed wprowadzeniem zmiany uruchomiono pełny zestaw 86 testów na oryginalnej implementacji aplikacji. Uzyskane wyniki przyjęto jako punkt odniesienia do późniejszych eksperymentów.

Wynik przebiegu bazowego:

Liczba wykonanych testów: 86

Testy zaliczone: 80

Testy niezaliczone: 6

Po każdej zmainie ponownie uruchamiano pełny zestaw testów. Za wykrycie zmiany uznawano nowe niepowodzenie testu, który przechodził w przebiegu bazowym.

Przeprowadzono 10 zmian, po jednej dla kazdej z funkcjonalnosci F1 - F10. Ponizej znajduje się tabela z zaplanowanymi zmianami:

| ID | Funkcjonalność | Kontrolowana zmiana w kodzie | Testy, które mogą wykryć błąd |
| :--- | :--- | :--- | :--- |
| Z01 | F1 – Rejestracja | W odpowiedzi rejestracji zwracamy adres e-mail zamiast nazwy użytkownika | TC-01 |
| Z02 | F2 – Logowanie | Zwracamy nieprawidłowy token zamiast prawidłowego JWT | TC-10b |
| Z03 | F3 – Bieżący użytkownik | Podczas aktualizacji profilu nie zapisujemy zmian `bio` i `image` w bazie | TC-13, TC-13b |
| Z04 | F4 – Profile i obserwowanie | Operacja `follow` usuwa relację zamiast ją dodawać | TC-18a, TC-27c |
| Z05 | F5 – Artykuły CRUD | Aktualizacja artykułu zmienia odpowiedź, ale nie zapisuje nowych pól w bazie | TC-24a — możliwe niewykrycie |
| Z06 | F6 – Lista artykułów | Zmieniamy sortowanie z najnowszych na najstarsze | TC-26h |
| Z07 | F7 – Feed | Zwracamy artykuły użytkowników nieobserwowanych zamiast obserwowanych | TC-27b, TC-27c |
| Z08 | F8 – Ulubione | Dodanie artykułu do ulubionych usuwa relację zamiast ją tworzyć | TC-28a, TC-28b, TC-28d |
| Z09 | F9 – Komentarze | Do zapisywanego komentarza dodajemy niezamierzony znak `!` | TC-29a, TC-30a |
| Z10 | F10 – Tagi | Endpoint zawsze zwraca pustą listę tagów | TC-32a, TC-32b |

## 2.1 Dokładne zmiany

### Z01 - Rejestracja

**# PRZED**
```python
"username": user.username,
```

**# PO**
```python
"username": user.email,
```

### Z02 - Logowanie

**# PRZED**
```python
"token": create_jwt_token(jwt_token),
```

**# PO**
```python
"token": "invalid-token",
```

### Z03 - Bieżący użytkownik

**# PRZED**
```python
request.user.save()
```

**# PO**
```python
request.user.save(update_fields=["username"])
```

### Z04 - Profile i obserwowanie

**# PRZED**
```python
profile.followers.add(request.user)
```

**# PO**
```python
profile.followers.remove(request.user)
```

### Z05 - Artykuły (CRUD)

**# PRZED**
```python
article.save(update_fields=updated_fields)
```

**# PO**
```python
article.save(update_fields=["updated"])
```

### Z06 - Lista artykułów

**# PRZED**
```python
queryset = queryset.order_by("-created")
```

**# PO**
```python
queryset = queryset.order_by("created")
```

### Z07 - Feed

**# PRZED**
```python
.filter(author__in=followed_authors)
```

**# PO**
```python
.exclude(author__in=followed_authors)
```

### Z08 - Ulubione

**# PRZED**
```python
article.favorites.add(request.user)
```

**# PO**
```python
article.favorites.remove(request.user)
```

### Z09 - Komentarze

**# PRZED**
```python
content=data.comment.body,
```

**# PO**
```python
content=data.comment.body + "!",
```

### Z10 - Tagi

**# PRZED**
```python
return {"tags": [t.name for t in Tag.objects.all()]}
```

**# PO**
```python
return {"tags": []}
```

## 2.2 Właściwe zmiany w funkcjach

## ZO1

## FAILED tests/blackbox/blackbox.py::TestRegistration::test_tc01_valid_registration
W eksperymencie Z01 zmieniono wartość pola username zwracanego podczas rejestracji na adres e-mail użytkownika.
Po ponownym wykonaniu pełnego zestawu testów test TC-01 wykrył nieprawidłową wartość pola.


## Z02

## FAILED tests/blackbox/blackbox.py::TestLogin::test_tc10b_token_from_login_is_usable

W eksperymencie Z02 prawidłowo generowany token JWT zastąpiono stałą wartością invalid-token. Po uruchomieniu zestawu testów TC-10b wykrył problem,
próbując użyć otrzymanego tokenu do pobrania danych bieżącego użytkownika.

## Z03

## FAILED tests/blackbox/blackbox.py::TestCurrentUser::test_tc13_update_bio_and_image
## FAILED tests/blackbox/blackbox.py::TestCurrentUser::test_tc13b_partial_update_keeps_other_fields

W eksperymencie Z03 zmieniono zapis użytkownika tak, aby aktualizowane było tylko pole username, bez utrwalania zmian bio i image. Po ponownym wykonaniu testów TC-13 i TC-13b wykryły nieprawidłowe działanie aktualizacji profilu,
w tym problem z zachowaniem danych przy częściowej aktualizacji.

## Z04

## FAILED tests/blackbox/blackbox.py::TestProfiles::test_tc18a_follow_and_unfollow
## FAILED tests/blackbox/blackbox.py::TestFeed::test_tc27c_only_followed_authors

W eksperymencie Z04 operację dodawania relacji obserwowania zastąpiono jej usuwaniem. Test TC-18a wykrył nieprawidłowy
stan obserwowania profilu, a TC-27c wykrył jego wpływ na zawartość feedu, który powinien prezentować artykuły obserwowanych autorów.

## Z05

W eksperymencie Z05 ograniczono zapis aktualizowanego artykułu do pola updated, pomijając utrwalenie zmodyfikowanych pól treści i opisu. Zgłoszony przebieg testów nie wykrył tej zmiany. Test TC-24a sprawdza wartości zwracane bezpośrednio po aktualizacji, ale nie pobiera artykułu ponownie z bazy danych.
Aby wykrywać taki błąd, należałoby rozszerzyć go o ponowny odczyt GET i porównanie zapisanych wartości.

## Z06

## FAILED tests/blackbox/blackbox.py::TestArticleList::test_tc26h_newest_first

W eksperymencie Z06 odwrócono sortowanie listy artykułów z malejącego na rosnące według daty utworzenia. Po ponownym uruchomieniu testów TC-26h wykrył,
że artykuły nie są zwracane w oczekiwanej kolejności od najnowszego do najstarszego.

## Z07

## FAILED tests/blackbox/blackbox.py::TestFeed::test_tc27b_empty_when_following_nobody
## FAILED tests/blackbox/blackbox.py::TestFeed::test_tc27c_only_followed_authors
## FAILED tests/blackbox/blackbox.py::TestFeed::test_tc27d_unfollow_removes_from_feed

W eksperymencie Z07 filtrowanie artykułów obserwowanych autorów zastąpiono wybieraniem artykułów autorów nieobserwowanych. Zmianę wykryły TC-27b, TC-27c i TC-27d. Testy ujawniły błędną zawartość feedu
w przypadku braku obserwowanych użytkowników, aktywnej relacji obserwowania oraz zakończenia obserwowania autora.

## Z08

## FAILED tests/blackbox/blackbox.py::TestFavorites::test_tc28a_favorite - asser...
## FAILED tests/blackbox/blackbox.py::TestFavorites::test_tc28b_counter_counts_distinct_users
## FAILED tests/blackbox/blackbox.py::TestFavorites::test_tc28c_unfavorite - ass...
## FAILED tests/blackbox/blackbox.py::TestFavorites::test_tc28d_favorited_flag_is_per_viewer

W eksperymencie Z08 zamiast dodawać użytkownika do listy polubień artykułu, usuwano istniejącą relację. Po ponownym wykonaniu testów TC-28a, TC-28b, TC-28c i TC-28d zakończyły się niepowodzeniem. Wyniki wskazują na wykrycie problemów z operacją polubienia, licznikiem favoritesCount oraz flagą favorited. Dokładna
przyczyna niepowodzenia TC-28c, który sprawdza cofnięcie polubienia, wymaga weryfikacji szczegółowego komunikatu asercji.

## Z09

## FAILED tests/blackbox/blackbox.py::TestComments::test_tc29a_add_comment - Ass...
## FAILED tests/blackbox/blackbox.py::TestComments::test_tc30a_list_comments_public

W eksperymencie Z09 do treści zapisywanego komentarza dodano niezamierzony znak !. Test TC-29a wykrył zmianę
treści zwróconej po utworzeniu komentarza, a TC-30a wykrył niezgodność treści komentarzy podczas pobierania ich listy.

## Z10

## FAILED tests/blackbox/blackbox.py::TestTags::test_tc32a_tags_contains_used_tag
## FAILED tests/blackbox/blackbox.py::TestTags::test_tc32b_tags_unique - Asserti...

W eksperymencie Z10 zmieniono endpoint tagów tak, aby niezależnie od zapisanych danych zwracał pustą listę. Test TC-32a wykrył brak tagu
użytego w artykule, a TC-32b wykrył, że tag dodany do dwóch artykułów nie występuje na liście dokładnie jeden raz.

## 2.3 Podsumowanie eksperymentów
Przeprowadzono 10 eksperymentów polegających na wprowadzeniu niewielkich zmian do badanych funkcji aplikacji.
W przypadku 9 zmian (Z01–Z04 oraz Z06–Z10) testy zakończyły się dodatkowymi niepowodzeniami, co wskazuje na skuteczne wykrycie wprowadzonych błędów.
Jedna zmiana (Z05) nie została wykryta. Polegała ona na pominięciu zapisu zmodyfikowanych danych artykułu do bazy. Test TC-24a sprawdzał odpowiedź na żądanie aktualizacji, ale nie weryfikował trwałości zmian poprzez ponowne pobranie artykułu.
Eksperymenty pokazują, że zestaw testów skutecznie wykrywa większość wprowadzonych zmian, jednak samo pokrycie instrukcji nie gwarantuje wykrycia wszystkich błędów. Istotne jest również sprawdzanie stanu aplikacji po wykonaniu operacji.
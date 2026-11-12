# Testy czarnoskrzynkowe - realworld-django-ninja

Repozytorium systemu: https://github.com/c4ffein/realworld-django-ninja

## 1. Zakres i założenia

Badany system to backend blogowy (klon platformy Medium) w Django Ninja, zgodny ze specyfikacją RealWorld API. W ramach zadania przygotowano testy czarnoskrzynkowe, a ze względu na charakterystykę systemu, jako badane funkcje przyjeto endpointy API, gdzie wejściem jest żądanie HTTP, a wyjściem kod odpowiedzi i JSON. Oczekiwane wyniki wynikają ze specyfikacji RealWorld oraz z ogólnych zasad HTTP/REST.

**Wybrane funkcje systemu do testów:**

|  | Funkcja | Endpoint | Uzasadnienie |
|---|---------|----------|--------------|
| F1 | Rejestracja | `POST /api/users` | punkt wejścia, walidacja danych |
| F2 | Logowanie | `POST /api/users/login` | bezpieczeństwo, wydawanie tokenu |
| F3 | Bieżący użytkownik | `GET/PUT /api/user` | autoryzacja, aktualizacja profilu |
| F4 | Profile i obserwowanie | `GET /api/profiles/{u}`, `POST/DELETE …/follow` | relacje między użytkownikami |
| F5 | Artykuły (CRUD) | `POST/GET/PUT/DELETE /api/articles[/{slug}]` | główna logika domenowa, uprawnienia |
| F6 | Lista artykułów | `GET /api/articles` | filtrowanie, paginacja, sortowanie |
| F7 | Feed | `GET /api/articles/feed` | zależność od relacji follow |
| F8 | Ulubione | `POST/DELETE /api/articles/{slug}/favorite` | liczniki, flaga zależna od widza |
| F9 | Komentarze | `GET/POST /api/articles/{slug}/comments`, `DELETE …/{id}` | CRUD z uprawnieniami |
| F10 | Tagi | `GET /api/tags` | agregacja danych |

## 2. Zastosowane techniki projektowania testów

- **Podział na klasy równoważności**
- **Analiza wartości brzegowych**
- **Testy stanu**
- **Testy negatywne**
- **Tablica decyzyjna uprawnień**

Macierz uprawnień:

| Operacja | Anonim | Zalogowany autor | Zalogowany nie-autor |
|----------|--------|------------------|----------------------|
| Odczyt artykułu / listy / komentarzy / tagów | 200 | 200 | 200 |
| Utworzenie artykułu | 401 | 201 | 201 |
| Edycja / usunięcie artykułu | 401 | 200 | 403 |
| Dodanie komentarza | 401 | 200/201 | 200/201 |
| Usunięcie komentarza | 401 | 200/204 | 403 |
| Favorite / follow / feed | 401 | 200 | 200 |

## 3. Przypadki testowe

**Skróty używane w warunkach wstępnych:**

| Skrót | Znaczenie |
|-------|-----------|
| U, U2, S | zarejestrowani użytkownicy z własnymi, ważnymi tokenami (S - użytkownik postronny, bez związku z danym artykułem) |
| A | artykuł utworzony przez U |
| C | komentarz do artykułu A |
| `{slug A}` | `slug` zwrócony przy tworzeniu artykułu A |

Wszystkie przypadki wymagają, by serwer API był uruchomiony; dane testowe tworzone są w ramach testu z losowymi nazwami.


### F1. Rejestracja - `POST /api/users`

#### TC-01 - Rejestracja z poprawnymi danymi

**Przypadek testowy TC-01**  
**Opis:** sprawdzenie, czy system tworzy konto i zwraca dane użytkownika wraz z tokenem

**Warunki wstępne:** serwer API jest uruchomiony; username i e-mail nie są jeszcze używane

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 01.1 | Wyślij `POST /users` z poprawnym, unikalnym `username`, `email` i `password` w obwiedni `user` | kod 201 |
| 01.2 | Sprawdź pola obiektu `user` w odpowiedzi | `username` i `email` zgodne z wejściem; `token` niepusty; obecne pola `bio` i `image` |

**Warunki wyjściowe:** w systemie istnieje nowe konto, a zwrócony token identyfikuje to konto

#### TC-02 - Hasło nie jest ujawniane w odpowiedzi

**Przypadek testowy TC-02**  
**Opis:** sprawdzenie poufności hasła po rejestracji

**Warunki wstępne:** serwer API jest uruchomiony

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 02.1 | Zarejestruj użytkownika z hasłem `Passw0rd!123` | kod 201 |
| 02.2 | Przeszukaj całą treść odpowiedzi pod kątem hasła i pola `password` | hasła ani pola `password` nie ma w odpowiedzi |

**Warunki wyjściowe:** konto istnieje, a odpowiedź nie zawiera danych poufnych

#### TC-03 - Rejestracja z brakującym polem wymaganym (×3)

**Przypadek testowy TC-03**  
**Opis:** sprawdzenie walidacji obecności pól `username`, `email`, `password`

**Warunki wstępne:** serwer API jest uruchomiony

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 03.1 | Wyślij `POST /users` bez pola `username` (pozostałe poprawne) | kod 422; ciało `{"errors": {...}}` |
| 03.2 | Wyślij `POST /users` bez pola `email` | kod 422; ciało `{"errors": {...}}` |
| 03.3 | Wyślij `POST /users` bez pola `password` | kod 422; ciało `{"errors": {...}}` |

**Warunki wyjściowe:** żadne konto nie zostało utworzone

#### TC-04 - Rejestracja z pustym polem (×3)

**Przypadek testowy TC-04**  
**Opis:** sprawdzenie odrzucania pustych napisów

**Warunki wstępne:** serwer API jest uruchomiony

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 04.1 | Wyślij `POST /users` z `username` równym `""` | kod 422; `errors` |
| 04.2 | Wyślij `POST /users` z `email` równym `""` | kod 422; `errors` |
| 04.3 | Wyślij `POST /users` z `password` równym `""` | kod 422; `errors` |

**Warunki wyjściowe:** żadne konto nie zostało utworzone

#### TC-05 - Rejestracja z niepoprawnym formatem e-maila (×5)

**Przypadek testowy TC-05**  
**Opis:** sprawdzenie walidacji formatu adresu e-mail (klasy niepoprawne)

**Warunki wstępne:** serwer API jest uruchomiony

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 05.1 | Wyślij `POST /users` z `email` = `plainaddress` | kod 422; `errors` |
| 05.2 | Wyślij z `email` = `@no-local.com` | kod 422; `errors` |
| 05.3 | Wyślij z `email` = `no-at.example.com` | kod 422; `errors` |
| 05.4 | Wyślij z `email` = `a@` | kod 422; `errors` |
| 05.5 | Wyślij z `email` = `a b@c.com` | kod 422; `errors` |

**Warunki wyjściowe:** żadne konto nie zostało utworzone

#### TC-06a - Rejestracja z zajętym adresem e-mail

**Przypadek testowy TC-06a**  
**Opis:** sprawdzenie, czy system odrzuca duplikat e-maila

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 06a.1 | Wyślij `POST /users` z e-mailem użytkownika U i nowym, unikalnym `username` | kod 422; `errors` |

**Warunki wyjściowe:** nie powstało drugie konto z tym e-mailem

#### TC-06b - Rejestracja z zajętym username

**Przypadek testowy TC-06b**  
**Opis:** sprawdzenie, czy system odrzuca duplikat nazwy użytkownika

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 06b.1 | Wyślij `POST /users` z `username` użytkownika U i nowym, unikalnym `email` | kod 422; `errors` |

**Warunki wyjściowe:** nie powstało drugie konto z tym username

#### TC-06c - Rejestracja z niepoprawną strukturą JSON

**Przypadek testowy TC-06c**  
**Opis:** sprawdzenie reakcji na brak obwiedni `user`

**Warunki wstępne:** serwer API jest uruchomiony

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 06c.1 | Wyślij `POST /users` z ciałem `{"username":..., "email":..., "password":...}` (bez klucza `user`) | kod 422 |

**Warunki wyjściowe:** żadne konto nie zostało utworzone


### F2. Logowanie - `POST /api/users/login`

#### TC-07 - Logowanie poprawnymi danymi

**Przypadek testowy TC-07**  
**Opis:** sprawdzenie, czy system uwierzytelnia użytkownika i wydaje token

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 07.1 | Wyślij `POST /users/login` z e-mailem i hasłem użytkownika U | kod 200 |
| 07.2 | Sprawdź obiekt `user` w odpowiedzi | `email` i `username` zgodne z danymi U; `token` niepusty |

**Warunki wyjściowe:** użytkownik otrzymał token uwierzytelniający

#### TC-08 - Logowanie ze złym hasłem

**Przypadek testowy TC-08**  
**Opis:** sprawdzenie, czy system odrzuca błędne hasło

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 08.1 | Wyślij `POST /users/login` z poprawnym e-mailem i hasłem `zle-haslo` | kod 401, 403 lub 422 (specyfikacja nie rozstrzyga jednoznacznie) |
| 08.2 | Sprawdź treść odpowiedzi | brak tokenu w odpowiedzi |

**Warunki wyjściowe:** token nie został wydany

#### TC-09 - Logowanie nieistniejącym e-mailem

**Przypadek testowy TC-09**  
**Opis:** sprawdzenie reakcji na nieznane konto

**Warunki wstępne:** serwer API jest uruchomiony

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 09.1 | Wyślij `POST /users/login` z losowym e-mailem, którego nie ma w systemie | kod 401, 403 lub 422 |
| 09.2 | Sprawdź treść odpowiedzi | brak tokenu w odpowiedzi |

**Warunki wyjściowe:** token nie został wydany

#### TC-10 - Logowanie bez hasła

**Przypadek testowy TC-10**  
**Opis:** sprawdzenie obsługi niekompletnych danych logowania

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 10.1 | Wyślij `POST /users/login` tylko z polem `email` | kod 401 lub 422 |

**Warunki wyjściowe:** token nie został wydany

#### TC-10b - Token z logowania umożliwia dostęp do zasobów chronionych

**Przypadek testowy TC-10b**  
**Opis:** sprawdzenie spójności logowania i autoryzacji

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 10b.1 | Zaloguj U i zapamiętaj zwrócony `token` | kod 200 |
| 10b.2 | Wyślij `GET /user` z nagłówkiem `Authorization: Token <token>` | kod 200; `user.email` zgodny z e-mailem U |

**Warunki wyjściowe:** token z logowania jest akceptowany przez system


### F3. Bieżący użytkownik - `GET/PUT /api/user`

#### TC-11 - Pobranie danych zalogowanego użytkownika

**Przypadek testowy TC-11**  
**Opis:** sprawdzenie, czy system zwraca dane właściciela tokenu

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 11.1 | Wyślij `GET /user` z tokenem U | kod 200; `user.username` zgodny z U |

**Warunki wyjściowe:** dane użytkownika nie zostały zmienione

#### TC-12a - Dostęp do `GET /user` bez tokenu

**Przypadek testowy TC-12a**  
**Opis:** sprawdzenie ochrony zasobu przed anonimem

**Warunki wstępne:** serwer API jest uruchomiony

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 12a.1 | Wyślij `GET /user` bez nagłówka `Authorization` | kod 401 |

**Warunki wyjściowe:** dane nie zostały ujawnione

#### TC-12b - Dostęp do `GET /user` z niepoprawnym tokenem (×3)

**Przypadek testowy TC-12b**  
**Opis:** sprawdzenie odporności systemu na błędne tokeny (klasy: losowy napis, napis podobny do JWT, pusty)

**Warunki wstępne:** serwer API jest uruchomiony

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 12b.1 | Wyślij `GET /user` z nagłówkiem `Token abc` | kod 401 |
| 12b.2 | Wyślij `GET /user` z nagłówkiem `Token x.y.z` | kod 401 |
| 12b.3 | Wyślij `GET /user` z nagłówkiem `Token ` (pusty token) | kod 401 |

**Warunki wyjściowe:** dane nie zostały ujawnione; serwer nie zgłasza błędu wewnętrznego

#### TC-13 - Aktualizacja `bio` i `image`

**Przypadek testowy TC-13**  
**Opis:** sprawdzenie, czy zmiana profilu jest zwrócona i zapamiętana

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 13.1 | Wyślij `PUT /user` z `bio`="Moja bio" i `image`="https://example.com/a.png" | kod 200; `user.bio` i `user.image` mają nowe wartości |
| 13.2 | Wyślij `GET /user` z tokenem U | `bio` i `image` nadal mają nowe wartości |

**Warunki wyjściowe:** profil U zawiera nowe `bio` i `image`

#### TC-13b - Aktualizacja częściowa nie zeruje pozostałych pól

**Przypadek testowy TC-13b**  
**Opis:** sprawdzenie, czy pominięte pola zachowują wartości

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 13b.1 | Wyślij `PUT /user` z samym `bio`="bio1" | kod 200 |
| 13b.2 | Wyślij `PUT /user` z samym `image`="https://example.com/b.png" | kod 200; `bio`="bio1"; `username` bez zmian |

**Warunki wyjściowe:** pola, których nie podano w ostatnim żądaniu, zachowały wartości

#### TC-14 - Zmiana e-maila na zajęty przez innego użytkownika

**Przypadek testowy TC-14**  
**Opis:** sprawdzenie ochrony unikalności e-maila przy aktualizacji

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 14.1 | Wyślij `PUT /user` tokenem U z `email` równym e-mailowi U2 | kod 422; `errors` |

**Warunki wyjściowe:** e-mail użytkownika U pozostaje niezmieniony

#### TC-15 - Aktualizacja profilu bez tokenu

**Przypadek testowy TC-15**  
**Opis:** sprawdzenie ochrony `PUT /user` przed anonimem

**Warunki wstępne:** serwer API jest uruchomiony

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 15.1 | Wyślij `PUT /user` z `bio`="x" bez nagłówka `Authorization` | kod 401 |

**Warunki wyjściowe:** żadne dane nie zostały zmienione


### F4. Profile - `GET /api/profiles/{username}`, `POST/DELETE …/follow`

#### TC-16 - Pobranie profilu istniejącego użytkownika

**Przypadek testowy TC-16**  
**Opis:** sprawdzenie zawartości publicznego profilu

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 16.1 | Wyślij `GET /profiles/{username U}` bez tokenu | kod 200 |
| 16.2 | Sprawdź obiekt `profile` | `username` zgodny; `following`=false; brak pola `email` |

**Warunki wyjściowe:** dane profilu nie zostały zmienione

#### TC-17 - Pobranie profilu nieistniejącego użytkownika

**Przypadek testowy TC-17**  
**Opis:** sprawdzenie reakcji na nieznany zasób

**Warunki wstępne:** serwer API jest uruchomiony

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 17.1 | Wyślij `GET /profiles/<losowa nazwa>` | kod 404 |

**Warunki wyjściowe:** brak zmian w systemie

#### TC-18a - Obserwowanie i przestanie obserwowania użytkownika

**Przypadek testowy TC-18a**  
**Opis:** sprawdzenie pełnego cyklu follow → unfollow

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 18a.1 | Wyślij `POST /profiles/{U2}/follow` tokenem U | kod 200; `profile.following`=true |
| 18a.2 | Wyślij `GET /profiles/{U2}` tokenem U | `following`=true |
| 18a.3 | Wyślij `DELETE /profiles/{U2}/follow` tokenem U | kod 200; `profile.following`=false |

**Warunki wyjściowe:** U nie obserwuje U2

#### TC-18b - Obserwowanie bez tokenu

**Przypadek testowy TC-18b**  
**Opis:** sprawdzenie ochrony operacji follow

**Warunki wstępne:** serwer API jest uruchomiony; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 18b.1 | Wyślij `POST /profiles/{U2}/follow` bez tokenu | kod 401 |

**Warunki wyjściowe:** relacja obserwowania nie powstała

#### TC-18c - Obserwowanie nieistniejącego użytkownika

**Przypadek testowy TC-18c**  
**Opis:** sprawdzenie reakcji na nieznany profil

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 18c.1 | Wyślij `POST /profiles/<losowa nazwa>/follow` tokenem U | kod 404 |

**Warunki wyjściowe:** relacja obserwowania nie powstała


### F5. Artykuły - CRUD

#### TC-19 - Utworzenie artykułu z poprawnymi danymi

**Przypadek testowy TC-19**  
**Opis:** sprawdzenie tworzenia artykułu i pól zwracanych

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 19.1 | Wyślij `POST /articles` tokenem U z `title`="Jak testowac", `description`, `body`, `tagList`=["a","b"] | kod 201 |
| 19.2 | Sprawdź pola `article` | `title`, `description`, `body` zgodne z wejściem; `tagList` = {a, b}; niepusty `slug` |
| 19.3 | Sprawdź pola pochodne | `favorited`=false; `favoritesCount`=0; `author.username` = U; obecne `createdAt` i `updatedAt` |

**Warunki wyjściowe:** w systemie istnieje artykuł autorstwa U

#### TC-19b - Utworzenie artykułu bez tagów

**Przypadek testowy TC-19b**  
**Opis:** sprawdzenie wartości domyślnej `tagList`

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 19b.1 | Wyślij `POST /articles` tokenem U bez pola `tagList` | kod 200/201; `article.tagList` = `[]` |

**Warunki wyjściowe:** artykuł istnieje i ma pustą listę tagów

#### TC-20 - Utworzenie artykułu z brakującym polem (×3)

**Przypadek testowy TC-20**  
**Opis:** sprawdzenie walidacji pól wymaganych

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 20.1 | Wyślij `POST /articles` bez `title` | kod 422; `errors` |
| 20.2 | Wyślij `POST /articles` bez `description` | kod 422; `errors` |
| 20.3 | Wyślij `POST /articles` bez `body` | kod 422; `errors` |

**Warunki wyjściowe:** żaden artykuł nie został utworzony

#### TC-21 - Utworzenie artykułu bez tokenu

**Przypadek testowy TC-21**  
**Opis:** sprawdzenie ochrony tworzenia artykułów

**Warunki wstępne:** serwer API jest uruchomiony

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 21.1 | Wyślij `POST /articles` z poprawnym ciałem, bez nagłówka `Authorization` | kod 401 |

**Warunki wyjściowe:** żaden artykuł nie został utworzony

#### TC-22a - Odczyt artykułu po `slug`

**Przypadek testowy TC-22a**  
**Opis:** sprawdzenie publicznego odczytu artykułu

**Warunki wstępne:** serwer API jest uruchomiony; istnieje artykuł A utworzony przez U (z tagiem `bbtag`)

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 22a.1 | Wyślij `GET /articles/{slug A}` bez tokenu | kod 200; `article.title` zgodny z A |

**Warunki wyjściowe:** artykuł nie został zmieniony

#### TC-22b - Odczyt artykułu o nieznanym `slug`

**Przypadek testowy TC-22b**  
**Opis:** sprawdzenie reakcji na nieistniejący zasób

**Warunki wstępne:** serwer API jest uruchomiony

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 22b.1 | Wyślij `GET /articles/<losowy slug>` | kod 404 |

**Warunki wyjściowe:** brak zmian w systemie

#### TC-23 - Dwa artykuły o tym samym tytule

**Przypadek testowy TC-23**  
**Opis:** sprawdzenie zachowania przy kolizji tytułów (specyfikacja nie rozstrzyga)

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 23.1 | Utwórz artykuł A1 tokenem U z tytułem T | kod 200/201 |
| 23.2 | Utwórz tokenem U drugi artykuł z tym samym tytułem T | kod 200/201 albo 422 |
| 23.3 | Jeśli utworzono: porównaj `slug` z A1 | `slug` drugiego artykułu różni się od `slug` A1 |

**Warunki wyjściowe:** żadne dwa artykuły nie dzielą tego samego `slug`

#### TC-24a - Edycja artykułu przez autora

**Przypadek testowy TC-24a**  
**Opis:** sprawdzenie aktualizacji pól artykułu

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem; istnieje artykuł A utworzony przez U (z tagiem `bbtag`)

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 24a.1 | Wyślij `PUT /articles/{slug A}` tokenem U z `body`="nowa tresc" i `description`="nowy opis" | kod 200 |
| 24a.2 | Sprawdź `article` | `body` i `description` nowe; `title` bez zmian |

**Warunki wyjściowe:** artykuł A ma zmienione `body` i `description`

#### TC-24b - Edycja artykułu przez innego użytkownika

**Przypadek testowy TC-24b**  
**Opis:** sprawdzenie reguł uprawnień (nie-autor)

**Warunki wstępne:** serwer API jest uruchomiony; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem; istnieje artykuł A utworzony przez U (z tagiem `bbtag`)

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 24b.1 | Wyślij `PUT /articles/{slug A}` tokenem U2 z `body`="hack" | kod 403 |
| 24b.2 | Wyślij `GET /articles/{slug A}` | `body` nadal równe pierwotnemu |

**Warunki wyjściowe:** artykuł A pozostał niezmieniony

#### TC-24c - Edycja artykułu bez tokenu

**Przypadek testowy TC-24c**  
**Opis:** sprawdzenie ochrony edycji przed anonimem

**Warunki wstępne:** serwer API jest uruchomiony; istnieje artykuł A utworzony przez U (z tagiem `bbtag`)

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 24c.1 | Wyślij `PUT /articles/{slug A}` bez tokenu | kod 401 |

**Warunki wyjściowe:** artykuł A pozostał niezmieniony

#### TC-24d - Edycja nieistniejącego artykułu

**Przypadek testowy TC-24d**  
**Opis:** sprawdzenie reakcji na nieznany zasób

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 24d.1 | Wyślij `PUT /articles/<losowy slug>` tokenem U | kod 404 |

**Warunki wyjściowe:** brak zmian w systemie

#### TC-25a - Usunięcie artykułu przez autora

**Przypadek testowy TC-25a**  
**Opis:** sprawdzenie usuwania i jego skutku

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem; istnieje artykuł A utworzony przez U (z tagiem `bbtag`)

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 25a.1 | Wyślij `DELETE /articles/{slug A}` tokenem U | kod 200 lub 204 |
| 25a.2 | Wyślij `GET /articles/{slug A}` | kod 404 |

**Warunki wyjściowe:** artykuł A nie istnieje

#### TC-25b - Usunięcie artykułu przez innego użytkownika

**Przypadek testowy TC-25b**  
**Opis:** sprawdzenie reguł uprawnień przy usuwaniu

**Warunki wstępne:** serwer API jest uruchomiony; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem; istnieje artykuł A utworzony przez U (z tagiem `bbtag`)

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 25b.1 | Wyślij `DELETE /articles/{slug A}` tokenem U2 | kod 403 |
| 25b.2 | Wyślij `GET /articles/{slug A}` | kod 200 |

**Warunki wyjściowe:** artykuł A nadal istnieje

#### TC-25c - Usunięcie artykułu bez tokenu

**Przypadek testowy TC-25c**  
**Opis:** sprawdzenie ochrony usuwania przed anonimem

**Warunki wstępne:** serwer API jest uruchomiony; istnieje artykuł A utworzony przez U (z tagiem `bbtag`)

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 25c.1 | Wyślij `DELETE /articles/{slug A}` bez tokenu | kod 401 |

**Warunki wyjściowe:** artykuł A nadal istnieje

#### TC-25d - Usunięcie nieistniejącego artykułu

**Przypadek testowy TC-25d**  
**Opis:** sprawdzenie reakcji na nieznany zasób

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 25d.1 | Wyślij `DELETE /articles/<losowy slug>` tokenem U | kod 404 |

**Warunki wyjściowe:** brak zmian w systemie


### F6. Lista artykułów - `GET /api/articles`

#### TC-26a - Struktura odpowiedzi listy

**Przypadek testowy TC-26a**  
**Opis:** sprawdzenie formatu odpowiedzi

**Warunki wstępne:** serwer API jest uruchomiony; istnieje artykuł A utworzony przez U (z tagiem `bbtag`)

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 26a.1 | Wyślij `GET /articles` bez parametrów | kod 200 |
| 26a.2 | Sprawdź typy pól | `articles` jest listą; `articlesCount` jest liczbą całkowitą ≥ długość listy |

**Warunki wyjściowe:** dane nie zostały zmienione

#### TC-26b - Filtrowanie po autorze

**Przypadek testowy TC-26b**  
**Opis:** sprawdzenie filtra `author`

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 26b.1 | Utwórz dwa artykuły tokenem U | kod 200/201 dla obu |
| 26b.2 | Wyślij `GET /articles?author={U}` | lista zawiera dokładnie te dwa artykuły; `articlesCount`=2 |

**Warunki wyjściowe:** dane nie zostały zmienione

#### TC-26c - Filtrowanie po nieistniejącym autorze

**Przypadek testowy TC-26c**  
**Opis:** sprawdzenie pustego wyniku filtra

**Warunki wstępne:** serwer API jest uruchomiony

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 26c.1 | Wyślij `GET /articles?author=<losowa nazwa>` | kod 200; `articles`=[]; `articlesCount`=0 |

**Warunki wyjściowe:** dane nie zostały zmienione

#### TC-26d - Filtrowanie po tagu

**Przypadek testowy TC-26d**  
**Opis:** sprawdzenie filtra `tag`

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 26d.1 | Utwórz artykuł z unikalnym tagiem T oraz artykuł z tagiem `inny` | kod 200/201 |
| 26d.2 | Wyślij `GET /articles?tag=T` | lista zawiera tylko artykuł z tagiem T |

**Warunki wyjściowe:** dane nie zostały zmienione

#### TC-26e - Ograniczenie liczby wyników (`limit`)

**Przypadek testowy TC-26e**  
**Opis:** wartość brzegowa: `limit` mniejszy od liczby wyników

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem ma 3 artykuły

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 26e.1 | Wyślij `GET /articles?author={U}&limit=2` | kod 200; w `articles` są 2 elementy; `articlesCount`=3 |

**Warunki wyjściowe:** dane nie zostały zmienione

#### TC-26f - Przesunięcie wyników (`offset`)

**Przypadek testowy TC-26f**  
**Opis:** sprawdzenie paginacji

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem ma 3 artykuły

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 26f.1 | Wyślij `GET /articles?author={U}` (bez offsetu) i zapamiętaj kolejność `slug` | kod 200 |
| 26f.2 | Wyślij `GET /articles?author={U}&offset=1&limit=10` | lista równa liście pełnej bez pierwszego elementu |

**Warunki wyjściowe:** dane nie zostały zmienione

#### TC-26g - `offset` większy od liczby wyników

**Przypadek testowy TC-26g**  
**Opis:** wartość brzegowa: przesunięcie poza zakres

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem ma 1 artykuł

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 26g.1 | Wyślij `GET /articles?author={U}&offset=100` | kod 200; `articles`=[]; `articlesCount`=1 |

**Warunki wyjściowe:** dane nie zostały zmienione

#### TC-26h - Kolejność: najnowsze najpierw

**Przypadek testowy TC-26h**  
**Opis:** sprawdzenie sortowania

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 26h.1 | Utwórz artykuł 1, odczekaj ok. 1,1 s, utwórz artykuł 2 | kod 200/201 |
| 26h.2 | Wyślij `GET /articles?author={U}` | kolejność: artykuł 2, artykuł 1 |

**Warunki wyjściowe:** dane nie zostały zmienione

#### TC-26i - Filtrowanie po ulubionych (`favorited`)

**Przypadek testowy TC-26i**  
**Opis:** sprawdzenie filtra `favorited`

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem ma 2 artykuły

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 26i.1 | Wyślij `POST /articles/{slug pierwszego}/favorite` tokenem U | kod 200 |
| 26i.2 | Wyślij `GET /articles?favorited={U}` | lista zawiera tylko polubiony artykuł |

**Warunki wyjściowe:** tylko jeden artykuł jest polubiony przez U

#### TC-26j - Pola elementu listy

**Przypadek testowy TC-26j**  
**Opis:** sprawdzenie kompletności pól w elemencie listy

**Warunki wstępne:** serwer API jest uruchomiony; istnieje artykuł A utworzony przez U (z tagiem `bbtag`)

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 26j.1 | Wyślij `GET /articles?author={U}` | kod 200 |
| 26j.2 | Sprawdź pierwszy element | obecne: `slug`, `title`, `description`, `tagList`, `createdAt`, `updatedAt`, `favorited`, `favoritesCount`, `author` |

**Warunki wyjściowe:** dane nie zostały zmienione


### F7. Feed - `GET /api/articles/feed`

#### TC-27a - Feed bez tokenu

**Przypadek testowy TC-27a**  
**Opis:** sprawdzenie ochrony feedu

**Warunki wstępne:** serwer API jest uruchomiony

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 27a.1 | Wyślij `GET /articles/feed` bez tokenu | kod 401 |

**Warunki wyjściowe:** brak zmian

#### TC-27b - Feed użytkownika, który nikogo nie obserwuje

**Przypadek testowy TC-27b**  
**Opis:** sprawdzenie pustego feedu

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem nikogo nie obserwuje

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 27b.1 | Wyślij `GET /articles/feed` tokenem U | kod 200; `articles`=[]; `articlesCount`=0 |

**Warunki wyjściowe:** brak zmian

#### TC-27c - Feed zawiera tylko artykuły obserwowanych autorów

**Przypadek testowy TC-27c**  
**Opis:** sprawdzenie zależności feedu od relacji follow

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem; istnieje trzeci użytkownik U3

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 27c.1 | Utwórz artykuł tokenem U2 i artykuł tokenem U3 | kod 200/201 |
| 27c.2 | Wyślij `POST /profiles/{U2}/follow` tokenem U | kod 200 |
| 27c.3 | Wyślij `GET /articles/feed` tokenem U | lista zawiera tylko artykuł U2 |

**Warunki wyjściowe:** U obserwuje wyłącznie U2

#### TC-27d - Przestanie obserwowania usuwa artykuły z feedu

**Przypadek testowy TC-27d**  
**Opis:** sprawdzenie reakcji feedu na unfollow

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem ma 1 artykuł

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 27d.1 | Wyślij `POST /profiles/{U2}/follow` tokenem U | kod 200 |
| 27d.2 | Wyślij `DELETE /profiles/{U2}/follow` tokenem U | kod 200 |
| 27d.3 | Wyślij `GET /articles/feed` tokenem U | `articles`=[] |

**Warunki wyjściowe:** U nikogo nie obserwuje


### F8. Ulubione - `POST/DELETE /api/articles/{slug}/favorite`

#### TC-28a - Polubienie artykułu

**Przypadek testowy TC-28a**  
**Opis:** sprawdzenie flagi i licznika po polubieniu

**Warunki wstępne:** serwer API jest uruchomiony; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem; istnieje artykuł A utworzony przez U (z tagiem `bbtag`)

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 28a.1 | Wyślij `POST /articles/{slug A}/favorite` tokenem U2 | kod 200 |
| 28a.2 | Sprawdź `article` | `favorited`=true; `favoritesCount`=1 |

**Warunki wyjściowe:** A jest polubiony przez U2

#### TC-28b - Licznik zlicza różnych użytkowników

**Przypadek testowy TC-28b**  
**Opis:** sprawdzenie sumowania polubień

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem; istnieje artykuł A utworzony przez U (z tagiem `bbtag`)

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 28b.1 | Polub A tokenem U | kod 200 |
| 28b.2 | Polub A tokenem U2 | kod 200; `favoritesCount`=2 |

**Warunki wyjściowe:** A jest polubiony przez U i U2

#### TC-28c - Cofnięcie polubienia

**Przypadek testowy TC-28c**  
**Opis:** sprawdzenie flagi i licznika po `DELETE`

**Warunki wstępne:** serwer API jest uruchomiony; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem; istnieje artykuł A utworzony przez U (z tagiem `bbtag`)

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 28c.1 | Polub A tokenem U2 | kod 200 |
| 28c.2 | Wyślij `DELETE /articles/{slug A}/favorite` tokenem U2 | kod 200; `favorited`=false; `favoritesCount`=0 |

**Warunki wyjściowe:** A nie jest polubiony przez nikogo

#### TC-28d - Flaga `favorited` zależy od oglądającego

**Przypadek testowy TC-28d**  
**Opis:** sprawdzenie widoku per użytkownik

**Warunki wstępne:** serwer API jest uruchomiony; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem; istnieje artykuł A utworzony przez U (z tagiem `bbtag`), polubiony przez U2

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 28d.1 | Wyślij `GET /articles/{slug A}` tokenem U2 | `favorited`=true |
| 28d.2 | Wyślij `GET /articles/{slug A}` bez tokenu | `favorited`=false; `favoritesCount`=1 |

**Warunki wyjściowe:** dane nie zostały zmienione

#### TC-28e - Polubienie bez tokenu

**Przypadek testowy TC-28e**  
**Opis:** sprawdzenie ochrony operacji

**Warunki wstępne:** serwer API jest uruchomiony; istnieje artykuł A utworzony przez U (z tagiem `bbtag`)

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 28e.1 | Wyślij `POST /articles/{slug A}/favorite` bez tokenu | kod 401 |

**Warunki wyjściowe:** licznik polubień bez zmian

#### TC-28f - Polubienie nieistniejącego artykułu

**Przypadek testowy TC-28f**  
**Opis:** sprawdzenie reakcji na nieznany zasób

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 28f.1 | Wyślij `POST /articles/<losowy slug>/favorite` tokenem U | kod 404 |

**Warunki wyjściowe:** brak zmian


### F9. Komentarze - `/api/articles/{slug}/comments`

#### TC-29a - Dodanie komentarza

**Przypadek testowy TC-29a**  
**Opis:** sprawdzenie tworzenia komentarza i pól zwracanych

**Warunki wstępne:** serwer API jest uruchomiony; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem; istnieje artykuł A utworzony przez U (z tagiem `bbtag`)

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 29a.1 | Wyślij `POST /articles/{slug A}/comments` tokenem U2 z `body`="swietny tekst" | kod 200 lub 201 |
| 29a.2 | Sprawdź `comment` | `body` zgodne; `author.username` = U2; obecne `id`, `createdAt`, `updatedAt` |

**Warunki wyjściowe:** A ma jeden komentarz autorstwa U2

#### TC-29b - Dodanie komentarza bez `body`

**Przypadek testowy TC-29b**  
**Opis:** sprawdzenie walidacji obecności pola

**Warunki wstępne:** serwer API jest uruchomiony; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem; istnieje artykuł A utworzony przez U (z tagiem `bbtag`)

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 29b.1 | Wyślij `POST …/comments` z ciałem `{"comment": {}}` | kod 422 |

**Warunki wyjściowe:** komentarz nie został dodany

#### TC-29c - Dodanie komentarza z pustym `body`

**Przypadek testowy TC-29c**  
**Opis:** wartość brzegowa: pusty napis

**Warunki wstępne:** serwer API jest uruchomiony; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem; istnieje artykuł A utworzony przez U (z tagiem `bbtag`)

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 29c.1 | Wyślij `POST …/comments` z `body`="" | kod 422 |

**Warunki wyjściowe:** komentarz nie został dodany

#### TC-29d - Dodanie komentarza bez tokenu

**Przypadek testowy TC-29d**  
**Opis:** sprawdzenie ochrony operacji

**Warunki wstępne:** serwer API jest uruchomiony; istnieje artykuł A utworzony przez U (z tagiem `bbtag`)

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 29d.1 | Wyślij `POST …/comments` bez tokenu | kod 401 |

**Warunki wyjściowe:** komentarz nie został dodany

#### TC-29e - Dodanie komentarza do nieistniejącego artykułu

**Przypadek testowy TC-29e**  
**Opis:** sprawdzenie reakcji na nieznany zasób

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 29e.1 | Wyślij `POST /articles/<losowy slug>/comments` tokenem U | kod 404 |

**Warunki wyjściowe:** brak zmian

#### TC-30a - Publiczna lista komentarzy

**Przypadek testowy TC-30a**  
**Opis:** sprawdzenie odczytu komentarzy przez anonima

**Warunki wstępne:** serwer API jest uruchomiony; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem; istnieje artykuł A utworzony przez U (z tagiem `bbtag`) z komentarzami „pierwszy” i „drugi”

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 30a.1 | Wyślij `GET /articles/{slug A}/comments` bez tokenu | kod 200; `comments` zawiera oba komentarze |

**Warunki wyjściowe:** dane nie zostały zmienione

#### TC-30b - Pusta lista komentarzy

**Przypadek testowy TC-30b**  
**Opis:** sprawdzenie artykułu bez komentarzy

**Warunki wstępne:** serwer API jest uruchomiony; istnieje artykuł A utworzony przez U (z tagiem `bbtag`) bez komentarzy

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 30b.1 | Wyślij `GET /articles/{slug A}/comments` | kod 200; `comments`=[] |

**Warunki wyjściowe:** dane nie zostały zmienione

#### TC-30c - Lista komentarzy nieistniejącego artykułu

**Przypadek testowy TC-30c**  
**Opis:** sprawdzenie reakcji na nieznany zasób

**Warunki wstępne:** serwer API jest uruchomiony

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 30c.1 | Wyślij `GET /articles/<losowy slug>/comments` | kod 404 |

**Warunki wyjściowe:** brak zmian

#### TC-31a - Usunięcie komentarza przez jego autora

**Przypadek testowy TC-31a**  
**Opis:** sprawdzenie usuwania i jego skutku

**Warunki wstępne:** serwer API jest uruchomiony; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem; istnieje artykuł A utworzony przez U (z tagiem `bbtag`) z komentarzem C autorstwa U2

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 31a.1 | Wyślij `DELETE /articles/{slug A}/comments/{id C}` tokenem U2 | kod 200 lub 204 |
| 31a.2 | Wyślij `GET /articles/{slug A}/comments` | `comments`=[] |

**Warunki wyjściowe:** komentarz C nie istnieje

#### TC-31b - Usunięcie komentarza przez autora artykułu (nie autora komentarza)

**Przypadek testowy TC-31b**  
**Opis:** sprawdzenie reguł uprawnień przy usuwaniu komentarza; w teście usuwającym jest U - autor artykułu, a komentarz napisał U2

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem; istnieje artykuł A utworzony przez U (z tagiem `bbtag`) z komentarzem C autorstwa U2

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 31b.1 | Wyślij `DELETE /articles/{slug A}/comments/{id C}` tokenem U | oczekiwano kodu 403 |
| 31b.2 | Wyślij `GET /articles/{slug A}/comments` | oczekiwano: komentarz C nadal istnieje |

**Warunki wyjściowe:** komentarz C nadal istnieje (przy założeniu, że autor artykułu nie moderuje komentarzy)

#### TC-31c - Usunięcie komentarza bez tokenu

**Przypadek testowy TC-31c**  
**Opis:** sprawdzenie ochrony operacji

**Warunki wstępne:** serwer API jest uruchomiony; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem; istnieje artykuł A utworzony przez U (z tagiem `bbtag`) z komentarzem C

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 31c.1 | Wyślij `DELETE …/comments/{id C}` bez tokenu | kod 401 |

**Warunki wyjściowe:** komentarz C nadal istnieje

#### TC-31d - Usunięcie nieistniejącego komentarza

**Przypadek testowy TC-31d**  
**Opis:** sprawdzenie reakcji na nieznany zasób

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem; istnieje artykuł A utworzony przez U (z tagiem `bbtag`)

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 31d.1 | Wyślij `DELETE /articles/{slug A}/comments/99999999` tokenem U | kod 404 |

**Warunki wyjściowe:** brak zmian

#### TC-31e - Usunięcie komentarza przez użytkownika niezwiązanego z artykułem i komentarzem

**Przypadek testowy TC-31e**  
**Opis:** jednoznaczny test autoryzacji: usuwający nie jest ani autorem komentarza, ani autorem artykułu

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem; istnieje drugi zarejestrowany użytkownik U2 z własnym tokenem; istnieje użytkownik postronny S; istnieje artykuł A utworzony przez U (z tagiem `bbtag`) z komentarzem C autorstwa U2

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 31e.1 | Wyślij `DELETE /articles/{slug A}/comments/{id C}` tokenem S | kod 403 |
| 31e.2 | Wyślij `GET /articles/{slug A}/comments` | komentarz C nadal istnieje |

**Warunki wyjściowe:** komentarz C nadal istnieje


### F10. Tagi - `GET /api/tags`

#### TC-32a - Tag użyty w artykule występuje na liście tagów

**Przypadek testowy TC-32a**  
**Opis:** sprawdzenie agregacji tagów

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 32a.1 | Utwórz artykuł z unikalnym tagiem T | kod 200/201 |
| 32a.2 | Wyślij `GET /tags` | kod 200; `tags` jest listą napisów; zawiera T |

**Warunki wyjściowe:** dane nie zostały zmienione

#### TC-32b - Tagi na liście są unikalne

**Przypadek testowy TC-32b**  
**Opis:** sprawdzenie braku duplikatów

**Warunki wstępne:** serwer API jest uruchomiony; istnieje zarejestrowany użytkownik U z ważnym tokenem

| Krok | Czynność | Oczekiwany wynik |
|------|----------|------------------|
| 32b.1 | Utwórz dwa artykuły z tym samym tagiem T | kod 200/201 dla obu |
| 32b.2 | Wyślij `GET /tags` | T występuje na liście dokładnie raz |

**Warunki wyjściowe:** dane nie zostały zmienione


Łącznie: **86 przypadków** (po rozwinięciu parametryzacji), zaimplementowanych w klasach `TestRegistration`, `TestLogin`, `TestCurrentUser`, `TestProfiles`, `TestArticleCreateRead`, `TestArticleUpdateDelete`, `TestArticleList`, `TestFeed`, `TestFavorites`, `TestComments`, `TestTags`.


Każdy test tworzy własnych użytkowników i dane z losowymi nazwami, więc testy są niezależne od siebie i od kolejności, a baza nie wymaga czyszczenia.

## 4. Wyniki wykonania

**Środowisko:** Windows, Python 3.12.10, pytest 9.2.0, aplikacja uruchomiona lokalnie, data uruchomienia 2026-11-09.

| Liczba testów | Zaliczone | Niezaliczone | Czas |
|---------------|-----------|--------------|------|
| 85 | 80 | 5 | 516,92 s (8 min 36 s) |

### 4.1 Testy niezaliczone

| Test | Wejście | Oczekiwano | Otrzymano | Klasyfikacja |
|------|---------|------------|-----------|--------------|
| TC-06a | rejestracja z e-mailem istniejącego użytkownika | 422 | 409 | odstępstwo od specyfikacji, niska waga |
| TC-06b | rejestracja z username istniejącego użytkownika | 422 | 409 | odstępstwo od specyfikacji, niska waga |
| TC-12b `abc` | `GET /user`, nagłówek `Token abc` | 401 | 500 | **defekt**, wysoka waga |
| TC-12b `x.y.z` | `GET /user`, nagłówek `Token x.y.z` | 401 | 500 | **defekt**, wysoka waga |
| TC-14 | `PUT /user` z e-mailem innego użytkownika | 422 | 500 | **defekt**, wysoka waga |

### 4.2 Analiza

**TC-06a, TC-06b - kod 409 zamiast 422.** Aplikacja poprawnie odrzuca duplikat, ale zwraca 409 Conflict. Specyfikacja RealWorld wymaga 422 dla błędów walidacji, więc jest to drobne odstępstwo od kontraktu API, które może zepsuć klientów oczekujących 422. Sam kod 409 jest uzasadniony semantycznie w REST.

**TC-12b - 500 dla zniekształconego tokenu.** Aplikacja zwraca błąd serwera zamiast 401. Pusty token (trzeci przypadek parametryzacji) został obsłużony poprawnie, więc problem dotyczy niepustych, ale niepoprawnych tokenów. Dane od klienta nie powinny powodować błędu 500, a w praktyce każdy może go wywołać jednym żądaniem.

**TC-14 - 500 przy zmianie e-maila na zajęty.** Aplikacja nie odrzuca takiej zmiany kontrolowanym błędem walidacji, tylko kończy się błędem serwera. Przy rejestracji ten sam rodzaj kolizji jest obsłużony poprawnie (409), więc ścieżka aktualizacji profilu jest niespójna z rejestracją.

### 4.3 Podsumowanie

- 80 z 85 przypadków (94%) zakończyło się zgodnie z oczekiwaniem. Bez żadnego niepowodzenia przeszły obszary: logowanie, profile i follow, CRUD artykułów, lista i filtry, feed, ulubione oraz tagi.
- Potwierdzone defekty (3 testy): błędy 500 zamiast kontrolowanych odpowiedzi 4xx dla zniekształconego tokenu (TC-12b) i dla kolizji e-maila przy aktualizacji profilu (TC-14).
- Odstępstwo od specyfikacji (2 testy): 409 zamiast 422 przy duplikacie rejestracji (TC-06a, TC-06b).
- Czas wykonania (ok. 8,5 min) jest długi jak na 86 testów. Główne źródła narzutu to prawdopodobnie tworzenie świeżego użytkownika w każdym teście oraz `sleep` w TC-26h.
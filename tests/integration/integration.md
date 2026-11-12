# Testy integracyjne - realworld-django-ninja

Repozytorium systemu: https://github.com/c4ffein/realworld-django-ninja

# Zadanie 1. Scenariusze testów integracyjnych

## 1.1 Elementy systemu i punkty integracji

System to backend REST (Django Ninja) zgodny ze specyfikacją RealWorld. Elementy wyróżniono po zachowaniu widocznym z zewnątrz, przez API.

W tabelach zawarto elementy systemu oraz testowane punkty integracji.

| Skrót | Element | Rola |
|-------|---------|------|
| E1 | Uwierzytelnianie | rejestracja, logowanie, wydawanie i weryfikacja tokenu (`Authorization: Token …`) |
| E2 | Użytkownicy i profile | dane konta, `bio`, `image`, relacja follow |
| E3 | Artykuły i tagi | tworzenie, edycja, usuwanie, lista z filtrami, tagi |
| E4 | Ulubione | polubienia, flaga `favorited`, licznik `favoritesCount` |
| E5 | Komentarze | dodawanie, lista, usuwanie komentarzy artykułu |
| E6 | Baza danych | trwałe przechowywanie danych wszystkich elementów |



| Punkt integracji | Elementy | Co należy zbadać |
|------------------|----------|---------------|
| P1 | E1 - E3 | token wydany przy rejestracji i logowaniu jest poprawnie rozpoznawany przy tworzeniu i edycji artykułów |
| P2 | E2 - E3 | dane profilu (`bio`, `image`, `following`) są poprawnie przekazywane do danych autora w artykułach i feedzie |
| P3 | E3 - E4 - E6 | polubienia wpływają na artykuł, listę z filtrem `favorited` i licznik, i nie zależą od relacji follow |
| P4 | E3 - E5 - E6 | komentarze i polubienia są powiązane z artykułem; po usunięciu artykułu nie zostają „osierocone” dane |
| P5 | E1 - E2 | zmiana danych logowania (e-mail) jest spójnie widoczna w logowaniu i tokenach |

## 1.2 Scenariusze testów integracyjnych

Oznaczenia: U, U2 – zarejestrowani użytkownicy z własnymi tokenami;

A – artykuł; 

Slug A – `slug`, czyli skrót nazwy artykułu wraz z losowymi znakami kończącymi, zwrócony przy tworzeniu A.

hasło testowe: `Passw0rd!123`.

### IT-01 - Rejestracja („happy path”)

**Punkty integracji:** E1, E3, E6  
**Cel:** sprawdzenie, że konto utworzone w E1 jest rozpoznawane przez E3, a dane trwale zapisane.

**Stan początkowy:** serwer działa; nazwa użytkownika i e-mail nie są jeszcze używane.  
**Dane wejściowe:** `username` = `userXXXX`, `email` = `userXXXX@example.com`, hasło `Passw0rd!123`; dwa artykuły z tytułami „Z logowania …” i „Z rejestracji …”.

| Krok | Działanie | Oczekiwany wynik |
|------|-----------|------------------|
| 1.1 | `POST /users` z danymi konta | 201; zwrócony `token` T1 |
| 1.2 | `POST /users/login` tym samym e-mailem i hasłem | 200; zwrócony `token` T2 |
| 1.3 | `POST /articles` z tokenem T2, następnie drugi artykuł z tokenem T1 | 201 dla obu; oba tokeny są akceptowane |
| 1.4 | `GET /articles/{slug}` bez tokenu | 200; `author.username` = `userXXXX` |
| 1.5 | `GET /articles?author=userXXXX` | oba artykuły na liście; `articlesCount` = 2 |
| 1.6 | `GET /user` z tokenem T2 | 200; `username` = `userXXXX` |

**Miejsca obserwacji:** odpowiedzi HTTP z kroków 1.1–1.6 (kod i JSON); trwałość danych widoczna w krokach 1.4–1.5.  
**Warunki końcowe:** istnieje konto i dwa jego artykuły.

### IT-02 - Followowanie artykułów

**Punkty integracji:** E1, E3, E4, E6  
**Cel:** sprawdzenie współpracy relacji follow, listy artykułów i polubień.

**Stan początkowy:** U (czytelnik) i U2 (autor); U2 ma jeden artykuł A z unikalnym tagiem; U nikogo nie obserwuje.  
**Dane wejściowe:** tokeny U i U2, Slug A.

| Krok | Działanie | Oczekiwany wynik |
|------|-----------|------------------|
| 2.1 | `GET /articles/feed` tokenem U | 200; `articles` = [] |
| 2.2 | `POST /profiles/{U2}/follow` tokenem U | 200; `following` = true |
| 2.3 | `GET /articles/feed` tokenem U | tylko A; `author.following` = true |
| 2.4 | `POST /articles/Slug A/favorite` tokenem U | 200; `favorited` = true; `favoritesCount` = 1 |
| 2.5 | `GET /articles/feed` tokenem U oraz `GET /articles?favorited={U}` | A ma `favorited` = true i licznik 1; filtr zwraca tylko A |
| 2.6 | `GET /articles/Slug A` bez tokenu | `favorited` = false; `favoritesCount` = 1 |
| 2.7 | `DELETE /profiles/{U2}/follow` tokenem U, potem `GET /articles/feed` i `GET /articles?favorited={U}` | feed pusty; filtr ulubionych nadal zwraca A (polubienie niezależne od follow) |
| 2.8 | `DELETE /articles/Slug A/favorite` tokenem U | `favoritesCount` = 0; filtr ulubionych pusty |

**Miejsca obserwacji:** odpowiedzi HTTP; pola `author.following`, `favorited`, `favoritesCount`, zawartość `articles` w feedzie i na liście.  
**Warunki końcowe:** U nie obserwuje U2 i nie ma polubień; A istnieje.

### IT-03 - Wpyw usunięcia artykułu na dane powiązane

**Punkty integracji:** E3, E5, E6  
**Cel:** sprawdzenie, że usunięcie artykułu porządkuje komentarze, polubienia i listy.

**Stan początkowy:** U2 (autor) ma artykuł A z unikalnym tagiem; U (komentujący) dodał dwa komentarze i polubił A.  
**Dane wejściowe:** komentarze „pierwszy” i „drugi”, tokeny U i U2.

| Krok | Działanie | Oczekiwany wynik |
|------|-----------|------------------|
| 3.1 | `POST …/comments` tokenem U (2 razy) i `POST …/favorite` | 200/201 dla komentarzy; 200 dla polubienia |
| 3.2 | `GET /articles/Slug A/comments` | 2 komentarze: „pierwszy”, „drugi” |
| 3.3 | `DELETE /articles/Slug A` tokenem U2 | 200 lub 204 |
| 3.4 | `GET /articles/Slug A` oraz `GET …/comments` | 404 oba |
| 3.5 | `DELETE …/comments/{id komentarza}` tokenem U | 404 |
| 3.6 | `GET /articles?author={U2}`, `?tag={tag}`, `?favorited={U}` | puste listy; dla autora `articlesCount` = 0 |

**Miejsca obserwacji:** kody odpowiedzi i zawartość list z kroków 3.4–3.6.  
**Warunki końcowe:** artykuł A i jego komentarze nie istnieją; lista polubień U jest pusta.

### IT-04 - Wpyw zmian w profilu na dane autora w artykułach

**Punkty integracji:** E2, E3 
**Cel:** sprawdzenie spójności danych użytkownika w różnych widokach.

**Stan początkowy:** U ma artykuł A.  
**Dane wejściowe:** `bio` = „Nowe bio autora”, `image` = `https://example.com/avatar.png`.

| Krok | Działanie | Oczekiwany wynik |
|------|-----------|------------------|
| 4.1 | `PUT /user` tokenem U z nowymi `bio` i `image` | 200 |
| 4.2 | `GET /profiles/{U}` | `bio` i `image` nowe |
| 4.3 | `GET /articles/Slug A` | `author.bio` i `author.image` nowe; `author.username` bez zmian |
| 4.4 | `GET /articles?author={U}` | pierwszy element ma te same nowe `author.bio` i `author.image` |

**Miejsca obserwacji:** pola profilu i obiektu `author` w trzech odpowiedziach (profil, artykuł, lista).  
**Warunki końcowe:** wszystkie trzy widoki pokazują te same dane.

### IT-05 - Przekazanie nieaktualnego slug-a między elementami

**Punkty integracji:** E3, E4, E5, E6  
**Cel:** sprawdzenie, że identyfikator usuniętego zasobu jest odrzucany kontrolowanym błędem, a ponowne utworzenie artykułu nie dziedziczy starych danych.

**Stan początkowy:** U2 (autor) ma artykuł A o tytule T; U (czytelnik) dodał komentarz i polubił A; następnie U2 usunął A.  
**Dane wejściowe:** nieaktualny Slug A, tytuł T.

| Krok | Działanie | Oczekiwany wynik |
|------|-----------|------------------|
| 5.1 | `POST` i `DELETE /articles/Slug A/favorite` tokenem U | 404 oba |
| 5.2 | `POST /articles/Slug A/comments` tokenem U | 404 |
| 5.3 | `PUT /articles/Slug A` tokenem U2 | 404 |
| 5.4 | Utworzenie nowego artykułu A2 o tytule T tokenem U2 | 201 |
| 5.5 | `GET /articles/{slug A2}` i `GET …/comments` tokenem U | `favoritesCount` = 0; `favorited` = false; komentarze = [] |

**Miejsca obserwacji:** kody odpowiedzi (oczekiwany 404, nie 500), pola `favoritesCount`, `favorited` i lista komentarzy nowego artykułu.  
**Warunki końcowe:** istnieje tylko A2, bez polubień i komentarzy.

### IT-06 - Wprowadzenie starych danych do logowania po zmianie e-maila

**Punkty integracji:** E1, E2, E3 
**Cel:** sprawdzenie, że zmiana e-maila odcina stare dane logowania, a nowe działają, bez naruszenia treści użytkownika.

**Stan początkowy:** U z e-mailem E1 i artykułem A.  
**Dane wejściowe:** nowy e-mail E2 (`nowyXXXX@example.com`).

| Krok | Działanie | Oczekiwany wynik |
|------|-----------|------------------|
| 6.1 | `PUT /user` tokenem U z `email` = E2 | 200; `user.email` = E2 |
| 6.2 | `POST /users/login` z e-mailem E1 | 401, 403 lub 422; brak tokenu |
| 6.3 | `POST /users/login` z e-mailem E2 | 200; nowy `token` T3 |
| 6.4 | `GET /user` tokenem T3 | `email` = E2; `username` bez zmian |
| 6.5 | `GET /articles/Slug A` | 200; `author.username` = U |
| 6.6 | `PUT /articles/Slug A` tokenem T3 | 200 |

**Miejsca obserwacji:** kody odpowiedzi logowania, pola `email` i `username`, odpowiedzi edycji artykułu.  
**Warunki końcowe:** U loguje się wyłącznie e-mailem E2; artykuł A jest dostępny i edytowalny.

## 1.3 Wykonanie testów manualnych

Testy manualne przeprowadzono z wykorzystaniem narzędzia Postman, które umożliwia wysyłanie żądań HTTP do testowanego interfejsu API oraz analizę otrzymywanych odpowiedzi. Istotną zaletą tego rozwiązania jest możliwość łatwego przekazywania tokenu autoryzacyjnego, uzyskiwany jest w wyniku pomyślnego zarejestrowania użytkownika lub przeprowadzenia procesu logowania, w nagłówkach żądań.

W ramach testów realizowano kolejne scenariusze, zgodnie z wcześniej określonymi założeniami. Dla każdego z nich wykonywano odpowiednie żądania, a następnie weryfikowano otrzymane odpowiedzi pod kątem zgodności z oczekiwanym zachowaniem systemu. Wszystkie przeprowadzone scenariusze zakończyły się wynikiem pozytywnym, co oznacza, że zaobserwowane zachowanie systemu było zgodne z przyjętymi oczekiwaniami.

### Potencjalne błędy integracyjne

| Potencjalny błąd | Gdzie mógłby wystąpić | Jak zapobiegać |
|------------------|-----------------------|----------------|
| Osierocone komentarze lub polubienia po usunięciu artykułu | IT-03, IT-05 | usuwanie kaskadowe w bazie; test regresyjny po każdej zmianie modeli |
| Nieaktualne dane autora w liście lub feedzie (np. stare `bio`) | IT-04 | pobierać dane autora z jednego źródła, bez kopii w artykułach |
| Przeniesienie polubień lub komentarzy na nowy artykuł o tym samym `slug` | IT-05 | unikalne identyfikatory wewnętrzne, niewykorzystywanie ponownie `slug` powiązanych z usuniętymi danymi |
| Stary e-mail nadal pozwala na logowanie, albo nowy nie działa | IT-06 | testy logowania po każdej zmianie danych konta |
| Błąd 500 zamiast 4xx przy niepoprawnych danych z innej warstwy | IT-05| centralna obsługa wyjątków zwracająca kontrolowane odpowiedzi 4xx |

# Zadanie 2. Automatyzacja testów integracji

## 2.1 Wybór wariantu i uzasadnienie

W ramach zadania wybrano wariant A, ponieważ:
- Badany system to backend REST bez własnego interfejsu użytkownika, więc testy E2E w przeglądarce nie mają dla niego zastosowania.
- Scenariusze z Zadania 1 są sekwencjami żądań HTTP z jednoznacznymi oczekiwaniami (kody i pola JSON), więc prosto zaimplementować je w ramach automatycznych testów.

## 2.2 Zaimplementowane testy

Plik: `tests/integration.py`.

| Scenariusz | Funkcja testowa | Rodzaj |
|------------|-----------------|--------|
| IT-01 | `test_it01_register_login_publish_read` | poprawny |
| IT-02 | `test_it02_follow_feed_favorite_flow` | poprawny |
| IT-03 | `test_it03_article_delete_leaves_no_dependent_data` | poprawny |
| IT-04 | `test_it04_profile_update_visible_in_articles` | poprawny |
| IT-05 | `test_it05_stale_slug_is_rejected_and_leaves_no_ghost_data` | negatywny |
| IT-06 | `test_it06_email_change_affects_login_but_not_content` | negatywny |

Spełnienie wymagań zadania testowania:

| Wymaganie | Jak zostało spełnione |
|-----------|---------------|
| Przygotowanie wymaganego stanu | każdy test sam tworzy użytkowników, artykuły, komentarze i relacje potrzebne w scenariuszu |
| Sprawdzanie rezultatu integracji | asercje na danych, które przechodzą między elementami (autor w artykule, feed po follow, listy po usunięciu) |
| Jednoznaczne asercje | każdy krok ma konkretny oczekiwany kod i pola; tolerancja kodów tylko tam, gdzie specyfikacja na to pozwala |
| Możliwość ponownego uruchomienia | nazwy użytkowników i tytuły są losowe, więc kolejne uruchomienia nie kolidują ze sobą|
| Sprzątanie danych | artykuły, komentarze i polubienia są usuwane po każdym teście |


Dane użytkowników niestety nie są w pełni sprzątane, ponieważ API nie udostępnia możliwości usuwania kont, więc użytkownicy zostają w bazie Rozwiązane zostało to przez tworzenie nowego użytkownika dla każdego zadania. Po przeprowadzeniu wszystkich testów baza danych jest czyszczona. Wymagany jest też uruchomiony serwer pod adresem `API_URL`.

## 2.3 Wynik działania testów automatycznych

| Data | Środowisko | Liczba testów | Zaliczone | Niezaliczone | Czas |
|------|------------|---------------|-----------|--------------|------|
|  10.11.2026    |        Python 3.12    | 6             |     6      |         0     |   2:30 min  | 



| Element Systemu | Status w testach |
|---------|------------------|
| Serwer aplikacji Django Ninja (E1–E5) | rzeczywisty, uruchomiony lokalnie |
| Baza danych SQL lite (E6) | rzeczywista, ta, z którą działa serwer; obserwowana pośrednio przez API |
| Uwierzytelnianie i tokeny | rzeczywiste, tokeny wydawane przez system |
| Klient HTTP | wykorzystanie biblioteki `requests` w roli przeglądarki użytkownika |

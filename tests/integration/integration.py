import os
import uuid

import pytest
import requests

BASE = os.environ.get("API_URL", "http://localhost:8000/api").rstrip("/")
TIMEOUT = 10
PASSWORD = "Passw0rd!123"


def uniq(prefix="u"):
    return f"{prefix}{uuid.uuid4().hex[:10]}"


def call(method, path, token=None, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Token {token}"
    return requests.request(method, BASE + path, headers=headers, timeout=TIMEOUT, **kwargs)


def register(username=None, email=None, password=PASSWORD):
    username = username or uniq("user")
    email = email or f"{username}@example.com"
    r = call("POST", "/users", json={"user": {"username": username, "email": email, "password": password}})
    return r, {"username": username, "email": email, "password": password}


def login(email, password=PASSWORD):
    return call("POST", "/users/login", json={"user": {"email": email, "password": password}})


def make_user():
    r, creds = register()
    assert r.status_code in (200, 201), r.text
    creds["token"] = r.json()["user"]["token"]
    return creds


def slugs(response):
    return [a["slug"] for a in response.json()["articles"]]


@pytest.fixture
def created_articles():
    """Rejestr utworzonych artykulow; po tescie sa usuwane (sprzatanie danych).
    Uzytkownikow nie da sie usunac przez API - maja losowe nazwy, wiec nie koliduja
    przy ponownym uruchomieniu (patrz ograniczenia w TESTY_INTEGRACYJNE.md)."""
    created = []
    yield created
    for slug, token in created:
        try:
            call("DELETE", f"/articles/{slug}", token=token)  # 404, jesli test juz usunal
        except requests.RequestException:
            pass


def publish(created, token, title=None, tags=None, description="opis", body="tresc"):
    payload = {"title": title or uniq("Tytul "), "description": description, "body": body}
    if tags is not None:
        payload["tagList"] = tags
    r = call("POST", "/articles", token=token, json={"article": payload})
    assert r.status_code in (200, 201), r.text
    article = r.json()["article"]
    created.append((article["slug"], token))
    return article


def test_it01_register_login_publish_read(created_articles):
    r, creds = register()
    assert r.status_code == 201
    token_from_registration = r.json()["user"]["token"]

    r = login(creds["email"], creds["password"])
    assert r.status_code == 200
    token_from_login = r.json()["user"]["token"]

    a1 = publish(created_articles, token_from_login, title=uniq("Z logowania "))
    a2 = publish(created_articles, token_from_registration, title=uniq("Z rejestracji "))

    r = call("GET", f"/articles/{a1['slug']}")
    assert r.status_code == 200
    assert r.json()["article"]["author"]["username"] == creds["username"]

    r = call("GET", "/articles", params={"author": creds["username"]})
    assert r.status_code == 200
    assert set(slugs(r)) == {a1["slug"], a2["slug"]}
    assert r.json()["articlesCount"] == 2

    me = call("GET", "/user", token=token_from_login).json()["user"]
    assert me["username"] == creds["username"]


def test_it02_follow_feed_favorite_flow(created_articles):
    reader, author = make_user(), make_user()
    art = publish(created_articles, author["token"], tags=[uniq("tag")])

    assert call("GET", "/articles/feed", token=reader["token"]).json()["articles"] == []

    r = call("POST", f"/profiles/{author['username']}/follow", token=reader["token"])
    assert r.status_code == 200 and r.json()["profile"]["following"] is True
    feed = call("GET", "/articles/feed", token=reader["token"])
    assert feed.status_code == 200
    assert slugs(feed) == [art["slug"]]
    assert feed.json()["articles"][0]["author"]["following"] is True

    r = call("POST", f"/articles/{art['slug']}/favorite", token=reader["token"])
    assert r.status_code == 200
    assert r.json()["article"]["favorited"] is True and r.json()["article"]["favoritesCount"] == 1

    feed_item = call("GET", "/articles/feed", token=reader["token"]).json()["articles"][0]
    assert feed_item["favorited"] is True and feed_item["favoritesCount"] == 1

    fav_list = call("GET", "/articles", params={"favorited": reader["username"]})
    assert slugs(fav_list) == [art["slug"]]

    anon = call("GET", f"/articles/{art['slug']}").json()["article"]
    assert anon["favorited"] is False and anon["favoritesCount"] == 1

    call("DELETE", f"/profiles/{author['username']}/follow", token=reader["token"])
    assert call("GET", "/articles/feed", token=reader["token"]).json()["articles"] == []
    assert slugs(call("GET", "/articles", params={"favorited": reader["username"]})) == [art["slug"]]

    r = call("DELETE", f"/articles/{art['slug']}/favorite", token=reader["token"])
    assert r.json()["article"]["favoritesCount"] == 0
    assert call("GET", "/articles", params={"favorited": reader["username"]}).json()["articles"] == []


def test_it03_article_delete_leaves_no_dependent_data(created_articles):
    author, commenter = make_user(), make_user()
    tag = uniq("tag")
    art = publish(created_articles, author["token"], tags=[tag])

    r1 = call("POST", f"/articles/{art['slug']}/comments", token=commenter["token"], json={"comment": {"body": "pierwszy"}})
    r2 = call("POST", f"/articles/{art['slug']}/comments", token=commenter["token"], json={"comment": {"body": "drugi"}})
    assert r1.status_code in (200, 201) and r2.status_code in (200, 201)
    comment_id = r1.json()["comment"]["id"]
    assert call("POST", f"/articles/{art['slug']}/favorite", token=commenter["token"]).status_code == 200

    comments = call("GET", f"/articles/{art['slug']}/comments").json()["comments"]
    assert sorted(c["body"] for c in comments) == ["drugi", "pierwszy"]

    # usuniecie artykulu
    r = call("DELETE", f"/articles/{art['slug']}", token=author["token"])
    assert r.status_code in (200, 204)

    # artykul i wszystko, co z nim powiazane, przestaje byc dostepne
    assert call("GET", f"/articles/{art['slug']}").status_code == 404
    assert call("GET", f"/articles/{art['slug']}/comments").status_code == 404
    assert call("DELETE", f"/articles/{art['slug']}/comments/{comment_id}", token=commenter["token"]).status_code == 404

    by_author = call("GET", "/articles", params={"author": author["username"]}).json()
    assert by_author["articles"] == [] and by_author["articlesCount"] == 0
    assert call("GET", "/articles", params={"tag": tag}).json()["articles"] == []
    assert call("GET", "/articles", params={"favorited": commenter["username"]}).json()["articles"] == []


def test_it04_profile_update_visible_in_articles(created_articles):
    user = make_user()
    art = publish(created_articles, user["token"])

    new_bio, new_image = "Nowe bio autora", "https://example.com/avatar.png"
    r = call("PUT", "/user", token=user["token"], json={"user": {"bio": new_bio, "image": new_image}})
    assert r.status_code == 200

    profile = call("GET", f"/profiles/{user['username']}").json()["profile"]
    assert profile["bio"] == new_bio and profile["image"] == new_image

    author = call("GET", f"/articles/{art['slug']}").json()["article"]["author"]
    assert author["username"] == user["username"]
    assert author["bio"] == new_bio and author["image"] == new_image

    listed = call("GET", "/articles", params={"author": user["username"]}).json()["articles"][0]["author"]
    assert listed["bio"] == new_bio and listed["image"] == new_image


def test_it05_stale_slug_is_rejected_and_leaves_no_ghost_data(created_articles):
    author, reader = make_user(), make_user()
    title = uniq("Ten sam tytul ")
    art = publish(created_articles, author["token"], title=title)

    call("POST", f"/articles/{art['slug']}/comments", token=reader["token"], json={"comment": {"body": "stary komentarz"}})
    call("POST", f"/articles/{art['slug']}/favorite", token=reader["token"])
    assert call("DELETE", f"/articles/{art['slug']}", token=author["token"]).status_code in (200, 204)

    # operacje na nieaktualnym slugu: kontrolowany blad 404 (nie 500), bez skutkow ubocznych
    stale = art["slug"]
    assert call("POST", f"/articles/{stale}/favorite", token=reader["token"]).status_code == 404
    assert call("DELETE", f"/articles/{stale}/favorite", token=reader["token"]).status_code == 404
    r = call("POST", f"/articles/{stale}/comments", token=reader["token"], json={"comment": {"body": "po usunieciu"}})
    assert r.status_code == 404
    r = call("PUT", f"/articles/{stale}", token=author["token"], json={"article": {"body": "x"}})
    assert r.status_code == 404

    # ponowne utworzenie artykulu o tym samym tytule nie dziedziczy "duchow" po starym
    art2 = publish(created_articles, author["token"], title=title)
    assert art2["favoritesCount"] == 0
    assert call("GET", f"/articles/{art2['slug']}/comments").json()["comments"] == []
    again = call("GET", f"/articles/{art2['slug']}", token=reader["token"]).json()["article"]
    assert again["favorited"] is False and again["favoritesCount"] == 0


def test_it06_email_change_affects_login_but_not_content(created_articles):
    user = make_user()
    art = publish(created_articles, user["token"])
    old_email, new_email = user["email"], f"{uniq('nowy')}@example.com"

    r = call("PUT", "/user", token=user["token"], json={"user": {"email": new_email}})
    assert r.status_code == 200
    assert r.json()["user"]["email"] == new_email

    assert login(old_email).status_code in (401, 403, 422)
    r = login(new_email)
    assert r.status_code == 200
    new_token = r.json()["user"]["token"]

    me = call("GET", "/user", token=new_token).json()["user"]
    assert me["email"] == new_email and me["username"] == user["username"]
    still = call("GET", f"/articles/{art['slug']}").json()["article"]
    assert still["author"]["username"] == user["username"]
    r = call("PUT", f"/articles/{art['slug']}", token=new_token, json={"article": {"body": "edycja po zmianie e-maila"}})
    assert r.status_code == 200

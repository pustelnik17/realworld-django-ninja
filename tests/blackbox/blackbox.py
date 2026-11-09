import os
import time
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


def make_user():
    r, creds = register()
    assert r.status_code in (200, 201), r.text
    creds["token"] = r.json()["user"]["token"]
    return creds


def make_article(token, title=None, description="opis", body="tresc", tags=None):
    payload = {"title": title or uniq("Tytul "), "description": description, "body": body}
    if tags is not None:
        payload["tagList"] = tags
    r = call("POST", "/articles", token=token, json={"article": payload})
    assert r.status_code in (200, 201), r.text
    return r.json()["article"]


def assert_error_format(response):
    """Bledy walidacji powinny miec format {"errors": {...}}."""
    body = response.json()
    assert "errors" in body and isinstance(body["errors"], dict) and body["errors"]


@pytest.fixture
def user():
    return make_user()


@pytest.fixture
def other_user():
    return make_user()


@pytest.fixture
def article(user):
    return make_article(user["token"], tags=["bbtag"])


class TestRegistration:
    def test_tc01_valid_registration(self):
        r, creds = register()
        assert r.status_code == 201
        u = r.json()["user"]
        assert u["username"] == creds["username"]
        assert u["email"] == creds["email"]
        assert isinstance(u["token"], str) and u["token"]
        assert "bio" in u and "image" in u

    def test_tc02_password_never_returned(self):
        r, creds = register()
        assert creds["password"] not in r.text
        assert "password" not in r.json()["user"]

    @pytest.mark.parametrize("missing", ["username", "email", "password"])
    def test_tc03_missing_required_field(self, missing):
        name = uniq("user")
        data = {"username": name, "email": f"{name}@example.com", "password": PASSWORD}
        del data[missing]
        r = call("POST", "/users", json={"user": data})
        assert r.status_code == 422
        assert_error_format(r)

    @pytest.mark.parametrize("field", ["username", "email", "password"])
    def test_tc04_empty_string_field(self, field):
        name = uniq("user")
        data = {"username": name, "email": f"{name}@example.com", "password": PASSWORD}
        data[field] = ""
        r = call("POST", "/users", json={"user": data})
        assert r.status_code == 422
        assert_error_format(r)

    @pytest.mark.parametrize("bad_email", ["plainaddress", "@no-local.com", "no-at.example.com", "a@", "a b@c.com"])
    def test_tc05_invalid_email_format(self, bad_email):
        r, _ = register(email=bad_email)
        assert r.status_code == 422
        assert_error_format(r)

    def test_tc06a_duplicate_email(self, user):
        r, _ = register(email=user["email"])
        assert r.status_code == 422
        assert_error_format(r)

    def test_tc06b_duplicate_username(self, user):
        r, _ = register(username=user["username"])
        assert r.status_code == 422
        assert_error_format(r)

    def test_tc06c_malformed_body_without_user_envelope(self):
        r = call("POST", "/users", json={"username": uniq(), "email": "a@b.com", "password": PASSWORD})
        assert r.status_code == 422


class TestLogin:
    def test_tc07_valid_login(self, user):
        r = call("POST", "/users/login", json={"user": {"email": user["email"], "password": user["password"]}})
        assert r.status_code == 200
        u = r.json()["user"]
        assert u["email"] == user["email"]
        assert u["username"] == user["username"]
        assert u["token"]

    def test_tc08_wrong_password(self, user):
        r = call("POST", "/users/login", json={"user": {"email": user["email"], "password": "zle-haslo"}})
        assert r.status_code in (401, 403, 422)
        assert "token" not in r.text

    def test_tc09_unknown_email(self):
        r = call("POST", "/users/login", json={"user": {"email": f"{uniq()}@nowhere.com", "password": PASSWORD}})
        assert r.status_code in (401, 403, 422)
        assert "token" not in r.text

    def test_tc10_missing_password(self, user):
        r = call("POST", "/users/login", json={"user": {"email": user["email"]}})
        assert r.status_code in (401, 422)

    def test_tc10b_token_from_login_is_usable(self, user):
        r = call("POST", "/users/login", json={"user": {"email": user["email"], "password": user["password"]}})
        token = r.json()["user"]["token"]
        r2 = call("GET", "/user", token=token)
        assert r2.status_code == 200
        assert r2.json()["user"]["email"] == user["email"]


class TestCurrentUser:
    def test_tc11_get_current_user(self, user):
        r = call("GET", "/user", token=user["token"])
        assert r.status_code == 200
        assert r.json()["user"]["username"] == user["username"]

    def test_tc12a_no_token(self):
        assert call("GET", "/user").status_code == 401

    @pytest.mark.parametrize("bad", ["abc", "x.y.z", ""])
    def test_tc12b_invalid_token(self, bad):
        r = call("GET", "/user", headers={"Authorization": f"Token {bad}"})
        assert r.status_code == 401

    def test_tc13_update_bio_and_image(self, user):
        upd = {"bio": "Moja bio", "image": "https://example.com/a.png"}
        r = call("PUT", "/user", token=user["token"], json={"user": upd})
        assert r.status_code == 200
        assert r.json()["user"]["bio"] == "Moja bio"
        assert r.json()["user"]["image"] == "https://example.com/a.png"
        again = call("GET", "/user", token=user["token"]).json()["user"]
        assert again["bio"] == "Moja bio"

    def test_tc13b_partial_update_keeps_other_fields(self, user):
        call("PUT", "/user", token=user["token"], json={"user": {"bio": "bio1"}})
        r = call("PUT", "/user", token=user["token"], json={"user": {"image": "https://example.com/b.png"}})
        assert r.status_code == 200
        assert r.json()["user"]["bio"] == "bio1"
        assert r.json()["user"]["username"] == user["username"]

    def test_tc14_update_email_to_existing(self, user, other_user):
        r = call("PUT", "/user", token=user["token"], json={"user": {"email": other_user["email"]}})
        assert r.status_code == 422
        assert_error_format(r)

    def test_tc15_update_without_token(self):
        assert call("PUT", "/user", json={"user": {"bio": "x"}}).status_code == 401


class TestProfiles:
    def test_tc16_get_profile(self, user):
        r = call("GET", f"/profiles/{user['username']}")
        assert r.status_code == 200
        p = r.json()["profile"]
        assert p["username"] == user["username"]
        assert p["following"] is False
        assert "email" not in p

    def test_tc17_profile_not_found(self):
        assert call("GET", f"/profiles/{uniq('nikt')}").status_code == 404

    def test_tc18a_follow_and_unfollow(self, user, other_user):
        r = call("POST", f"/profiles/{other_user['username']}/follow", token=user["token"])
        assert r.status_code == 200 and r.json()["profile"]["following"] is True
        seen = call("GET", f"/profiles/{other_user['username']}", token=user["token"])
        assert seen.json()["profile"]["following"] is True
        r = call("DELETE", f"/profiles/{other_user['username']}/follow", token=user["token"])
        assert r.status_code == 200 and r.json()["profile"]["following"] is False

    def test_tc18b_follow_requires_auth(self, other_user):
        assert call("POST", f"/profiles/{other_user['username']}/follow").status_code == 401

    def test_tc18c_follow_unknown_user(self, user):
        assert call("POST", f"/profiles/{uniq('nikt')}/follow", token=user["token"]).status_code == 404


class TestArticleCreateRead:
    def test_tc19_create_valid(self, user):
        r = call("POST", "/articles", token=user["token"], json={"article": {
            "title": "Jak testowac", "description": "krotki opis", "body": "tresc", "tagList": ["a", "b"]}})
        assert r.status_code == 201
        a = r.json()["article"]
        assert a["title"] == "Jak testowac"
        assert a["description"] == "krotki opis"
        assert a["body"] == "tresc"
        assert sorted(a["tagList"]) == ["a", "b"]
        assert a["slug"]
        assert a["favorited"] is False and a["favoritesCount"] == 0
        assert a["author"]["username"] == user["username"]
        assert a["createdAt"] and a["updatedAt"]

    def test_tc19b_create_without_tags(self, user):
        a = make_article(user["token"])
        assert a["tagList"] == []

    @pytest.mark.parametrize("missing", ["title", "description", "body"])
    def test_tc20_missing_required_field(self, user, missing):
        data = {"title": uniq("T"), "description": "d", "body": "b"}
        del data[missing]
        r = call("POST", "/articles", token=user["token"], json={"article": data})
        assert r.status_code == 422
        assert_error_format(r)

    def test_tc21_create_requires_auth(self):
        r = call("POST", "/articles", json={"article": {"title": "t", "description": "d", "body": "b"}})
        assert r.status_code == 401

    def test_tc22a_get_by_slug(self, article):
        r = call("GET", f"/articles/{article['slug']}")
        assert r.status_code == 200
        assert r.json()["article"]["title"] == article["title"]

    def test_tc22b_get_unknown_slug(self):
        assert call("GET", f"/articles/{uniq('nie-ma-')}").status_code == 404

    def test_tc23_same_title_twice(self, user):
        title = uniq("Powtorka ")
        a1 = make_article(user["token"], title=title)
        r = call("POST", "/articles", token=user["token"],
                 json={"article": {"title": title, "description": "d", "body": "b"}})
        # Specyfikacja nie rozstrzyga: dopuszczalne jest unikalne slug-owanie lub odrzucenie.
        assert r.status_code in (200, 201, 422)
        if r.status_code in (200, 201):
            assert r.json()["article"]["slug"] != a1["slug"]


class TestArticleUpdateDelete:
    def test_tc24a_author_updates(self, user, article):
        r = call("PUT", f"/articles/{article['slug']}", token=user["token"],
                 json={"article": {"body": "nowa tresc", "description": "nowy opis"}})
        assert r.status_code == 200
        a = r.json()["article"]
        assert a["body"] == "nowa tresc" and a["description"] == "nowy opis"
        assert a["title"] == article["title"]

    def test_tc24b_non_author_forbidden(self, other_user, article):
        r = call("PUT", f"/articles/{article['slug']}", token=other_user["token"],
                 json={"article": {"body": "hack"}})
        assert r.status_code == 403
        assert call("GET", f"/articles/{article['slug']}").json()["article"]["body"] == article["body"]

    def test_tc24c_update_requires_auth(self, article):
        assert call("PUT", f"/articles/{article['slug']}", json={"article": {"body": "x"}}).status_code == 401

    def test_tc24d_update_unknown_slug(self, user):
        r = call("PUT", f"/articles/{uniq('nie-ma-')}", token=user["token"], json={"article": {"body": "x"}})
        assert r.status_code == 404

    def test_tc25a_author_deletes(self, user, article):
        r = call("DELETE", f"/articles/{article['slug']}", token=user["token"])
        assert r.status_code in (200, 204)
        assert call("GET", f"/articles/{article['slug']}").status_code == 404

    def test_tc25b_non_author_cannot_delete(self, other_user, article):
        r = call("DELETE", f"/articles/{article['slug']}", token=other_user["token"])
        assert r.status_code == 403
        assert call("GET", f"/articles/{article['slug']}").status_code == 200

    def test_tc25c_delete_requires_auth(self, article):
        assert call("DELETE", f"/articles/{article['slug']}").status_code == 401

    def test_tc25d_delete_unknown_slug(self, user):
        assert call("DELETE", f"/articles/{uniq('nie-ma-')}", token=user["token"]).status_code == 404


class TestArticleList:
    def test_tc26a_response_shape(self, article):
        r = call("GET", "/articles")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body["articles"], list)
        assert isinstance(body["articlesCount"], int)
        assert body["articlesCount"] >= len(body["articles"])

    def test_tc26b_filter_by_author(self, user):
        a1 = make_article(user["token"])
        a2 = make_article(user["token"])
        body = call("GET", "/articles", params={"author": user["username"]}).json()
        slugs = [a["slug"] for a in body["articles"]]
        assert set(slugs) == {a1["slug"], a2["slug"]}
        assert body["articlesCount"] == 2

    def test_tc26c_filter_by_unknown_author_is_empty(self):
        body = call("GET", "/articles", params={"author": uniq("nikt")}).json()
        assert body["articles"] == [] and body["articlesCount"] == 0

    def test_tc26d_filter_by_tag(self, user):
        tag = uniq("tag")
        tagged = make_article(user["token"], tags=[tag])
        make_article(user["token"], tags=["inny"])
        body = call("GET", "/articles", params={"tag": tag}).json()
        assert [a["slug"] for a in body["articles"]] == [tagged["slug"]]

    def test_tc26e_limit(self, user):
        for _ in range(3):
            make_article(user["token"])
        body = call("GET", "/articles", params={"author": user["username"], "limit": 2}).json()
        assert len(body["articles"]) == 2
        assert body["articlesCount"] == 3

    def test_tc26f_offset(self, user):
        for _ in range(3):
            make_article(user["token"])
        full = call("GET", "/articles", params={"author": user["username"]}).json()["articles"]
        paged = call("GET", "/articles", params={"author": user["username"], "offset": 1, "limit": 10}).json()
        assert [a["slug"] for a in paged["articles"]] == [a["slug"] for a in full][1:]

    def test_tc26g_offset_beyond_total(self, user):
        make_article(user["token"])
        body = call("GET", "/articles", params={"author": user["username"], "offset": 100}).json()
        assert body["articles"] == []
        assert body["articlesCount"] == 1

    def test_tc26h_newest_first(self, user):
        first = make_article(user["token"])
        time.sleep(1.1)
        second = make_article(user["token"])
        slugs = [a["slug"] for a in call("GET", "/articles", params={"author": user["username"]}).json()["articles"]]
        assert slugs == [second["slug"], first["slug"]]

    def test_tc26i_filter_favorited(self, user, other_user):
        fav = make_article(other_user["token"])
        make_article(other_user["token"])
        call("POST", f"/articles/{fav['slug']}/favorite", token=user["token"])
        body = call("GET", "/articles", params={"favorited": user["username"]}).json()
        assert [a["slug"] for a in body["articles"]] == [fav["slug"]]

    def test_tc26j_list_item_has_no_body_requirement_but_has_core_fields(self, article):
        item = call("GET", "/articles", params={"author": article["author"]["username"]}).json()["articles"][0]
        for key in ("slug", "title", "description", "tagList", "createdAt", "updatedAt",
                    "favorited", "favoritesCount", "author"):
            assert key in item


class TestFeed:
    def test_tc27a_requires_auth(self):
        assert call("GET", "/articles/feed").status_code == 401

    def test_tc27b_empty_when_following_nobody(self, user):
        body = call("GET", "/articles/feed", token=user["token"]).json()
        assert body["articles"] == [] and body["articlesCount"] == 0

    def test_tc27c_only_followed_authors(self, user, other_user):
        third = make_user()
        mine = make_article(other_user["token"])
        make_article(third["token"])
        call("POST", f"/profiles/{other_user['username']}/follow", token=user["token"])
        body = call("GET", "/articles/feed", token=user["token"]).json()
        assert [a["slug"] for a in body["articles"]] == [mine["slug"]]

    def test_tc27d_unfollow_removes_from_feed(self, user, other_user):
        make_article(other_user["token"])
        call("POST", f"/profiles/{other_user['username']}/follow", token=user["token"])
        call("DELETE", f"/profiles/{other_user['username']}/follow", token=user["token"])
        assert call("GET", "/articles/feed", token=user["token"]).json()["articles"] == []


class TestFavorites:
    def test_tc28a_favorite(self, other_user, article):
        r = call("POST", f"/articles/{article['slug']}/favorite", token=other_user["token"])
        assert r.status_code == 200
        a = r.json()["article"]
        assert a["favorited"] is True and a["favoritesCount"] == 1

    def test_tc28b_counter_counts_distinct_users(self, user, other_user, article):
        call("POST", f"/articles/{article['slug']}/favorite", token=user["token"])
        r = call("POST", f"/articles/{article['slug']}/favorite", token=other_user["token"])
        assert r.json()["article"]["favoritesCount"] == 2

    def test_tc28c_unfavorite(self, other_user, article):
        call("POST", f"/articles/{article['slug']}/favorite", token=other_user["token"])
        r = call("DELETE", f"/articles/{article['slug']}/favorite", token=other_user["token"])
        assert r.status_code == 200
        a = r.json()["article"]
        assert a["favorited"] is False and a["favoritesCount"] == 0

    def test_tc28d_favorited_flag_is_per_viewer(self, user, other_user, article):
        call("POST", f"/articles/{article['slug']}/favorite", token=other_user["token"])
        as_other = call("GET", f"/articles/{article['slug']}", token=other_user["token"]).json()["article"]
        as_anon = call("GET", f"/articles/{article['slug']}").json()["article"]
        assert as_other["favorited"] is True
        assert as_anon["favorited"] is False
        assert as_anon["favoritesCount"] == 1

    def test_tc28e_requires_auth(self, article):
        assert call("POST", f"/articles/{article['slug']}/favorite").status_code == 401

    def test_tc28f_unknown_article(self, user):
        assert call("POST", f"/articles/{uniq('nie-ma-')}/favorite", token=user["token"]).status_code == 404


class TestComments:
    def _add(self, token, slug, body="komentarz"):
        return call("POST", f"/articles/{slug}/comments", token=token, json={"comment": {"body": body}})

    def test_tc29a_add_comment(self, other_user, article):
        r = self._add(other_user["token"], article["slug"], "swietny tekst")
        assert r.status_code in (200, 201)
        c = r.json()["comment"]
        assert c["body"] == "swietny tekst"
        assert c["author"]["username"] == other_user["username"]
        assert c["id"] is not None and c["createdAt"] and c["updatedAt"]

    def test_tc29b_missing_body(self, other_user, article):
        r = call("POST", f"/articles/{article['slug']}/comments", token=other_user["token"], json={"comment": {}})
        assert r.status_code == 422

    def test_tc29c_empty_body(self, other_user, article):
        assert self._add(other_user["token"], article["slug"], "").status_code == 422

    def test_tc29d_requires_auth(self, article):
        r = call("POST", f"/articles/{article['slug']}/comments", json={"comment": {"body": "x"}})
        assert r.status_code == 401

    def test_tc29e_unknown_article(self, user):
        assert self._add(user["token"], uniq("nie-ma-")).status_code == 404

    def test_tc30a_list_comments_public(self, other_user, article):
        self._add(other_user["token"], article["slug"], "pierwszy")
        self._add(other_user["token"], article["slug"], "drugi")
        r = call("GET", f"/articles/{article['slug']}/comments")
        assert r.status_code == 200
        bodies = [c["body"] for c in r.json()["comments"]]
        assert sorted(bodies) == ["drugi", "pierwszy"]

    def test_tc30b_list_empty(self, article):
        r = call("GET", f"/articles/{article['slug']}/comments")
        assert r.status_code == 200 and r.json()["comments"] == []

    def test_tc30c_list_unknown_article(self):
        assert call("GET", f"/articles/{uniq('nie-ma-')}/comments").status_code == 404

    def test_tc31a_author_deletes_comment(self, other_user, article):
        cid = self._add(other_user["token"], article["slug"]).json()["comment"]["id"]
        r = call("DELETE", f"/articles/{article['slug']}/comments/{cid}", token=other_user["token"])
        assert r.status_code in (200, 204)
        assert call("GET", f"/articles/{article['slug']}/comments").json()["comments"] == []

    def test_tc31b_non_author_cannot_delete(self, user, other_user, article):
        cid = self._add(other_user["token"], article["slug"]).json()["comment"]["id"]
        r = call("DELETE", f"/articles/{article['slug']}/comments/{cid}", token=user["token"])
        assert r.status_code == 403
        assert len(call("GET", f"/articles/{article['slug']}/comments").json()["comments"]) == 1

    def test_tc31c_delete_requires_auth(self, other_user, article):
        cid = self._add(other_user["token"], article["slug"]).json()["comment"]["id"]
        assert call("DELETE", f"/articles/{article['slug']}/comments/{cid}").status_code == 401

    def test_tc31d_delete_unknown_comment(self, user, article):
        r = call("DELETE", f"/articles/{article['slug']}/comments/99999999", token=user["token"])
        assert r.status_code == 404


class TestTags:
    def test_tc32a_tags_contains_used_tag(self, user):
        tag = uniq("tag")
        make_article(user["token"], tags=[tag])
        r = call("GET", "/tags")
        assert r.status_code == 200
        tags = r.json()["tags"]
        assert isinstance(tags, list) and all(isinstance(t, str) for t in tags)
        assert tag in tags

    def test_tc32b_tags_unique(self, user):
        tag = uniq("tag")
        make_article(user["token"], tags=[tag])
        make_article(user["token"], tags=[tag])
        tags = call("GET", "/tags").json()["tags"]
        assert tags.count(tag) == 1

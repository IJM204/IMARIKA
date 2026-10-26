"""
Tests du Plan A : comptes utilisateurs, isolation, reponses rapides, interface.
Aucun appel a Ollama (marker "fast") — execution en moins de 10 s.

    python -m pytest tests/test_auth.py -q
"""
import uuid

import pytest

pytestmark = pytest.mark.fast


def _cleanup(username: str) -> None:
    """Supprime le compte de test cree par le fixture (evite de polluer la base)."""
    from backend.core.database import get_connection

    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "DELETE FROM conversations WHERE user_id = (SELECT id FROM users WHERE username = ?)",
                (username,),
            )
            conn.execute(
                "DELETE FROM sessions WHERE user_id = (SELECT id FROM users WHERE username = ?)",
                (username,),
            )
            conn.execute("DELETE FROM users WHERE username = ?", (username,))
    finally:
        conn.close()


@pytest.fixture()
def userA(client):
    """Compte de test unique (supprime apres le test)."""
    name = "t_" + uuid.uuid4().hex[:8]
    r = client.post(
        "/api/v1/auth/register",
        json={"username": name, "password": "secret123", "region": "Bujumbura"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    yield data
    client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {data['token']}"})
    _cleanup(name)


@pytest.fixture()
def userB(client):
    name = "t_" + uuid.uuid4().hex[:8]
    r = client.post(
        "/api/v1/auth/register",
        json={"username": name, "password": "secret123"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    yield data
    client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {data['token']}"})
    _cleanup(name)


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------- #
#  Comptes                                                               #
# --------------------------------------------------------------------- #
def test_register_returns_token_and_profile(client, userA):
    assert userA["token"]
    assert userA["user"]["username"].startswith("t_")


def test_me_returns_profile(client, userA):
    r = client.get("/api/v1/auth/me", headers=_auth(userA["token"]))
    assert r.status_code == 200
    assert r.json()["region"] == "Bujumbura"


def test_me_requires_auth(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_duplicate_username_rejected(client):
    name = "t_" + uuid.uuid4().hex[:8]
    payload = {"username": name, "password": "secret123"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 200
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 400
    assert "pris" in r.json()["detail"]
    _cleanup(name)


def test_wrong_password_rejected(client, userA):
    r = client.post(
        "/api/v1/auth/login",
        json={"username": userA["user"]["username"], "password": "mauvais"},
    )
    assert r.status_code == 401


def test_short_password_rejected(client):
    name = "t_" + uuid.uuid4().hex[:8]
    r = client.post("/api/v1/auth/register", json={"username": name, "password": "abc"})
    assert r.status_code == 422  # schema Pydantic (min 6)


def test_logout_invalidates_token(client, userA):
    assert client.post("/api/v1/auth/logout", headers=_auth(userA["token"])).status_code == 200
    assert client.get("/api/v1/auth/me", headers=_auth(userA["token"])).status_code == 401


# --------------------------------------------------------------------- #
#  Isolation des historiques                                             #
# --------------------------------------------------------------------- #
def _greet(client, token, text="bonjour"):
    return client.post("/api/v1/chat", json={"message": text}, headers=_auth(token))


def test_greeting_is_instant_and_scoped(client, userA):
    r = _greet(client, userA["token"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert "Imarika" in body["response"]
    assert body["conversation_id"]

    h = client.get("/api/v1/history", headers=_auth(userA["token"]))
    assert h.status_code == 200
    assert any(c["id"] == body["conversation_id"] for c in h.json())


def test_users_cannot_see_each_others_history(client, userA, userB):
    conv_id = _greet(client, userA["token"]).json()["conversation_id"]

    # userB : historique vide, conversation inaccessible
    h = client.get("/api/v1/history", headers=_auth(userB["token"]))
    assert all(c["id"] != conv_id for c in h.json())

    assert client.get(f"/api/v1/history/{conv_id}", headers=_auth(userB["token"])).status_code == 404
    assert client.delete(f"/api/v1/history/{conv_id}", headers=_auth(userB["token"])).status_code == 404

    # userA garde l'acces
    assert client.get(f"/api/v1/history/{conv_id}", headers=_auth(userA["token"])).status_code == 200


def test_anonymous_cannot_see_user_history(client, userA):
    conv_id = _greet(client, userA["token"]).json()["conversation_id"]
    h = client.get("/api/v1/history")
    assert h.status_code == 200
    assert all(c["id"] != conv_id for c in h.json())


# --------------------------------------------------------------------- #
#  Reponses rapides (hors LLM)                                           #
# --------------------------------------------------------------------- #
@pytest.mark.parametrize("msg,attendu", [
    ("bonjour", "Imarika"),
    ("Salut !", "Imarika"),
    ("merci", "plaisir"),
    ("Qui es-tu ?", "Imarika"),
    ("aide", "Agriculture"),
    ("Muraho", "Muraho"),
    ("Habari", "Habari"),
])
def test_fast_replies(client, userA, msg, attendu):
    r = _greet(client, userA["token"], msg)
    assert r.status_code == 200, r.text
    assert attendu in r.json()["response"]


def test_greeting_bypasses_ollama_check(client, userA):
    """Meme si Ollama est eteint, une salutation reste repondue (200)."""
    r = _greet(client, userA["token"], "bonjour")
    assert r.status_code == 200


# --------------------------------------------------------------------- #
#  Interface web                                                         #
# --------------------------------------------------------------------- #
def test_index_page_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Imarika" in r.text and "<form" in r.text


def test_health_endpoint(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["backend_online"] is True
    assert body["model_name"]

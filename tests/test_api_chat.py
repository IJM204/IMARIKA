"""
Tests C, D, E — Chat API, Conversation SQLite, History API.

Necessitent une vraie generation (marque "ollama") :
la fixture de module n'envoie QUE DEUX messages, ce qui couvre C, D et E.

    1er message sans conversation_id  -> creation de la conversation
    2e  message avec conversation_id  -> reutilisation du meme identifiant

La conversation de test est supprimee de SQLite en fin de module.
"""

import pytest

from backend.services.history_service import history_service

pytestmark = pytest.mark.ollama

QUESTION_1 = "Comment améliorer la production du maïs au Burundi ?"
QUESTION_2 = "Quand faut-il semer le haricot au Burundi ?"


def _post_chat(client, **payload):
    """POST /api/v1/chat en conservant (status_code, payload, raw) pour les assertions."""
    try:
        response = client.post("/api/v1/chat", json={**payload, "language": "fr"})
        content_type = response.headers.get("content-type", "")
        body = response.json() if "json" in content_type else {}
        return {"status_code": response.status_code, "payload": body, "raw": response.text}
    except Exception as exc:  # pragma: no cover - transport/timeout
        return {"status_code": 0, "payload": {}, "raw": f"{type(exc).__name__}: {exc}"}


@pytest.fixture(scope="module")
def conversation(client):
    """Deux messages reels : creation puis reutilisation de la conversation."""
    first = _post_chat(client, message=QUESTION_1)
    conv_id = first["payload"].get("conversation_id")

    if conv_id:
        second = _post_chat(client, message=QUESTION_2, conversation_id=conv_id)
    else:
        second = {"status_code": 0, "payload": {}, "raw": "pas de conversation_id"}

    yield {
        "client": client,
        "first": first,
        "second": second,
        "conversation_id": conv_id,
        "second_id": second["payload"].get("conversation_id"),
    }

    # Nettoyage : aucun artefact de test ne reste dans data/imarika.db
    if conv_id:
        history_service.delete_conversation(conv_id)


# --------------------------------------------------------------------- C ----
def test_chat_api_reponse_200(conversation):
    assert conversation["first"]["status_code"] == 200, conversation["first"]["raw"]


def test_chat_api_reponse_json_valide(conversation):
    payload = conversation["first"]["payload"]
    assert payload.get("status") == "success", payload
    assert isinstance(payload.get("response"), str)
    assert payload["response"].strip(), "reponse assistant vide"
    assert payload.get("conversation_id"), "conversation_id absent"
    assert not payload.get("error")


def test_chat_api_contexte_utilise(conversation):
    payload = conversation["first"]["payload"]
    context = payload.get("context_used")
    assert context is None or isinstance(context, list)
    if context:
        assert all(isinstance(chunk, str) and chunk.strip() for chunk in context)


# --------------------------------------------------------------------- D ----
def test_premier_message_cree_une_conversation(conversation):
    """D1 — le 1er message cree une conversation visible dans l'historique."""
    assert conversation["conversation_id"], "aucune conversation creee par le 1er message"
    listed = conversation["client"].get("/api/v1/history").json()
    ids = [entry["id"] for entry in listed]
    assert conversation["conversation_id"] in ids


def test_deuxieme_message_reutilise_le_conversation_id(conversation):
    """D2 — le 2e message appartient a la MEME conversation."""
    assert conversation["second"]["status_code"] == 200, conversation["second"]["raw"]
    assert conversation["second_id"] == conversation["conversation_id"], (
        "le 2e message a cree une NOUVELLE conversation au lieu de reutiliser l'identifiant"
    )


# --------------------------------------------------------------------- E ----
def test_sqlite_messages_enregistres(conversation):
    """E/SQLite : 2 questions + 2 reponses reellement ecrites en base."""
    conv = history_service.get_conversation_messages(conversation["conversation_id"])
    assert conv, "conversation introuvable en SQLite"

    messages = conv["messages"]
    assert len(messages) == 4, (
        f"4 messages attendus (2 user + 2 assistant), {len(messages)} trouves"
    )

    senders = [message["sender"] for message in messages]
    assert senders == ["user", "assistant", "user", "assistant"], senders
    assert all(message["content"].strip() for message in messages)
    assert messages[0]["content"] == QUESTION_1
    assert messages[2]["content"] == QUESTION_2


def test_history_api_liste(conversation):
    """E/History API — GET /api/v1/history retrouve la conversation creee."""
    response = conversation["client"].get("/api/v1/history")
    assert response.status_code == 200, response.text

    entry = next(
        (c for c in response.json() if c["id"] == conversation["conversation_id"]),
        None,
    )
    assert entry, "conversation absente de GET /api/v1/history"
    assert entry["message_count"] == 4, entry
    assert entry["title"].strip()
    assert entry["created_at"] and entry["updated_at"]


def test_history_api_detail(conversation):
    """E/History API — GET /api/v1/history/{id} retourne les 4 messages."""
    conv_id = conversation["conversation_id"]
    response = conversation["client"].get(f"/api/v1/history/{conv_id}")
    assert response.status_code == 200, response.text

    payload = response.json()
    assert payload["id"] == conv_id
    assert len(payload["messages"]) == 4
    assert payload["messages"][0]["sender"] == "user"
    assert payload["messages"][1]["sender"] == "assistant"
    assert payload["messages"][1]["content"].strip()


def test_history_api_conversation_inconnue_404(conversation):
    """Lecture d'une conversation inexistante : 404 propre, pas d'erreur 500."""
    response = conversation["client"].get("/api/v1/history/conversation-inexistante")
    assert response.status_code == 404, response.text

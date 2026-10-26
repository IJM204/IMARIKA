"""
Tests F — Streaming SSE : POST /api/v1/chat/stream.

Generation reelle (marque "ollama") : Qwen3 en CPU peut etre lent,
aucune duree maximale n'est imposee.

Verifie : HTTP 200, content-type SSE, evenement start, tokens,
evenement final done, absence d'erreur, sauvegarde SQLite de la reponse.
"""

import json

import pytest

from backend.services.history_service import history_service

pytestmark = pytest.mark.ollama

QUESTION = "Comment fertiliser le maïs au Burundi ?"


@pytest.fixture(scope="module")
def stream(client):
    """Consomme un flux SSE complet et retourne les evenements + identifiants."""
    events = []
    content_type = ""
    status_code = 0
    exception = None

    try:
        with client.stream(
            "POST",
            "/api/v1/chat/stream",
            json={"message": QUESTION, "language": "fr"},
        ) as response:
            status_code = response.status_code
            content_type = response.headers.get("content-type", "")
            for line in response.iter_lines():
                line = line.strip()
                if not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if not raw:
                    continue
                try:
                    events.append(json.loads(raw))
                except json.JSONDecodeError as exc:  # evenement SSE mal forme
                    exception = exc
    except Exception as exc:  # pragma: no cover - transport/timeout
        exception = exc

    data = {"events": events, "content_type": content_type,
            "status_code": status_code, "exception": exception,
            "conversation_id": None}
    for event in events:
        if event.get("event") == "done":
            data["conversation_id"] = event.get("conversation_id")

    yield data

    if data["conversation_id"]:
        history_service.delete_conversation(data["conversation_id"])


def test_streaming_http_200_et_content_type_sse(stream):
    assert stream["exception"] is None, stream["exception"]
    assert stream["status_code"] == 200, stream
    assert "text/event-stream" in stream["content_type"], stream["content_type"]


def test_streaming_evenement_demarrage(stream):
    events = stream["events"]
    assert events, "aucun evenement SSE recu"
    assert events[0]["event"] == "start", events[0]
    assert events[0].get("conversation_id"), "conversation_id absent de l'evenement start"


def test_streaming_tokens_recus(stream):
    tokens = [e for e in stream["events"] if e.get("event") == "token"]
    assert tokens, "aucun token recu dans le flux"
    content = "".join(e.get("token", "") for e in tokens)
    assert len(content.strip()) > 10, f"reponse streamee trop courte : {content!r}"


def test_streaming_evenement_final_done(stream):
    events = stream["events"]
    kinds = [e.get("event") for e in events]
    assert kinds[-1] == "done", kinds
    assert "error" not in kinds, [e for e in events if e.get("event") == "error"]
    assert events[-1].get("conversation_id")


def test_streaming_reponse_sauvegardee_sqlite(stream):
    conv_id = stream["conversation_id"]
    assert conv_id, "aucune conversation enregistree"
    conv = history_service.get_conversation_messages(conv_id)
    assert conv, "conversation absente de SQLite apres streaming"

    messages = conv["messages"]
    assert len(messages) == 2, f"user + assistant attendus, {len(messages)} trouves"
    assert messages[0]["sender"] == "user"
    assert messages[0]["content"] == QUESTION
    assert messages[1]["sender"] == "assistant"
    assert messages[1]["content"].strip(), "reponse assistant vide en SQLite"

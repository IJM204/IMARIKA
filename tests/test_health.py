"""
Tests A — Sante du systeme (rapides, aucune generation Ollama).

GET /health      : route racine (monitoring / frontend)
GET /api/v1/health : route versionnee (consommee par React)
"""

import pytest

from backend.core.config import settings

pytestmark = pytest.mark.fast


def test_health_racine_repond_200(client):
    response = client.get("/health")
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["backend_online"] is True
    assert data["ollama_online"] in (True, False)
    assert data["model_available"] in (True, False)
    assert isinstance(data["model_name"], str) and data["model_name"]
    assert data["status"] in ("healthy", "degraded")


def test_health_api_v1_repond_200(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["backend_online"] is True
    assert data["status"] in ("healthy", "degraded")


def test_health_identique_sur_les_deux_routes(client):
    root = client.get("/health").json()
    v1 = client.get("/api/v1/health").json()
    assert root["status"] == v1["status"]
    assert root["model_name"] == v1["model_name"]


def test_health_ollama_et_modele_disponibles(client, ollama_online):
    """Quand Ollama tourne, le statut doit etre healthy et le modele present."""
    if not ollama_online:
        pytest.skip("Ollama non disponible : sante 'degraded' attendue, test non applicable")

    data = client.get("/api/v1/health").json()
    assert data["ollama_online"] is True, data
    assert data["model_available"] is True, data
    assert data["status"] == "healthy", data
    assert data["error"] is None, data


def test_configuration_modele_qwen3_sans_llama3():
    """Le MVP doit pointer vers qwen3:1.7b — jamais llama3 (aucun autre modele)."""
    assert settings.OLLAMA_MODEL == "qwen3:1.7b"
    assert "llama3" not in settings.OLLAMA_MODEL.lower()

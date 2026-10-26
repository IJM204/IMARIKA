"""
PHASE 3 — Test d'integration Ollama (modele deja installe : qwen3:1.7b).

Marques "ollama" : ces tests sont plus lents (generation reelle sur CPU) et
sont sautes automatiquement si repond sur localhost:11434.

Aucun modele n'est telecharge : on utilise exclusivement qwen3:1.7b.
"""

import httpx
import pytest

from backend.core.config import settings

OLLAMA_URL = settings.OLLAMA_BASE_URL
MODEL = "qwen3:1.7b"


def _models():
    response = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=10.0)
    response.raise_for_status()
    return [model["name"] for model in response.json().get("models", [])]


@pytest.mark.ollama
def test_ollama_repond_sur_localhost():
    """1 — Ollama est accessible sur localhost:11434."""
    response = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=10.0)
    assert response.status_code == 200
    assert "models" in response.json()


@pytest.mark.ollama
def test_modele_qwen3_1_7b_present():
    """2 — Le modele qwen3:1.7b est present dans Ollama (sans rien telecharger)."""
    names = _models()
    assert any(name == MODEL or name.startswith(f"{MODEL}:") for name in names), (
        f"{MODEL} absent, modeles disponibles : {names}"
    )


@pytest.mark.ollama
def test_generation_reelle_avec_qwen3():
    """
    3 — Une generation reelle fonctionne (prompt court, budget de tokens reduit).

    qwen3 produit des tokens de reflexion ("thinking") avant la reponse :
    on les desactive ici pour que le budget couvre la reponse visible.
    """
    response = httpx.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": MODEL,
            "prompt": "Cite deux activites agricoles courantes au Burundi, en une phrase.",
            "stream": False,
            "think": False,
            "options": {"num_predict": 64, "temperature": 0.3},
        },
        timeout=300.0,
    )
    assert response.status_code == 200, response.text

    body = response.json()
    text = (body.get("response") or "").strip()
    assert text, "generation vide"
    assert body.get("model") == MODEL
    assert body.get("done") is True

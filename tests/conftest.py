"""
Configuration pytest — AGRIBurundi-AI / Imarika (MVP).

Strategie :
  * tests rapides (defaut) : aucun appel a Ollama (sante, knowledge, config).
  * tests "ollama" : generation reelle avec le modele installe qwen3:1.7b.
    Ils sont sautes proprement si Ollama n'est pas joignable.
  * tests "legacy" : ancienne architecture, exclus par pytest.ini (addopts).

Execution :
    python -m pytest                    # tout sauf legacy
    python -m pytest -m fast            # uniquement les tests rapides
    python -m pytest -m "ollama"        # uniquement l integration Ollama
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import httpx
import pytest
from fastapi.testclient import TestClient

# Modules legacy : ils importent l'ancienne architecture (LangGraph / llama3)
# et ne doivent pas etre executes par la suite du MVP actuel.
collect_ignore = [
    "unit/simple_test.py",            # subprocess "ollama run llama3"
    "integration/test_enhanced.py",   # core.langgraph_imarika (llama3)
    "integration/evaluate_system.py", # meme architecture legacy
]

OLLAMA_URL = "http://localhost:11434"


def ollama_reachable() -> bool:
    """Verifie rapidement que repond sur localhost:11434."""
    try:
        return httpx.get(f"{OLLAMA_URL}/api/tags", timeout=3.0).status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def ollama_online() -> bool:
    """Vrai si Ollama repond (partage par les tests qui en ont besoin)."""
    return ollama_reachable()


@pytest.fixture(scope="session")
def client():
    """
    Client de test FastAPI en process (TestClient).
    Lance le lifespan (init_db SQLite) et attend les reponses longues :
    Qwen3 genere sur CPU (~1,4 token/s), d ou un timeout large.
    """
    from backend.main import app

    with TestClient(app) as test_client:
        # Timeout large (Qwen3 genere sur CPU, ~1,4 token/s) : le TestClient
        # n'accepte pas timeout= dans son constructeur, on l'applique apres.
        test_client.timeout = httpx.Timeout(600.0, connect=10.0)
        yield test_client


def pytest_collection_modifyitems(items):
    """Sans Ollama, on saute (skip) au lieu d'echouer les tests d integration."""
    if ollama_reachable():
        return
    skip_marker = pytest.mark.skip(
        reason="Ollama indisponible sur localhost:11434 — test d integration saute"
    )
    for item in items:
        if "ollama" in item.keywords:
            item.add_marker(skip_marker)

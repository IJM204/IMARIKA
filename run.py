#!/usr/bin/env python3
"""
Imarika / AGRIBurundi-AI - Lanceur principal.
Usage: python run.py [mode]

Modes:
  api     - Backend FastAPI + interface web legere (DEFAUT)
  legacy  - Ancienne interface Streamlit (LOURD: charge matplotlib,
            networkx et anciens modeles -> risque de plantage sur 8 Go RAM)
  test    - Tests systeme
  build-kg- Reconstruit le graphe de connaissances
  help    - Affiche cette aide
"""

import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def run_api():
    """Lance l'API FastAPI avec l'interface web statique (chemin leger)."""
    import uvicorn
    from backend.core.config import settings

    print("Imarika - demarrage du serveur (mode leger)")
    print(f"  Interface : http://localhost:{settings.PORT}")
    print(f"  API docs  : http://localhost:{settings.PORT}/docs")
    print(f"  Modele    : {settings.OLLAMA_MODEL} (Ollama: {settings.OLLAMA_BASE_URL})")
    print("  Appuyez sur Ctrl+C pour arreter.")
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level="info",
    )


def run_legacy():
    """Ancienne interface Streamlit (lourde)."""
    print("Imarika - ancienne interface Streamlit (mode LOURD)")
    print("  Si la machine ralentit, utilisez: python run.py")
    subprocess.run([
        "streamlit", "run", "core/streamlit_chatgpt_style.py",
        "--server.port", "8501",
        "--server.headless", "true",
        "--server.runOnSave", "true",
    ])


def run_test():
    """Lance les tests Python (pytest)."""
    print("Imarika - tests...")
    subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"])


def build_knowledge_graph():
    """Reconstruit le graphe de connaissances depuis les CSV."""
    print("Imarika - reconstruction du graphe de connaissances...")
    subprocess.run([sys.executable, "-m", "core.knowledge_graph"])


def show_help():
    print("""
Imarika / AGRIBurundi-AI

Usage: python run.py [mode]

Modes:
  api      - Backend FastAPI + interface web legere (DEFAUT)
  legacy   - Ancienne interface Streamlit (lourd)
  test     - Tests pytest
  build-kg - Reconstruit le graphe de connaissances
  help     - Cette aide

Exemples:
  python run.py          # interface web sur http://localhost:8000
  python run.py legacy   # ancien Streamlit sur http://localhost:8501
    """)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "api"

    if mode in ("api", "chat"):
        run_api()
    elif mode == "legacy":
        run_legacy()
    elif mode == "test":
        run_test()
    elif mode == "build-kg":
        build_knowledge_graph()
    elif mode in ("help", "-h", "--help"):
        show_help()
    else:
        print(f"Mode inconnu: {mode}")
        show_help()
        sys.exit(1)

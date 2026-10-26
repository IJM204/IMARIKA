"""
Script manuel de verification du service Ollama (MVP, non collecte par pytest).

Meme couverture que tests/test_ollama_integration.py ; conserve pour un
controle rapide en ligne de commande :  python test_ollama_quick.py
"""

import asyncio, sys
sys.path.insert(0, "D:/AGRIBurundi-AI")
from backend.services.ollama_service import ollama_service

async def main():
    print("=== Test Ollama Service ===")
    
    # Test 1: availability
    ok = await ollama_service.is_ollama_available()
    assert ok, "FAIL: Ollama non disponible"
    print(f"[PASS] Ollama disponible: {ok}")
    
    # Test 2: model
    m_ok = await ollama_service.is_model_available()
    assert m_ok, "FAIL: Modele qwen3:1.7b non disponible"
    print(f"[PASS] Modele disponible: {m_ok}")
    
    # Test 3: health
    h = await ollama_service.get_health_status()
    assert h["ollama_online"], "FAIL: ollama_online=False"
    assert h["model_available"], "FAIL: model_available=False"
    print(f"[PASS] Health: {h}")
    
    print("\n[PASS] Tous les tests de base Ollama Service sont OK")

asyncio.run(main())

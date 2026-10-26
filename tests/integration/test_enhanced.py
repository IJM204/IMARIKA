#!/usr/bin/env python3
"""
[LEGACY] Test de l'ancienne architecture LangGraph/Llama3 — obsolète pour le MVP.

Classifie "legacy" : appelle core.langgraph_imarika (chaine Streamlit/LangGraph +
"llama3"), alors que le MVP utilise FastAPI + qwen3:1.7b sans LangGraph.
Exclu de la collecte pytest (tests/conftest.py : collect_ignore).

Le test E2E du MVP : tests/test_api_chat.py + tests/test_streaming.py.
"""

__test__ = False  # ce module n'est pas une suite de tests du MVP

from core.langgraph_imarika import run_imarika_agent

def test_enhanced_system():
    """Test the enhanced agricultural system"""
    
    test_queries = [
        "What nutrients does maize need?",
        "How do I manage pests in beans?", 
        "What weather is good for cassava?"
    ]
    
    print("🧠 Testing Enhanced Imarika System")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 30)
        
        try:
            response = run_imarika_agent(query)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")
        
        print()

if __name__ == "__main__":
    test_enhanced_system()
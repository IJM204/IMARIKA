"""
[LEGACY] Script de demonstration de l'ancienne API — obsolète pour le MVP.

Classifie "legacy" (marqueur pytest) : il est exclu par defaut via pytest.ini
(addopts = -m "not legacy") car il cible l'ancien contrat /api/chat avec un
champ "location" qui n'existe plus dans le schema actuel, et il exige un
serveur deja lance sans assertion verifiable.

Le suite du MVP utilise : tests/test_api_chat.py (POST /api/v1/chat).
Execution manuelle conservee : python tests/test_api.py
"""

import requests
import json

import pytest

pytestmark = pytest.mark.legacy

def test_health():
    response = requests.get("http://localhost:8000/health")
    print(f"Health Check: {response.status_code}")
    print(response.json())

def test_chat():
    url = "http://localhost:8000/api/chat"
    payload = {
        "message": "What nutrients does maize need?",
        "location": "Nairobi"
    }
    headers = {"Content-Type": "application/json"}
    
    print("\nSending chat message: 'What nutrients does maize need?'")
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=30)
        print(f"Chat Response Status: {response.status_code}")
        print(f"Bot Response: {response.json().get('response')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Note: Backend must be running for these tests to pass
    print("Testing Imarika API...")
    try:
        test_health()
        test_chat()
    except Exception as e:
        print(f"Connection failed: {e}. Is the server running on port 8000?")

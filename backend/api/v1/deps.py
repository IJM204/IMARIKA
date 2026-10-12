"""Dependances FastAPI : recuperation de l'utilisateur connecte (optionnelle)."""
from typing import Optional

from fastapi import HTTPException, Request

from backend.services import auth_service


def extract_token(request: Request) -> Optional[str]:
    """Lit le jeton dans le header Authorization (Bearer) ou la query string."""
    auth_header = request.headers.get("Authorization") or ""
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        if token:
            return token
    # Repli query string (utile si un client ne sait pas poser de header)
    return request.query_params.get("token")


def get_current_user(request: Request) -> Optional[dict]:
    """Profil utilisateur si connecte, sinon None (mode anonyme conserve
    pour la compatibilite avec les tests et l'ancien frontend React)."""
    return auth_service.get_user_by_token(extract_token(request))


def require_user(request: Request) -> dict:
    """Utilisateur OBLIGATOIRE (401 sinon)."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentification requise. Connectez-vous avec votre identifiant et mot de passe.",
        )
    return user

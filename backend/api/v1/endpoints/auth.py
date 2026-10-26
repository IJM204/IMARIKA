"""Endpoints d'authentification : inscription, connexion, profil, deconnexion."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.api.v1.deps import extract_token, get_current_user, require_user
from backend.schemas.auth import (
    AuthResponse,
    LoginRequest,
    ProfileUpdate,
    RegisterRequest,
    UserProfile,
)
from backend.services import auth_service
from backend.services.auth_service import AuthError

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=AuthResponse, summary="Creer un compte")
async def register(payload: RegisterRequest):
    try:
        user = auth_service.create_user(
            username=payload.username,
            password=payload.password,
            display_name=payload.display_name,
            phone=payload.phone,
            region=payload.region,
            crops=payload.crops,
            language=payload.language,
        )
    except AuthError as e:
        raise HTTPException(status_code=400, detail=str(e))

    session = auth_service.create_session(user["id"])
    return AuthResponse(token=session["token"], user=UserProfile(**user))


import time
from collections import defaultdict

# Suivi des tentatives de connexion pour protection anti-bruteforce (IP -> [timestamps])
_LOGIN_ATTEMPTS = defaultdict(list)

def _check_login_rate_limit(client_ip: str, max_attempts: int = 10, window_seconds: int = 60):
    now = time.time()
    valid_attempts = [t for t in _LOGIN_ATTEMPTS[client_ip] if now - t < window_seconds]
    _LOGIN_ATTEMPTS[client_ip] = valid_attempts
    if len(valid_attempts) >= max_attempts:
        raise HTTPException(
            status_code=429,
            detail="Trop de tentatives infructueuses de connexion. Veuillez patienter une minute.",
        )


@router.post("/login", response_model=AuthResponse, summary="Se connecter")
async def login(payload: LoginRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    _check_login_rate_limit(client_ip)

    try:
        user = auth_service.authenticate(payload.username, payload.password)
    except AuthError as e:
        _LOGIN_ATTEMPTS[client_ip].append(time.time())
        raise HTTPException(status_code=401, detail=str(e))

    # Réinitialisation après connexion réussie
    if client_ip in _LOGIN_ATTEMPTS:
        _LOGIN_ATTEMPTS[client_ip] = []

    session = auth_service.create_session(user["id"])
    return AuthResponse(token=session["token"], user=UserProfile(**user))


@router.get("/me", response_model=UserProfile, summary="Profil courant")
async def me(user: Optional[dict] = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Non connecte.")
    return UserProfile(**user)


@router.patch("/me", response_model=UserProfile, summary="Mettre a jour le profil")
async def update_me(payload: ProfileUpdate, user: dict = Depends(require_user)):
    updated = auth_service.update_profile(user["id"], **payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=400, detail="Aucun champ a mettre a jour.")
    return UserProfile(**updated)


@router.post("/logout", summary="Se deconnecter")
async def logout(request: Request, user: dict = Depends(require_user)):
    """Invalide le jeton de session courant."""
    token = extract_token(request)
    auth_service.delete_session(token)
    return {"status": "success", "message": "Deconnexion reussie."}

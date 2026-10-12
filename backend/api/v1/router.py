"""Routeur principal API v1 regroupant tous les endpoints."""
from fastapi import APIRouter
from backend.api.v1.endpoints.health import router as health_router
from backend.api.v1.endpoints.chat import router as chat_router
from backend.api.v1.endpoints.history import router as history_router
from backend.api.v1.endpoints.auth import router as auth_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(history_router)
api_v1_router.include_router(auth_router)

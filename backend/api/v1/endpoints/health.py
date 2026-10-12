"""Endpoint GET /health — verifie backend + Ollama + modele."""
from fastapi import APIRouter
from backend.schemas.health import HealthResponse
from backend.services.ollama_service import ollama_service
from datetime import datetime, timezone

router = APIRouter()

@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Verification complete de l'etat du systeme.
    Retourne le statut reel du backend, d'Ollama et du modele.
    """
    status = await ollama_service.get_health_status()
    all_ok = status["ollama_online"] and status["model_available"]
    return HealthResponse(
        status="healthy" if all_ok else "degraded",
        backend_online=True,
        ollama_online=status["ollama_online"],
        model_available=status["model_available"],
        model_name=status["model_name"],
        error=None if all_ok else "Ollama ou le modele est indisponible",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

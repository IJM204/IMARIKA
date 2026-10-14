"""Endpoints météo et calendrier agricole (Open-Meteo, sans clé)."""
from typing import Optional

from fastapi import APIRouter, Depends

from backend.api.v1.deps import get_current_user
from backend.services.weather_service import weather_service, PROVINCES

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("", summary="Météo + calendrier agricole par province")
async def get_weather(
    province: Optional[str] = None,
    user: Optional[dict] = Depends(get_current_user),
):
    """
    Météo actuelle + 5 jours + conseils saisonniers pour une province.
    Fallback : Gitega si la province est inconnue.
    """
    # Utilise la province du profil si non specifiee
    if not province and user and user.get("region"):
        province = user["region"]
    return await weather_service.get_forecast(province)


@router.get("/provinces", summary="Liste des provinces supportées")
async def list_provinces():
    return {"provinces": list(PROVINCES.keys())}

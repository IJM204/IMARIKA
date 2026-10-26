"""Endpoints météo et calendrier agricole (Open-Meteo, sans clé)."""
from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.api.v1.deps import get_current_user
from backend.services.weather_service import weather_service, PROVINCES, LOCATIONS

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("", summary="Météo + calendrier agricole par ville ou province")
async def get_weather(
    location: Optional[str] = Query(None, description="Nom de la ville, province ou commune"),
    province: Optional[str] = Query(None, description="Alias rétrocompatible pour location"),
    user: Optional[dict] = Depends(get_current_user),
):
    """
    Météo actuelle + 5 jours + conseils saisonniers pour n'importe quelle ville ou province.
    Supporte les 18 provinces du Burundi, les villes/communes et les villes régionales.
    Géocodage dynamique pour toute autre localité.
    Fallback : Gitega si la localisation est inconnue.
    """
    target = location or province
    if not target and user and user.get("region"):
        target = user["region"]
    return await weather_service.get_forecast(target)


@router.get("/provinces", summary="Liste des provinces historiques du Burundi")
async def list_provinces():
    return {"provinces": list(PROVINCES.keys())}


@router.get("/locations", summary="Liste complète des villes et provinces pré-enregistrées")
async def list_locations():
    """Retourne les localités classées par catégories pour faciliter la sélection dans l'UI."""
    burundi_provinces = [k for k, v in LOCATIONS.items() if v[3] == "Burundi" and not k.startswith("Buhumuza") and not k.startswith("Burunga") and not k.startswith("Butanyerera") and k != "Bujumbura" and not "(" in v[2]]
    burundi_communes = [v[2] for k, v in LOCATIONS.items() if v[3] == "Burundi" and "(" in v[2]]
    new_provinces = ["Buhumuza", "Burunga", "Butanyerera", "Gitega", "Bujumbura"]
    regional = [v[2] for k, v in LOCATIONS.items() if v[3] != "Burundi"]

    return {
        "burundi_provinces": burundi_provinces,
        "new_provinces": new_provinces,
        "burundi_communes": burundi_communes,
        "regional_cities": regional,
        "all_keys": list(LOCATIONS.keys()),
    }


"""
Tests du service météo multi-villes et multi-provinces.
Vérifie le géocodage, les prévisions Open-Meteo et l'interception dans le chat.
"""

import pytest
from backend.services.weather_service import weather_service, LOCATIONS, PROVINCES
from backend.services.chat_service import chat_service


@pytest.mark.asyncio
async def test_resolve_known_burundi_province():
    lat, lon, disp_name, country, fallback = await weather_service.resolve_location("Ngozi")
    assert -2.95 < lat < -2.85
    assert 29.75 < lon < 29.90
    assert "Ngozi" in disp_name
    assert country == "Burundi"
    assert fallback is False


@pytest.mark.asyncio
async def test_resolve_commune_burundi():
    lat, lon, disp_name, country, fallback = await weather_service.resolve_location("Nyanza-Lac")
    assert "Nyanza-Lac" in disp_name
    assert country == "Burundi"
    assert fallback is False


@pytest.mark.asyncio
async def test_resolve_regional_city():
    lat, lon, disp_name, country, fallback = await weather_service.resolve_location("Kigali")
    assert "Kigali" in disp_name
    assert country == "Rwanda"
    assert fallback is False


@pytest.mark.asyncio
async def test_detect_weather_query_in_chat():
    assert chat_service._detect_weather_query("météo à Ngozi") == "ngozi"
    assert chat_service._detect_weather_query("quel temps fait-il à Kigali ?") == "kigali"
    assert chat_service._detect_weather_query("temps à Rumonge") == "rumonge"
    assert chat_service._detect_weather_query("pluie à Nyanza-Lac") == "nyanza-lac"
    assert chat_service._detect_weather_query("météo") == "Gitega"
    assert chat_service._detect_weather_query("comment fertiliser le haricot ?") is None


def test_weather_endpoint_api(client):
    r = client.get("/api/v1/weather?location=Gitega")
    assert r.status_code == 200
    data = r.json()
    assert "province" in data
    assert "current" in data
    assert "daily" in data


def test_weather_locations_endpoint(client):
    r = client.get("/api/v1/weather/locations")
    assert r.status_code == 200
    data = r.json()
    assert "burundi_provinces" in data
    assert "burundi_communes" in data
    assert "regional_cities" in data
    assert len(data["burundi_provinces"]) >= 15

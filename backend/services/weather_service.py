"""
Service météo et calendrier agricole pour Imarika.

Source : API Open-Meteo (gratuite, sans clé) — forecast + climview saisonnier.
Les 18 provinces du Burundi sont pre-geolocalisees ci-dessous.

Saisons agricoles burundaises (source : ai/knowledge/burundi_agri_context.py) :
  - Saison A (Impeshi)     : sept. -> janv. — semis principaux
  - Saison B (Urugaryi)    : fevr. -> juin  — pluies, humidite, maladies
  - Saison C (Ici)         : juin -> sept.  — contre-saison dans les marais
"""
import httpx
from datetime import date
from typing import Dict, Any, Optional, List

# ------------------------------------------------------------ #
#  Provinces du Burundi : -> (latitude, longitude)              #
# ------------------------------------------------------------ #
PROVINCES: Dict[str, tuple] = {
    "Bujumbura Mairie": (-3.38, 29.36),
    "Bujumbura Rural": (-3.47, 29.53),
    "Bubanza": (-3.08, 29.40),
    "Cibitoke": (-2.90, 29.37),
    "Kayanza": (-2.92, 29.61),
    "Ngozi": (-2.91, 29.83),
    "Karuzi": (-3.11, 29.91),
    "Muramvya": (-3.26, 29.63),
    "Mwaro": (-3.51, 29.72),
    "Gitega": (-3.43, 29.93),
    "Rutana": (-3.90, 29.99),
    "Makamba": (-4.13, 29.81),
    "Bururi": (-3.94, 29.62),
    "Rumonge": (-3.97, 29.45),
    "Muyinga": (-2.84, 30.34),
    "Kirundo": (-2.58, 30.09),
    "Cankuzo": (-3.17, 30.55),
    "Ruyigi": (-3.48, 30.25),
}

# Codes WMO -> emoji + libelle court (subset metier)
WMO: Dict[int, tuple] = {
    0: ("☀️", "Ciel dégagé"),
    1: ("🌤️", "Peu nuageux"),
    2: ("⛅", "Partiellement nuageux"),
    3: ("☁️", "Couvert"),
    45: ("🌫️", "Brouillard"),
    48: ("🌫️", "Brouillard givrant"),
    51: ("🌦️", "Bruine légère"),
    53: ("🌦️", "Bruine"),
    55: ("🌧️", "Bruine dense"),
    61: ("🌧️", "Pluie faible"),
    63: ("🌧️", "Pluie"),
    65: ("🌧️", "Pluie forte"),
    66: ("🌧️", "Pluie verglaçante"),
    71: ("🌨️", "Neige faible"),
    80: ("🌦️", "Averses faibles"),
    81: ("🌦️", "Averses"),
    82: ("⛈️", "Averses violentes"),
    95: ("⛈️", "Orage"),
    96: ("⛈️", "Orage et grêle"),
    99: ("⛈️", "Orage violent et grêle"),
}

def _wmo(code: int):
    return WMO.get(code, ("❓", "Temps inconnu"))

# ------------------------------------------------------------ #
#  Calendrier saisonnier                                        #
# ------------------------------------------------------------ #
def _season_for(month: int) -> dict:
    """Mois 1..12 -> activite saisonniere conseillee."""
    if month in (9, 10, 11) or month == 12:
        season = {
            "name": "Saison A (Impeshi)",
            "window": "septembre à janvier",
            "tasks": [
                "Préparez le terrain et semez les cultures principales (maïs, haricot, sorgho).",
                "Apportez FOMI Imbura ou fumier composté au semis.",
                "Désherbez tôt : la première pulling des mauvaises herbes est décisive.",
            ],
        }
        if month == 12:
            season["tasks"].append(
                "Continuez l'entretien : arrosage si le déficit pluviométrique s'installe."
            )
        return season
    if month in (1, 2, 3, 4, 5):
        season = {
            "name": "Saison B (Urugaryi)",
            "window": "février à juin",
            "tasks": [
                "Cultures de deuxième saison : patate douce, manioc, maraîchage.",
                "Surveillez les maladies = humidité élevée ( mildiou, pourridié).",
                "Récoltez le maïs selon la maturité des grains.",
            ],
        }
        if month in (5,):
            season["tasks"].append("Récoltez les premières cultures de saison B.")
        return season
    return {
        "name": "Saison C (Ici)",
        "window": "juin à septembre",
        "tasks": [
            "Contre-saison dans les marais drainés : Maraîchage intensif.",
            "Stockage et conservation des récoltes de saison B.",
            "Préparez le fumier et la litière pour la saison A.",
        ],
    }


class WeatherService:
    """Meteo reelle (Open-Meteo) + calendrier saisonnier par province."""

    def normalize_province(self, name: Optional[str]) -> str:
        """Retourne une province connue (fallback Gitega)."""
        if not name:
            return "Gitega"
        n = name.strip().lower()
        for p in PROVINCES:
            # match de prefixe tolerant : "gitega" == "Gitega",
            # "bujumbura" -> premiere entree Bujumbura
            if n == p.lower() or n.startswith(p.split()[0].lower()):
                return p
        return "Gitega"

    def _season_today(self) -> dict:
        return _season_for(date.today().month)

    async def get_forecast(self, province: Optional[str] = None) -> Dict[str, Any]:
        """Meteo actuelle + 5 jours + calendrier saisonnier, par province."""
        prov = self.normalize_province(province)
        lat, lon = PROVINCES[prov]
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,precipitation,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
            "timezone": "Africa/Bujumbura",
            "forecast_days": 5,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(url, params=params)
                r.raise_for_status()
                data = r.json()
        except Exception:
            return {
                "province": prov,
                "available": False,
                "error": "Service météo indisponible pour le moment.",
                "today_season": self._season_today(),
            }

        cur = data.get("current", {})
        d = data.get("daily", {})
        times: List[str] = d.get("time", [])

        daily = []
        for i, day in enumerate(times):
            code = int(d.get("weather_code", [0] * len(times))[i])
            emoji, label = _wmo(code)
            daily.append({
                "date": day,
                "t_max": d.get("temperature_2m_max", [None] * len(times))[i],
                "t_min": d.get("temperature_2m_min", [None] * len(times))[i],
                "rain_mm": d.get("precipitation_sum", [None] * len(times))[i],
                "emoji": emoji,
                "label": label,
            })

        code_now = int(cur.get("weather_code", 0))
        emoji_now, label_now = _wmo(code_now)
        season = self._season_today()
        total_rain = sum(
            x for x in d.get("precipitation_sum", []) if isinstance(x, (int, float))
        )

        # Conseil derive : pluie prevue + periode de semis ?
        advice = ""
        if total_rain >= 15:
            advice = "Bon cumul de pluie prévu : profitez-en pour semer ou transplanter."
        elif total_rain <= 2:
            advice = "Peu de pluie prévue : prévenez le stress hydrique (paillage, arrosage)."

        return {
            "province": prov,
            "available": True,
            "current": {
                "temperature": cur.get("temperature_2m"),
                "precipitation": cur.get("precipitation"),
                "emoji": emoji_now,
                "label": label_now,
            },
            "daily": daily,
            "rain_5d_mm": round(total_rain, 1),
            "advice": advice,
            "today_season": season,
        }


weather_service = WeatherService()

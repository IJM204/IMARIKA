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
from typing import Dict, Any, Optional, List, Tuple

# ------------------------------------------------------------ #
#  Provinces et villes prédéfinies : (latitude, longitude, nom affiché, pays)
# ------------------------------------------------------------ #
LOCATIONS: Dict[str, tuple] = {
    # --- 18 Provinces historiques du Burundi ---
    "Bujumbura Mairie": (-3.38, 29.36, "Bujumbura Mairie", "Burundi"),
    "Bujumbura Rural": (-3.47, 29.53, "Bujumbura Rural", "Burundi"),
    "Bujumbura": (-3.38, 29.36, "Bujumbura", "Burundi"),
    "Bubanza": (-3.08, 29.40, "Bubanza", "Burundi"),
    "Cibitoke": (-2.90, 29.37, "Cibitoke", "Burundi"),
    "Kayanza": (-2.92, 29.61, "Kayanza", "Burundi"),
    "Ngozi": (-2.91, 29.83, "Ngozi", "Burundi"),
    "Karuzi": (-3.11, 29.91, "Karuzi", "Burundi"),
    "Muramvya": (-3.26, 29.63, "Muramvya", "Burundi"),
    "Mwaro": (-3.51, 29.72, "Mwaro", "Burundi"),
    "Gitega": (-3.43, 29.93, "Gitega", "Burundi"),
    "Rutana": (-3.90, 29.99, "Rutana", "Burundi"),
    "Makamba": (-4.13, 29.81, "Makamba", "Burundi"),
    "Bururi": (-3.94, 29.62, "Bururi", "Burundi"),
    "Rumonge": (-3.97, 29.45, "Rumonge", "Burundi"),
    "Muyinga": (-2.84, 30.34, "Muyinga", "Burundi"),
    "Kirundo": (-2.58, 30.09, "Kirundo", "Burundi"),
    "Cankuzo": (-3.17, 30.55, "Cankuzo", "Burundi"),
    "Ruyigi": (-3.48, 30.25, "Ruyigi", "Burundi"),

    # --- Nouvelles provinces administratives (Burundi) ---
    "Buhumuza": (-3.17, 30.55, "Buhumuza", "Burundi"),
    "Burunga": (-3.94, 29.62, "Burunga", "Burundi"),
    "Butanyerera": (-2.91, 29.83, "Butanyerera", "Burundi"),

    # --- Communes et villes majeures du Burundi ---
    "Nyanza-Lac": (-4.35, 29.60, "Nyanza-Lac (Makamba)", "Burundi"),
    "Gatumba": (-3.35, 29.24, "Gatumba (Bujumbura)", "Burundi"),
    "Rugombo": (-2.83, 29.08, "Rugombo (Cibitoke)", "Burundi"),
    "Mabayi": (-2.68, 29.27, "Mabayi (Cibitoke)", "Burundi"),
    "Bugarama": (-3.55, 29.47, "Bugarama (Rumonge)", "Burundi"),
    "Kayogoro": (-4.12, 30.02, "Kayogoro (Makamba)", "Burundi"),
    "Teza": (-3.22, 29.57, "Teza (Muramvya)", "Burundi"),
    "Mabanda": (-4.27, 29.77, "Mabanda (Makamba)", "Burundi"),
    "Kabezi": (-3.54, 29.35, "Kabezi (Bujumbura)", "Burundi"),
    "Gitaza": (-3.60, 29.34, "Gitaza (Rumonge)", "Burundi"),

    # --- Métropoles et hubs régionaux est-africains ---
    "Kigali": (-1.95, 30.06, "Kigali", "Rwanda"),
    "Bukavu": (-2.51, 28.86, "Bukavu", "RDC"),
    "Uvira": (-3.40, 29.14, "Uvira", "RDC"),
    "Goma": (-1.68, 29.23, "Goma", "RDC"),
    "Nairobi": (-1.29, 36.82, "Nairobi", "Kenya"),
    "Kampala": (0.32, 32.58, "Kampala", "Ouganda"),
    "Dodoma": (-6.17, 35.74, "Dodoma", "Tanzanie"),
    "Dar es Salaam": (-6.82, 39.28, "Dar es Salaam", "Tanzanie"),
    "Mwanza": (-2.52, 32.90, "Mwanza", "Tanzanie"),
}

# Compatibilité descendante
PROVINCES: Dict[str, tuple] = {
    k: (v[0], v[1]) for k, v in LOCATIONS.items()
    if v[3] == "Burundi" and not k.startswith("Buhumuza") and not k.startswith("Burunga") and not k.startswith("Butanyerera") and k != "Bujumbura"
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
    return WMO.get(code, ("❓", "Temps variable"))

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
                "Surveillez les maladies = humidité élevée (mildiou, pourridié).",
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
            "Contre-saison dans les marais drainés : maraîchage intensif.",
            "Stockage et conservation des récoltes de saison B.",
            "Préparez le fumier et la litière pour la saison A.",
        ],
    }


class WeatherService:
    """Météo réelle (Open-Meteo) + calendrier saisonnier pour villes et provinces."""

    def __init__(self):
        # Cache mémoire de géocodage dynamique : query -> {lat, lon, name, country}
        self._geocode_cache: Dict[str, Dict[str, Any]] = {}

    async def resolve_location(self, query: Optional[str]) -> Tuple[float, float, str, str, bool]:
        """
        Résout une localisation en (lat, lon, display_name, country, fallback_used).
        Tente dans l'ordre :
          1. Dictionnaire local LOCATIONS (instantané)
          2. Cache mémoire de géocodage
          3. API gratuite Open-Meteo Geocoding
          4. Fallback Gitega si introuvable
        """
        if not query or not query.strip():
            loc = LOCATIONS["Gitega"]
            return loc[0], loc[1], loc[2], loc[3], False

        clean = query.strip()
        clean_lower = clean.lower()

        # 1. Correspondance exacte ou préfixe dans LOCATIONS
        for key, val in LOCATIONS.items():
            if clean_lower == key.lower():
                return val[0], val[1], val[2], val[3], False
        for key, val in LOCATIONS.items():
            first_word = key.split()[0].lower()
            if clean_lower == first_word or clean_lower.startswith(first_word):
                return val[0], val[1], val[2], val[3], False

        # 2. Vérification dans le cache mémoire
        if clean_lower in self._geocode_cache:
            c = self._geocode_cache[clean_lower]
            return c["lat"], c["lon"], c["name"], c["country"], False

        # 3. Géocodage dynamique via Open-Meteo Geocoding API
        try:
            url = "https://geocoding-api.open-meteo.com/v1/search"
            params = {"name": clean, "count": 1, "language": "fr", "format": "json"}
            async with httpx.AsyncClient(timeout=4.0) as client:
                r = await client.get(url, params=params)
                if r.status_code == 200:
                    data = r.json()
                    results = data.get("results", [])
                    if results:
                        res = results[0]
                        lat = float(res["latitude"])
                        lon = float(res["longitude"])
                        name = res.get("name", clean.title())
                        admin1 = res.get("admin1")
                        country = res.get("country", "")
                        disp_name = f"{name} ({admin1})" if admin1 and admin1 != name else name
                        self._geocode_cache[clean_lower] = {
                            "lat": lat,
                            "lon": lon,
                            "name": disp_name,
                            "country": country,
                        }
                        return lat, lon, disp_name, country, False
        except Exception:
            pass

        # 4. Fallback sur Gitega
        fallback = LOCATIONS["Gitega"]
        return fallback[0], fallback[1], f"{clean.title()} (inconnu, météo Gitega)", "Burundi", True

    def normalize_province(self, name: Optional[str]) -> str:
        """Compatibilité historique : retourne un nom de province connu."""
        if not name:
            return "Gitega"
        n = name.strip().lower()
        for p in PROVINCES:
            if n == p.lower() or n.startswith(p.split()[0].lower()):
                return p
        return "Gitega"

    def _season_today(self) -> dict:
        return _season_for(date.today().month)

    async def get_forecast(self, location: Optional[str] = None) -> Dict[str, Any]:
        """Météo actuelle + 5 jours + conseils agricoles pour n'importe quelle ville ou province."""
        lat, lon, disp_name, country, fallback_used = await self.resolve_location(location)

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
            "timezone": "Africa/Bujumbura",
            "forecast_days": 5,
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get(url, params=params)
                r.raise_for_status()
                data = r.json()
        except Exception:
            return {
                "province": disp_name,
                "location_name": disp_name,
                "country": country,
                "available": False,
                "error": "Service météo momentanément indisponible (problème réseau).",
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

        advice = ""
        if total_rain >= 15:
            advice = "Bon cumul de pluie prévu : profitez-en pour semer ou transplanter."
        elif total_rain <= 2:
            advice = "Peu de pluie prévue : prévenez le stress hydrique (paillage, arrosage régulier)."
        else:
            advice = "Conditions d'humidité modérées : idéales pour l'entretien et le désherbage."

        return {
            "province": disp_name,
            "location_name": disp_name,
            "country": country,
            "coordinates": {"latitude": lat, "longitude": lon},
            "available": True,
            "fallback_used": fallback_used,
            "current": {
                "temperature": cur.get("temperature_2m"),
                "humidity": cur.get("relative_humidity_2m"),
                "wind_speed": cur.get("wind_speed_10m"),
                "precipitation": cur.get("precipitation"),
                "emoji": emoji_now,
                "label": label_now,
            },
            "daily": daily,
            "rain_5d_mm": round(total_rain, 1),
            "advice": advice,
            "today_season": season,
        }

    async def format_chat_response(self, location_query: str) -> str:
        """Génère une réponse formatée en Markdown pour le chat."""
        w = await self.get_forecast(location_query)
        if not w.get("available"):
            return (
                f"⚠️ Désolé, les informations météo pour **{location_query}** ne sont pas disponibles "
                f"pour le moment ({w.get('error', 'erreur réseau')})."
            )

        cur = w.get("current", {})
        temp = cur.get("temperature")
        temp_str = f"{round(temp)} °C" if temp is not None else "N/A"
        humidity = cur.get("humidity")
        hum_str = f" · Humidité : {humidity} %" if humidity is not None else ""
        wind = cur.get("wind_speed")
        wind_str = f" · Vent : {wind} km/h" if wind is not None else ""
        rain_today = cur.get("precipitation", 0)

        loc_label = f"{w['location_name']}"
        if w.get("country"):
            loc_label += f" ({w['country']})"

        lines = [
            f"🌤️ **Météo en direct pour {loc_label}** :",
            f"- **Conditions actuelles** : {cur.get('emoji', '🌡️')} **{temp_str}** — {cur.get('label', '')}{hum_str}{wind_str}",
            f"- **Pluie aujourd'hui** : {rain_today} mm · **Cumul prévu (5 jours)** : {w.get('rain_5d_mm', 0)} mm",
            "",
            "📅 **Prévisions des prochains jours** :",
        ]

        days_fr = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        for d in w.get("daily", [])[:5]:
            try:
                dt = date.fromisoformat(d["date"])
                day_name = days_fr[dt.weekday()]
            except Exception:
                day_name = d["date"]
            t_max = round(d['t_max']) if d['t_max'] is not None else '?'
            t_min = round(d['t_min']) if d['t_min'] is not None else '?'
            rain = d.get('rain_mm', 0)
            lines.append(f"  • **{day_name}** : {d['emoji']} {t_max}° / {t_min}° (💧 {rain} mm)")

        if w.get("advice"):
            lines.append("")
            lines.append(f"💡 **Conseil agricole** : {w['advice']}")

        season = w.get("today_season", {})
        if season.get("name"):
            lines.append(f"🌱 **Calendrier** : {season['name']} ({season.get('window', '')})")

        return "\n".join(lines)


weather_service = WeatherService()

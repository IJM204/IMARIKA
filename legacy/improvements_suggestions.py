# Additional Agricultural Tools for RAG System

import datetime
from typing import Dict, Any

def get_planting_calendar(crop: str, location: str = "East Africa") -> str:
    """Provide planting calendar based on crop and region"""
    calendars = {
        "maize": "Plant during long rains (March-May) or short rains (October-December)",
        "beans": "Plant at start of rainy seasons, avoid waterlogged conditions", 
        "cassava": "Plant year-round, best during rainy season onset",
        "sweet_potato": "Plant during rainy seasons, harvest after 4-6 months"
    }
    
    crop_lower = crop.lower()
    advice = calendars.get(crop_lower, f"Consult local extension for {crop} planting times")
    
    current_month = datetime.datetime.now().strftime("%B")
    return f"Planting advice for {crop}:\n{advice}\n\nCurrent month: {current_month}"

def calculate_irrigation_needs(crop: str, temperature: float, humidity: float) -> str:
    """Calculate basic irrigation requirements"""
    if temperature > 30 and humidity < 50:
        return f"{crop} needs frequent irrigation - daily watering recommended"
    elif temperature > 25 and humidity < 60:
        return f"{crop} needs moderate irrigation - water every 2-3 days"
    else:
        return f"{crop} irrigation needs are low - monitor soil moisture"

def pest_disease_alert(weather_conditions: Dict[str, Any]) -> str:
    """Alert for pest/disease risks based on weather"""
    temp = weather_conditions.get('temperature', 25)
    humidity = weather_conditions.get('humidity', 60)
    
    alerts = []
    
    if humidity > 80:
        alerts.append("High fungal disease risk - ensure good air circulation")
    if temp > 28 and humidity > 70:
        alerts.append("Bacterial disease risk - avoid overhead watering")
    if temp > 30:
        alerts.append("Heat stress risk - provide shade for sensitive crops")
        
    return "Pest/Disease Alerts:\n" + "\n".join(f"• {alert}" for alert in alerts) if alerts else "No major risks detected"

def soil_moisture_advice(weather_data: str) -> str:
    """Provide soil moisture management advice"""
    if "rain" in weather_data.lower():
        return "Recent rain detected - check soil drainage, avoid overwatering"
    elif "clear" in weather_data.lower() or "sunny" in weather_data.lower():
        return "Clear weather - monitor soil moisture levels, consider mulching"
    else:
        return "Check soil moisture manually - insert finger 2 inches into soil"

# Market price integration (mock function)
def get_crop_prices(crop: str, location: str = "Kenya") -> str:
    """Mock function for crop price information"""
    # In real implementation, this would connect to agricultural market APIs
    prices = {
        "maize": "KES 45-50 per kg",
        "beans": "KES 80-100 per kg", 
        "cassava": "KES 25-30 per kg"
    }
    
    price = prices.get(crop.lower(), "Price data not available")
    return f"Current {crop} prices in {location}: {price}\n(Prices are indicative - check local markets)"
import streamlit as st
import requests
import os
from datetime import datetime

def get_weather_data(location):
    """Get weather data for location"""
    api_key = os.getenv("OPENWEATHER_API_KEY", "demo_key")
    
    if api_key == "demo_key":
        # Return demo data if no API key
        return {
            "location": location,
            "temperature": 22.5,
            "humidity": 65,
            "description": "partly cloudy",
            "wind_speed": 3.2,
            "pressure": 1013,
            "forecast": [
                {"date": "2024-01-01", "temp": 24, "description": "sunny"},
                {"date": "2024-01-02", "temp": 21, "description": "cloudy"},
                {"date": "2024-01-03", "temp": 23, "description": "partly cloudy"}
            ]
        }
    
    try:
        # Current weather
        current_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        current_response = requests.get(current_url, timeout=5)
        
        if current_response.status_code == 200:
            current_data = current_response.json()
            return {
                "location": location,
                "temperature": current_data["main"]["temp"],
                "humidity": current_data["main"]["humidity"],
                "description": current_data["weather"][0]["description"],
                "wind_speed": current_data["wind"]["speed"],
                "pressure": current_data["main"]["pressure"]
            }
    except:
        pass
    
    return None

def render_weather_widget():
    """Render weather widget"""
    
    location = st.session_state.get('user_location', 'Nairobi')
    weather_data = get_weather_data(location)
    
    if weather_data:
        st.markdown(f"""
        <div class="weather-widget fade-in">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <div style="font-size: 1.5rem; margin-right: 0.5rem;">🌤️</div>
                        <div style="font-size: 1.2rem; font-weight: 600;">Weather in {weather_data['location']}</div>
                    </div>
                    <div style="font-size: 2rem; font-weight: 700; margin: 0.5rem 0;">
                        {weather_data['temperature']:.1f}°C
                    </div>
                    <div style="text-transform: capitalize; opacity: 0.9;">
                        {weather_data['description']}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="margin-bottom: 0.5rem;">
                        <span style="opacity: 0.8;">Humidity:</span> {weather_data['humidity']}%
                    </div>
                    <div style="margin-bottom: 0.5rem;">
                        <span style="opacity: 0.8;">Wind:</span> {weather_data['wind_speed']} m/s
                    </div>
                    <div>
                        <span style="opacity: 0.8;">Pressure:</span> {weather_data['pressure']} hPa
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Agricultural advice based on weather
        if weather_data['temperature'] > 25:
            advice = "🌡️ High temperature - ensure adequate irrigation for crops"
            color = "#FF6B6B"
        elif weather_data['humidity'] > 80:
            advice = "💧 High humidity - monitor for fungal diseases"
            color = "#4ECDC4"
        elif weather_data['wind_speed'] > 5:
            advice = "💨 Windy conditions - secure young plants and check irrigation"
            color = "#45B7D1"
        else:
            advice = "✅ Good conditions for most agricultural activities"
            color = "#96CEB4"
        
        st.markdown(f"""
        <div style="background: {color}; color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0; text-align: center;">
            <strong>{advice}</strong>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        st.markdown("""
        <div class="weather-widget fade-in">
            <div style="text-align: center;">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🌤️</div>
                <div>Weather data unavailable</div>
                <div style="font-size: 0.9rem; opacity: 0.8; margin-top: 0.5rem;">
                    Add OpenWeather API key for live weather data
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
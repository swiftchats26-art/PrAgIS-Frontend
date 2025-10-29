import python_weather
import asyncio
from typing import Dict, Optional

async def fetch_python_weather(lat: float, lon: float) -> Optional[Dict]:
    """Fetch weather data using python-weather as a backup source.
    
    Args:
        lat: Latitude of the location
        lon: Longitude of the location
        
    Returns:
        Dictionary containing weather data or None if fetch fails
    """
    try:
        # Initialize the client. Older/newer versions expose different unit constants
        unit = None
        if hasattr(python_weather, "CELSIUS"):
            unit = getattr(python_weather, "CELSIUS")
        elif hasattr(python_weather, "METRIC"):
            unit = getattr(python_weather, "METRIC")

        # Use unit if available, otherwise fall back to default client
        if unit is not None:
            async with python_weather.Client(unit=unit) as client:
                # Fetch weather data based on lat/lon
                weather = await client.get(f"{lat},{lon}")
        else:
            async with python_weather.Client() as client:
                weather = await client.get(f"{lat},{lon}")
            
            if not weather:
                return None
                
            # Extract current conditions
            current = {
                "temperature": weather.current.temperature,
                "humidity": weather.current.humidity,
                "description": weather.current.description,
            }
            
            # Get forecast for next few days
            forecast = []
            for forecast_day in weather.forecasts:
                day_data = {
                    "date": forecast_day.date.isoformat(),
                    "temperature": forecast_day.temperature,
                    "humidity": forecast_day.humidity,
                    "description": forecast_day.description,
                }
                # Add hourly data if available
                if forecast_day.hourly:
                    hourly = []
                    for hour in forecast_day.hourly:
                        hourly.append({
                            "time": hour.time.isoformat(),
                            "temperature": hour.temperature,
                            "humidity": hour.humidity,
                            "description": hour.description
                        })
                    day_data["hourly"] = hourly
                forecast.append(day_data)
            
            return {
                "current": current,
                "forecast": forecast,
                "source": "python-weather"
            }
            
    except Exception as e:
        print(f"Error fetching python-weather data: {str(e)}")
        return None
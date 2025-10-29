"""Mock weather provider for testing."""
from typing import Dict, Any
from datetime import datetime, timezone
from ..services.weather_types import WeatherData, validate_weather_data
from ..services.weather_service import WeatherProvider

class MockWeatherProvider(WeatherProvider):
    """Mock weather provider that returns test data."""
    
    def __init__(self, mock_data: Dict[str, Any] = None):
        self.mock_data = mock_data or {}
        
    def get_provider_name(self) -> str:
        return "mock"
        
    async def get_weather_data(self, lat: float, lon: float) -> WeatherData:
        """Get mock weather data."""
        # Use provided mock data or generate test data
        data = self.mock_data.get(f"{lat:.4f},{lon:.4f}") or {
            "et0_mm": 4.0,
            "recent_rain_mm": 0.0,
            "forecast_rain_mm": 0.0,
            "tmax_c": 30.0,
            "rh_percent": 60.0,
            "wind_speed_ms": 2.0,
            "solar_rad_wmpm2": 500.0,
            "source": "mock",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location_quality": "actual"
        }
        
        return validate_weather_data(data)
        
def create_mock_weather_data(locations: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Create mock weather data for testing.
    
    Args:
        locations: Dict mapping "lat,lon" strings to weather data
        
    Returns:
        Dict suitable for MockWeatherProvider
    """
    mock_data = {}
    for loc, data in locations.items():
        # Ensure required fields
        full_data = {
            "et0_mm": data.get("et0_mm", 4.0),
            "recent_rain_mm": data.get("recent_rain_mm", 0.0),
            "forecast_rain_mm": data.get("forecast_rain_mm", 0.0),
            "tmax_c": data.get("tmax_c", 30.0),
            "rh_percent": data.get("rh_percent", 60.0),
            "wind_speed_ms": data.get("wind_speed_ms", 2.0),
            "solar_rad_wmpm2": data.get("solar_rad_wmpm2", 500.0),
            "source": "mock",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location_quality": "actual"
        }
        mock_data[loc] = full_data
        
    return mock_data
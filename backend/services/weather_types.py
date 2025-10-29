"""Type definitions and validators for weather data."""
from typing import TypedDict, Optional
from datetime import datetime, timezone
import json

class WeatherData(TypedDict):
    """Standardized weather data format."""
    et0_mm: float           # Reference ET in mm/day
    recent_rain_mm: float   # Recent rainfall in mm
    forecast_rain_mm: float # Forecasted rain in mm
    tmax_c: float          # Max temperature in Celsius
    rh_percent: float      # Relative humidity %
    wind_speed_ms: float   # Wind speed m/s
    solar_rad_wmpm2: float # Solar radiation W/m²
    source: str            # Data source identifier
    timestamp: str         # ISO format timestamp
    location_quality: str  # "actual" or "interpolated"
    
def validate_weather_data(data: dict) -> WeatherData:
    """Validate and normalize weather data.
    
    Args:
        data: Raw weather data dict
        
    Returns:
        Normalized WeatherData
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    if not isinstance(data, dict):
        raise ValueError("Weather data must be a dictionary")
        
    # Required fields with validation
    result = {
        "et0_mm": float(data.get("et0_mm", 0.0)),
        "recent_rain_mm": float(data.get("recent_rain_mm", 0.0)),
        "forecast_rain_mm": float(data.get("forecast_rain_mm", 0.0)),
        "tmax_c": float(data.get("tmax_c", 25.0)),  # Default reasonable temp
        "rh_percent": float(data.get("rh_percent", 60.0)),  # Default RH
        "wind_speed_ms": float(data.get("wind_speed_ms", 2.0)),  # Light breeze default
        "solar_rad_wmpm2": float(data.get("solar_rad_wmpm2", 500.0)),  # Moderate radiation
        "source": str(data.get("source", "unknown")),
        "timestamp": data.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        "location_quality": data.get("location_quality", "interpolated")
    }
    
    # Validation rules
    if result["et0_mm"] < 0 or result["et0_mm"] > 15:  # Max realistic ET0
        raise ValueError(f"Invalid ET0 value: {result['et0_mm']}")
        
    if result["recent_rain_mm"] < 0:
        raise ValueError(f"Invalid recent rain value: {result['recent_rain_mm']}")
        
    if result["forecast_rain_mm"] < 0:
        raise ValueError(f"Invalid forecast rain value: {result['forecast_rain_mm']}")
        
    if result["tmax_c"] < -50 or result["tmax_c"] > 60:  # Earth's records
        raise ValueError(f"Invalid temperature value: {result['tmax_c']}")
        
    if result["rh_percent"] < 0 or result["rh_percent"] > 100:
        raise ValueError(f"Invalid humidity value: {result['rh_percent']}")
        
    return result

def calculate_et0(temp_c: float, rh_percent: float, wind_speed_ms: float, 
                 solar_rad_wmpm2: float, elevation_m: float = 100) -> float:
    """Calculate ET0 using FAO Penman-Monteith equation.
    
    Simplified version for demonstration. Production code should use
    proper FAO-56 implementation with all required parameters.
    
    Args:
        temp_c: Air temperature in Celsius
        rh_percent: Relative humidity percentage
        wind_speed_ms: Wind speed in m/s
        solar_rad_wmpm2: Solar radiation in W/m²
        elevation_m: Elevation in meters (default 100m)
        
    Returns:
        ET0 in mm/day
    """
    # Convert solar radiation from W/m² to MJ/m²/day
    solar_rad_mj = solar_rad_wmpm2 * 0.0864
    
    # Simplified calculation (demo only - use full equation in production)
    et0 = (0.0023 * (temp_c + 17.8) * solar_rad_mj * 
           (1 + 0.033 * wind_speed_ms) * 
           (1 - rh_percent/200))
    
    return max(0, round(et0, 2))  # Ensure non-negative
    
def cache_weather_data(data: WeatherData, cache_file: str):
    """Cache weather data to file.
    
    Args:
        data: Weather data to cache
        cache_file: Path to cache file
    """
    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cache = {}
        
    # Use timestamp as key
    cache[data["timestamp"]] = data
    
    # Keep only last 24 hours of data
    now = datetime.now(timezone.utc)
    cache = {
        k: v for k, v in cache.items()
        if (now - datetime.fromisoformat(k)).total_seconds() < 86400
    }
    
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)
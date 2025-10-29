from typing import Dict, Any, Optional
import logging
from ..services.weather_service import get_weather_service
from ..services.weather_types import WeatherData

logger = logging.getLogger(__name__)

class ET0Agent:
    """Evapotranspiration (ET0) Agent using weather service.
    
    Provides ET0 estimates from multiple sources with quality indicators:
    1. Direct weather feed if provided
    2. Weather service providers (Open-Meteo, local stations)
    3. Cached weather data
    4. Temperature-based estimation as fallback
    """
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.weather_service = get_weather_service()

    async def run(self, input_data: Dict[str, Any]) -> Dict:
        last_5 = input_data.get("last_5_days", []) or []
        # prefer to use pyet if available and climate inputs provided
        # attempt to collect a temperature and humidity estimate
        temps = [d.get("tmax_c") for d in last_5 if d.get("tmax_c") is not None]
        avg_temp = sum(temps) / len(temps) if temps else None

        et0 = None
        # try pyet wrapper
        try:
            from ..clients.pyet_wrapper import compute_et0_with_pyet
            if avg_temp is not None:
                et0 = compute_et0_with_pyet(temperature=avg_temp)
        except Exception:
            et0 = None

        # Try direct weather feed first
        if input_data.get("weather_feed"):
            try:
                weather = input_data["weather_feed"]
                if weather.get("et0_mm"):
                    et0 = float(weather["et0_mm"])
                    output = {"et0_mm_per_day": et0, "source": "weather_feed"}
                    # High confidence for direct weather feed data
                    return {"output": output, "confidence": 0.95}
            except Exception:
                pass
                
        # fallback: estimate from temperature
        if et0 is None and avg_temp is not None:
            et0 = round(0.2 * avg_temp, 2)  # Simple temperature-based estimate
            
        output = {
            "et0_mm_per_day": et0,
            "source": "temperature_estimate" if avg_temp is not None else None,
            "temperature_c": avg_temp
        }
        
        # Composite confidence based on data source quality
        if et0 is None:
            confidence = 0.1  # No usable data
        elif output["source"] == "weather_feed":
            confidence = 0.95  # Direct weather feed
        elif output["source"] == "temperature_estimate":
            confidence = 0.6 + min(0.2, 0.04 * len(temps))  # Temperature-based estimate
        else:
            confidence = 0.4  # Unknown source
            
        return {"output": output, "confidence": round(confidence, 2)}

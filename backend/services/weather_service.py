"""Weather data service that uses free providers (Open-Meteo and python-weather).

This module intentionally avoids paid providers. Open-Meteo (free) is the primary
source and `python-weather` is used as a backup when needed. A lightweight local
cache/fallback is present for resilience.
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import json
import asyncio
from functools import partial
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class WeatherProvider(ABC):
    """Abstract base class for weather data providers."""

    @abstractmethod
    async def get_weather_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Return standardized weather dict for the given location."""


class OpenMeteoProvider(WeatherProvider):
    """Provider that uses the Open-Meteo free API via the sync client helper.

    The client in `backend.clients.open_meteo` is synchronous, so we call it in
    a thread executor to avoid blocking the event loop.
    """

    def __init__(self, days: int = 5, timezone: str = "UTC"):
        self.days = days
        self.timezone = timezone

    async def get_weather_data(self, lat: float, lon: float) -> Dict[str, Any]:
        try:
            # Import the sync helper and run in executor
            from ..clients.open_meteo import fetch_open_meteo
            loop = asyncio.get_running_loop()
            fetch = partial(fetch_open_meteo, lat, lon, self.days, self.timezone)
            result = await loop.run_in_executor(None, fetch)
        except Exception as e:
            logger.error(f"OpenMeteo fetch failed: {e}")
            result = None

        # Default fallback values
        tmax_c = None
        recent_rain = 0.0
        forecast_rain = 0.0

        if result and isinstance(result, dict):
            daily = result.get("daily", {})
            tmax_list = daily.get("temperature_2m_max", [])
            precip_list = daily.get("precipitation_sum", [])
            try:
                if tmax_list:
                    tmax_c = float(tmax_list[-1])
                if precip_list:
                    recent_rain = float(precip_list[-1])
                    # forecast: sum of next day's precip if available
                    if len(precip_list) >= 2:
                        forecast_rain = float(precip_list[-1])  # best-effort
            except Exception:
                pass

        # Simple ET0 estimate (fallback) — replace with proper calculator as needed
        if tmax_c is not None:
            try:
                et0 = 0.0023 * (tmax_c + 17.8) * (max(tmax_c - 20, 0)) * 0.408
            except Exception:
                et0 = 4.0
        else:
            et0 = 4.0

        return {
            "et0_mm": round(float(et0), 2),
            "recent_rain_mm": round(float(recent_rain), 2),
            "forecast_rain_mm": round(float(forecast_rain), 2),
            "tmax_c": round(float(tmax_c), 2) if tmax_c is not None else None,
            "rh_percent": None,
            "wind_speed_ms": None,
            "solar_rad_wmpm2": None,
            "source": "open_meteo",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location_quality": "actual"
        }


class PythonWeatherProvider(WeatherProvider):
    """Provider that uses the async `python-weather` client as a backup."""

    async def get_weather_data(self, lat: float, lon: float) -> Dict[str, Any]:
        try:
            from ..clients.weather import fetch_python_weather
            res = await fetch_python_weather(lat, lon)
            if not res:
                raise RuntimeError("python-weather returned no data")

            current = res.get("current", {})
            forecast = res.get("forecast", [])
            tmax = current.get("temperature")
            recent_rain = 0.0
            forecast_rain = 0.0
            # attempt to derive forecast rain from hourly/forecast if available
            if forecast:
                # no direct precipitation in python-weather; keep zeros
                pass

            et0 = 0.0023 * (tmax + 17.8) * (max(tmax - 20, 0)) * 0.408 if tmax is not None else 4.0

            return {
                "et0_mm": round(float(et0), 2),
                "recent_rain_mm": round(float(recent_rain), 2),
                "forecast_rain_mm": round(float(forecast_rain), 2),
                "tmax_c": round(float(tmax), 2) if tmax is not None else None,
                "rh_percent": current.get("humidity"),
                "wind_speed_ms": None,
                "solar_rad_wmpm2": None,
                "source": res.get("source", "python-weather"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "location_quality": "actual"
            }
        except Exception as e:
            logger.debug(f"python-weather provider failed: {e}")
            raise


class LocalWeatherProvider(WeatherProvider):
    """Local weather station or cached data provider."""

    def __init__(self, cache_file: Optional[str] = None):
        self.cache_file = cache_file or "weather_cache.json"

    async def get_weather_data(self, lat: float, lon: float) -> Dict[str, Any]:
        try:
            with open(self.cache_file, "r") as f:
                cache = json.load(f)

            cached = cache.get(f"{lat:.4f},{lon:.4f}")
            if cached:
                return {
                    **cached,
                    "source": "local_cache",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
        except Exception:
            pass

        # Fallback estimation
        return {
            "et0_mm": 4.0,
            "recent_rain_mm": 0.0,
            "forecast_rain_mm": 0.0,
            "tmax_c": 30.0,
            "rh_percent": None,
            "wind_speed_ms": None,
            "solar_rad_wmpm2": None,
            "source": "fallback",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location_quality": "interpolated"
        }


# Singleton instance
_weather_service_instance = None

def get_weather_service():
    """Get or create the singleton WeatherService instance."""
    global _weather_service_instance
    if _weather_service_instance is None:
        _weather_service_instance = WeatherService()
    return _weather_service_instance

class WeatherService:
    """Weather service that manages providers and caching.

    Defaults to `open_meteo` (free). Falls back to `python_weather` then `local`.
    """

    def __init__(self):
        self.providers: Dict[str, WeatherProvider] = {}
        self._setup_providers()

    def _setup_providers(self):
        # Register free providers
        try:
            self.providers["open_meteo"] = OpenMeteoProvider()
            logger.info("Registered OpenMeteoProvider")
        except Exception as e:
            logger.warning(f"Could not register OpenMeteoProvider: {e}")

        try:
            self.providers["python_weather"] = PythonWeatherProvider()
            logger.info("Registered PythonWeatherProvider")
        except Exception:
            logger.debug("python-weather is not available")

        # Local provider always available
        self.providers["local"] = LocalWeatherProvider()

    async def get_weather(self, lat: float, lon: float, provider: str = "open_meteo") -> Dict[str, Any]:
        """Get weather data from the preferred provider with fallbacks.

        Args:
            lat: Latitude
            lon: Longitude
            provider: Preferred provider key (default: 'open_meteo')
        """
        tried = []

        if provider in self.providers:
            try:
                return await self.providers[provider].get_weather_data(lat, lon)
            except Exception as e:
                logger.warning(f"Weather provider {provider} failed: {e}")
                tried.append(provider)

        # Try python_weather if available and not already tried
        if "python_weather" in self.providers and "python_weather" not in tried:
            try:
                return await self.providers["python_weather"].get_weather_data(lat, lon)
            except Exception as e:
                logger.warning(f"python_weather provider failed: {e}")
                tried.append("python_weather")

        # Finally try local fallback
        return await self.providers["local"].get_weather_data(lat, lon)

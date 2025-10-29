import datetime
from typing import Optional, Dict, Any
import requests


def fetch_open_meteo(lat: float, lon: float, days: int = 5, timezone: str = "UTC") -> Optional[Dict[str, Any]]:
    """Fetch daily summary (tmax,tmin,precipitation) for the last `days` days including today.

    Returns a dict with daily lists or None on error.
    """
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days - 1)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": timezone,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None

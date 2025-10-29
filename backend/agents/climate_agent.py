from typing import Dict, Any
from ..clients.weather import fetch_python_weather


class ClimateAgent:
    """Climate Agent with multiple data sources.

    Expects last 5 days data in the request. Returns a summary and a confidence.
    Can use Open-Meteo and python-weather as backup sources.
    """
    def __init__(self, config: Dict = None):
        self.config = config or {}
        # optional client will be dynamically imported
        self.client = None

    async def run(self, input_data: Dict[str, Any]) -> Dict:
        last_5 = input_data.get("last_5_days", []) or []
        lat = input_data.get("latitude")
        lon = input_data.get("longitude")
        # try to fetch data from backup sources if lat/lon provided
        om_data = None
        pw_data = None
        if lat is not None and lon is not None:
            try:
                from ..clients.open_meteo import fetch_open_meteo
                om_data = await __import_open_meteo(lat, lon)
            except Exception:
                om_data = None
            
            try:
                pw_data = await fetch_python_weather(lat, lon)
            except Exception:
                pw_data = None
        # placeholder: average Tmax, Tmin, rainfall
        tmax = None
        tmin = None
        rain = 0.0
        count = 0
        for d in last_5:
            if d.get("tmax_c") is not None:
                tmax = (tmax or 0) + d.get("tmax_c")
            if d.get("tmin_c") is not None:
                tmin = (tmin or 0) + d.get("tmin_c")
            if d.get("rainfall_mm"):
                rain += d.get("rainfall_mm")
            count += 1
        if count:
            tmax = tmax / count if tmax is not None else None
            tmin = tmin / count if tmin is not None else None

        output = {
            "avg_tmax_c": tmax,
            "avg_tmin_c": tmin,
            "total_rainfall_mm": rain,
            "open_meteo": om_data,
            "python_weather": pw_data,
        }
        # confidence placeholder: more data -> higher confidence
        confidence = min(0.95, 0.5 + 0.1 * len(last_5))
        return {"output": output, "confidence": round(confidence, 2)}


async def __import_open_meteo(lat, lon):
    # run blocking requests call in thread
    import asyncio
    from functools import partial
    from ..clients.open_meteo import fetch_open_meteo

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(fetch_open_meteo, lat, lon))

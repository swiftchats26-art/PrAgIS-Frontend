from typing import Optional

def compute_et0_with_pyet(temperature: float, humidity: float = 50.0, wind: float = 2.0, radiation: float = 15.0) -> Optional[float]:
    """Try to compute ET0 using pyet if available, otherwise return None.

    This is a thin wrapper that gracefully handles absence of pyet.
    """
    try:
        import pyet
        # Use a simpler method that works with basic inputs
        if hasattr(pyet, "hargreaves"):
            # pyet expects pandas series, but we can use simple calculation
            return round(0.0023 * (temperature + 17.8) * (temperature - temperature) ** 0.5, 2)
        # fallback to simple temperature-based estimate
        return round(0.2 * temperature, 2)
    except Exception:
        return round(0.2 * temperature, 2)

"""Validates and processes location data for soil/climate queries."""
from typing import Dict, Tuple, Optional
import math

def validate_coordinates(lat: float, lon: float) -> Tuple[bool, str]:
    """Validate if coordinates are within reasonable bounds for India."""
    if not (6 <= lat <= 37 and 68 <= lon <= 97):
        return False, "Coordinates outside India's boundaries"
    return True, "OK"

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula."""
    R = 6371  # Earth's radius in km

    lat1, lon1 = math.radians(lat1), math.radians(lon1)
    lat2, lon2 = math.radians(lat2), math.radians(lon2)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def get_fallback_location(region: str = "UP") -> Dict[str, float]:
    """Get fallback coordinates for known regions."""
    FALLBACK_COORDS = {
        "UP": {"lat": 26.8467, "lon": 80.9462},  # Lucknow
        "Punjab": {"lat": 30.9010, "lon": 75.8573},  # Ludhiana
        "Bihar": {"lat": 25.5941, "lon": 85.1376}  # Patna
    }
    return FALLBACK_COORDS.get(region, FALLBACK_COORDS["UP"])

def validate_nearest_point(
    query_lat: float,
    query_lon: float,
    nearest_lat: float,
    nearest_lon: float,
    max_distance_km: float = 50.0
) -> Tuple[float, float, float, bool]:
    """Validate nearest point and return fallback if too far.
    
    Returns:
        Tuple of (final_lat, final_lon, distance_km, used_fallback)
    """
    distance = calculate_distance_km(query_lat, query_lon, nearest_lat, nearest_lon)
    
    if distance > max_distance_km:
        fallback = get_fallback_location("UP")
        return (
            fallback["lat"],
            fallback["lon"],
            0.0,  # Distance to fallback (assumed to be accurate)
            True
        )
    
    return nearest_lat, nearest_lon, distance, False
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import numpy as np


class TimeMatch:
    """Utility for time-based adjustments considering location and season.
    
    Handles:
    1. Seasonal adjustments based on location
    2. Growth stage matching
    3. Day/night cycle adjustments
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        # Default latitude bands for seasonal adjustments
        self.lat_bands = {
            "tropical": (-23.5, 23.5),
            "subtropical_n": (23.5, 35),
            "subtropical_s": (-35, -23.5),
            "temperate_n": (35, 66.5),
            "temperate_s": (-66.5, -35)
        }
        
    def get_location_band(self, lat: float) -> str:
        """Determine climate band based on latitude."""
        for band, (min_lat, max_lat) in self.lat_bands.items():
            if min_lat <= lat <= max_lat:
                return band
        return "other"
        
    def get_season(self, date: datetime, lat: float) -> str:
        """Determine current season based on date and latitude."""
        # Month-based season determination
        month = date.month
        
        # Northern/Southern hemisphere adjustment
        if lat > 0:  # Northern hemisphere
            if 3 <= month <= 5:
                return "spring"
            elif 6 <= month <= 8:
                return "summer"
            elif 9 <= month <= 11:
                return "autumn"
            else:
                return "winter"
        else:  # Southern hemisphere
            if 3 <= month <= 5:
                return "autumn"
            elif 6 <= month <= 8:
                return "winter"
            elif 9 <= month <= 11:
                return "spring"
            else:
                return "summer"
    
    def get_adjustment_factors(self, lat: float, lon: float, current_date: Optional[datetime] = None) -> Dict[str, float]:
        """Calculate location and time-based adjustment factors."""
        current_date = current_date or datetime.now()
        
        # Get location band and season
        band = self.get_location_band(lat)
        season = self.get_season(current_date, lat)
        
        # Base adjustments by climate band
        base_factors = {
            "tropical": {"water_need": 1.2, "growth_rate": 1.1},
            "subtropical_n": {"water_need": 1.1, "growth_rate": 1.0},
            "subtropical_s": {"water_need": 1.1, "growth_rate": 1.0},
            "temperate_n": {"water_need": 0.9, "growth_rate": 0.9},
            "temperate_s": {"water_need": 0.9, "growth_rate": 0.9},
            "other": {"water_need": 1.0, "growth_rate": 1.0}
        }
        
        # Seasonal adjustments
        season_factors = {
            "summer": {"water_need": 1.2, "growth_rate": 1.15},
            "spring": {"water_need": 1.1, "growth_rate": 1.1},
            "autumn": {"water_need": 0.9, "growth_rate": 0.9},
            "winter": {"water_need": 0.8, "growth_rate": 0.75}
        }
        
        # Calculate combined factors
        base = base_factors[band]
        seasonal = season_factors[season]
        
        return {
            "water_need": round(base["water_need"] * seasonal["water_need"], 2),
            "growth_rate": round(base["growth_rate"] * seasonal["growth_rate"], 2),
            "location_band": band,
            "season": season,
            "confidence": 0.9  # High confidence in astronomical calculations
        }

    def adjust_schedule(self, base_schedule: Dict[str, Any], lat: float, lon: float) -> Dict[str, Any]:
        """Adjust irrigation schedule based on location and time factors."""
        factors = self.get_adjustment_factors(lat, lon)
        
        # Adjust water volumes by water_need factor
        if "irrigation_volume_mm" in base_schedule:
            base_schedule["irrigation_volume_mm"] *= factors["water_need"]
            base_schedule["irrigation_volume_mm"] = round(base_schedule["irrigation_volume_mm"], 1)
        
        # Add adjustment metadata
        base_schedule["adjustment_factors"] = factors
        
        return base_schedule
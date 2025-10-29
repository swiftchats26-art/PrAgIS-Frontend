"""Drought predictor module using soil and terrain data.

Reads soil_data.csv to determine drought risk based on:
1. Slope distributions (steep slopes increase runoff)
2. Aspect ratios (N/S/E/W facing affects evaporation)
3. Land use ratios (water bodies, vegetation cover)
4. Soil quality indicators
"""
import csv
from pathlib import Path
from typing import Dict, Optional, Tuple
import numpy as np
from .location_validator import calculate_distance_km


class DroughtPredictor:
    def __init__(self, soil_data_path: Optional[str] = None):
        if soil_data_path is None:
            soil_data_path = str(Path(__file__).parent.parent / "soil_data.csv")
        
        self.soil_data = self._load_soil_data(soil_data_path)
        
    def _load_soil_data(self, filepath: str) -> Dict[Tuple[float, float], Dict]:
        """Load and parse soil_data.csv into a dict keyed by (lat,lon)."""
        soil_data = {}
        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        lat = float(row['lat'])
                        lon = float(row['lon'])
                        soil_data[(lat, lon)] = {
                            'elevation': float(row['elevation']),
                            # Slope distributions (8 categories)
                            'slopes': [float(row[f'slope{i}']) for i in range(1,9)],
                            # Aspect ratios (N,E,S,W,Unknown)
                            'aspects': {
                                'N': float(row['aspectN']),
                                'E': float(row['aspectE']),
                                'S': float(row['aspectS']),
                                'W': float(row['aspectW']),
                                'U': float(row['aspectUnknown'])
                            },
                            # Land use percentages
                            'water_pct': float(row['WAT_LAND']),
                            'veg_pct': float(row['NVG_LAND']) + float(row['GRS_LAND']) + float(row['FOR_LAND']),
                            'urban_pct': float(row['URB_LAND']),
                            'cultivated_pct': float(row['CULT_LAND']),
                            # Soil quality indicators
                            'soil_quality': [int(row[f'SQ{i}']) for i in range(1,8)]
                        }
                    except (ValueError, KeyError):
                        continue
        except Exception as e:
            print(f"Error loading soil data: {e}")
            return {}
            
        return soil_data
        
    def _find_nearest_point(self, lat: float, lon: float) -> Optional[Tuple[float, float]]:
        """Find the closest soil data point to the given coordinates."""
        if not self.soil_data:
            return None
            
        points = np.array(list(self.soil_data.keys()))
        query = np.array([lat, lon])
        
        # Calculate Euclidean distances
        distances = np.sqrt(np.sum((points - query)**2, axis=1))
        nearest_idx = np.argmin(distances)
        
        return tuple(points[nearest_idx])
        
    def predict_drought_risk(self, lat: float, lon: float, 
                           current_moisture: Optional[float] = None,
                           crop_type: Optional[str] = None,
                           soil_type: Optional[str] = None) -> Dict:
        """Calculate drought risk score (0-100) and confidence based on soil/terrain data.
        
        Args:
            lat: Latitude of the location
            lon: Longitude of the location
            current_moisture: Current soil moisture percentage if known
            crop_type: Type of crop (e.g., "rice", "wheat")
            soil_type: Soil texture class (e.g., "clay", "sandy")
            
        Returns:
            Dict with drought_risk (0-100), confidence (0-1), and supporting data
        """
        # Try to use soil_data when available and local
        nearest = self._find_nearest_point(lat, lon)
        used_nearest = False
        nearest_details = None

        if nearest:
            data = self.soil_data[nearest]
            try:
                nearest_lat, nearest_lon = nearest
                distance_km = calculate_distance_km(lat, lon, nearest_lat, nearest_lon)
            except Exception:
                distance_km = None

            # If nearest is sufficiently close, use soil-data based predictor
            if distance_km is not None and distance_km <= 50.0:
                used_nearest = True
                # 1. Slope risk: steeper slopes = higher drought risk
                steep_slope_pct = sum(data['slopes'][4:])  # Sum of slopes > category 4
                slope_risk = min(100, steep_slope_pct * 100)

                # 2. Aspect risk: south-facing slopes have higher evaporation
                aspect_risk = (data['aspects']['S'] * 100 + 
                              data['aspects']['W'] * 70 +
                              data['aspects']['E'] * 60 +
                              data['aspects']['N'] * 30) / 2.6  # Normalize to 0-100

                # 3. Land use risk: more vegetation and water = lower risk
                water_veg_pct = data['water_pct'] + (data['veg_pct'] * 0.7)
                land_risk = max(0, 100 - water_veg_pct)

                # 4. Soil quality risk: better quality = lower risk
                sq_avg = np.mean(data['soil_quality'])
                soil_risk = max(0, 100 - (sq_avg * 20))  # Scale 1-5 to 0-100

                # Basic moisture risk (if provided)
                moisture_risk = 0
                try:
                    from .crop_water_constants import CROP_WATER_NEEDS, SOIL_MOISTURE_LIMITS
                    if current_moisture is not None and crop_type and soil_type:
                        if crop_type in CROP_WATER_NEEDS and soil_type in SOIL_MOISTURE_LIMITS:
                            crop_needs = CROP_WATER_NEEDS[crop_type]
                            soil_limits = SOIL_MOISTURE_LIMITS[soil_type]
                            if current_moisture < crop_needs.get("drought_threshold", 0):
                                deficit = crop_needs["drought_threshold"] - current_moisture
                                range_to_wilting = crop_needs["drought_threshold"] - soil_limits["wilting_point"]
                                if range_to_wilting > 0:
                                    moisture_risk = min(100, (deficit / range_to_wilting) * 100)
                                    if current_moisture < soil_limits["wilting_point"]:
                                        moisture_risk = min(100, moisture_risk * 1.5)
                except Exception:
                    moisture_risk = 0

                weights = {
                    'slope': 0.25,
                    'aspect': 0.15,
                    'land': 0.2,
                    'soil': 0.2,
                    'moisture': 0.2
                }

                drought_risk = (
                    slope_risk * weights['slope'] +
                    aspect_risk * weights['aspect'] +
                    land_risk * weights['land'] +
                    soil_risk * weights['soil'] +
                    moisture_risk * weights['moisture']
                )

                confidence = 0.85
                if current_moisture is not None:
                    confidence = min(0.95, confidence + 0.03)

                nearest_details = {
                    'nearest_point': nearest,
                    'distance_km': round(distance_km, 2),
                    'elevation_m': data.get('elevation'),
                    'slope_risk': round(slope_risk, 2),
                    'aspect_risk': round(aspect_risk, 2),
                    'land_risk': round(land_risk, 2),
                    'soil_risk': round(soil_risk, 2)
                }

                return {
                    'drought_risk': round(min(100, max(0, drought_risk)), 2),
                    'confidence': round(confidence, 2),
                    'details': nearest_details
                }

        # If we reach here, soil data is missing or too distant — use custom formula
        # Custom formula inputs: current_moisture (pct), optional et0 and recent rain can be provided
        # We'll accept optional keys via kwargs-like pattern in future; for now assume caller
        # can pass ET0/rain via additional args in the call site if needed.

        # Try to import soil/crop defaults
        try:
            from .irrigation_calculator import SOIL_PARAMS as IC_SOIL_PARAMS
        except Exception:
            IC_SOIL_PARAMS = {}
        try:
            from .crop_water_constants import CROP_WATER_NEEDS as CW_NEEDS
        except Exception:
            CW_NEEDS = {}

        # Use percentage inputs
        if current_moisture is None:
            return {
                'drought_risk': 50,
                'confidence': 0.25,
                'details': {'message': 'No moisture data available', 'used_nearest': False, 'used_custom': True}
            }

        current_vwc = current_moisture / 100.0

        # Determine target and wilting using available metadata
        target_vwc = None
        wilting_vwc = None
        if soil_type and soil_type in IC_SOIL_PARAMS:
            params = IC_SOIL_PARAMS[soil_type]
            target_vwc = getattr(params, 'target_vwc', None)
            wilting_vwc = getattr(params, 'wilting_point_vwc', None)
        if target_vwc is None and crop_type and crop_type in CW_NEEDS:
            target_vwc = CW_NEEDS[crop_type].get('optimal_moisture', None)
            if target_vwc is not None:
                target_vwc = target_vwc / 100.0
        if wilting_vwc is None and soil_type and soil_type in IC_SOIL_PARAMS:
            wilting_vwc = getattr(IC_SOIL_PARAMS[soil_type], 'wilting_point_vwc', None)

        # Fallback defaults
        if target_vwc is None:
            target_vwc = 0.28
        if wilting_vwc is None:
            wilting_vwc = 0.12

        # Basic moisture deficit risk
        if target_vwc <= wilting_vwc:
            # sanity fallback
            target_vwc = wilting_vwc + 0.1

        deficit = max(0.0, target_vwc - current_vwc)
        denom = max(1e-6, target_vwc - wilting_vwc)
        drought_base = (deficit / denom) * 100.0

        # ET0 and recent rain modifiers: the predictor signature doesn't include ET0/rain,
        # but callers can augment using crop-specific adjustments; we'll assume neutral ET0
        et0 = None
        recent_rain_mm = 0.0

        # ET0 factor: assume 4 mm/day baseline
        et0_factor = 1.0
        if et0 is not None:
            et0_factor = max(0.5, min(1.5, 1.0 + (et0 - 4.0) / 6.0))

        # Rain factor reduces risk
        rain_factor = max(0.0, 1.0 - (recent_rain_mm / 50.0))

        drought_risk = drought_base * et0_factor * rain_factor
        drought_risk = min(100.0, max(0.0, drought_risk))

        # Confidence: higher when we have moisture and crop/soil metadata
        confidence = 0.6
        if crop_type in CW_NEEDS:
            confidence += 0.1
        if soil_type in IC_SOIL_PARAMS:
            confidence += 0.05
        confidence = min(0.95, confidence)

        details = {
            'used_nearest': False,
            'used_custom': True,
            'current_moisture_pct': current_moisture,
            'target_vwc': round(target_vwc, 3),
            'wilting_vwc': round(wilting_vwc, 3),
            'deficit_vwc': round(deficit, 3),
            'et0_used_mm_per_day': et0,
            'recent_rain_mm': recent_rain_mm
        }

        return {
            'drought_risk': round(drought_risk, 2),
            'confidence': round(confidence, 2),
            'details': details
        }
"""Soil and water management agent with improved calculations."""
from typing import Dict, Any, Optional
import numpy as np
from ..utils.drought_predictor import DroughtPredictor
from ..utils.location_validator import validate_coordinates, validate_nearest_point
from ..utils.irrigation_calculator import (
    calculate_irrigation_need,
    SOIL_PARAMS,
    ROOT_DEPTHS,
    IRRIGATION_EFFICIENCY
)

class SoilWaterAgent:
    """Soil & Water Agent with drought prediction and irrigation calculation.
    
    Uses soil moisture history, ET0, and terrain/soil data to:
    1. Calculate current soil moisture and water deficit
    2. Assess drought risk using both moisture and terrain factors
    3. Recommend irrigation amounts based on root zone water balance
    """
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.drought_predictor = DroughtPredictor()

    async def run(self, input_data: Dict[str, Any]) -> Dict:
        """Process soil moisture data and recommend irrigation."""
        # Validate location first
        lat = input_data.get('latitude')
        lon = input_data.get('longitude')
        if lat is None or lon is None:
            return {
                "error": "Missing coordinates",
                "confidence": 0.1
            }
            
        valid, reason = validate_coordinates(lat, lon)
        if not valid:
            return {
                "error": reason,
                "confidence": 0.1
            }

        # Get input parameters with validation
        soil_type = input_data.get("soil_type", "clay")
        if soil_type not in SOIL_PARAMS:
            soil_type = "clay"  # Fallback to clay for UP region
            
        crop_type = input_data.get("crop_type", "rice")
        if crop_type not in ROOT_DEPTHS:
            crop_type = "rice"  # Fallback to rice
            
        growth_stage = input_data.get("growth_stage", "vegetative")
        if growth_stage not in ROOT_DEPTHS[crop_type]:
            growth_stage = "vegetative"

        # Process moisture history
        last_5 = input_data.get("last_5_days", []) or []
        values = [d.get("soil_moisture_pct") for d in last_5 if d.get("soil_moisture_pct") is not None]
        if not values:
            return {
                "error": "No soil moisture data available",
                "confidence": 0.1
            }
        
        # Convert percentage to volumetric water content
        current_vwc = sum(values) / len(values) / 100.0  # Convert % to fraction
        
        # Get ET0 and rainfall data
        et0 = None
        try:
            et0 = input_data.get("et0_override") or input_data.get("et0", {})
            if isinstance(et0, dict):
                et0 = et0.get("et0_mm_per_day")
        except Exception:
            et0 = 4.0  # fallback daily ET
            
        rain = sum([d.get("rainfall_mm") or d.get("precipitation", 0) for d in last_5])
        
        # Calculate irrigation needs using root zone method
        irrigation_result = calculate_irrigation_need(
            current_vwc=current_vwc,
            crop_type=crop_type,
            soil_type=soil_type,
            growth_stage=growth_stage,
            irrigation_mode="sprinkler",  # Will be adjusted for rice in vegetative stage
            et0_mm=et0
        )
        
        # Override irrigation mode for rice in vegetative stage
        if crop_type == "rice" and growth_stage == "vegetative":
            irrigation_result["irrigation_mode"] = "flood"
        
        # Get drought risk prediction with location validation
        drought_data = None
        if lat is not None and lon is not None:
            drought_data = self.drought_predictor.predict_drought_risk(
                lat=lat,
                lon=lon,
                current_moisture=current_vwc * 100,  # Convert back to percentage
                crop_type=crop_type,
                soil_type=soil_type
            )
            
            # Validate nearest point and use fallback if needed
            if drought_data and 'details' in drought_data:
                details = drought_data['details']
                if details.get('distance_km', 0) > 50:
                    # Reset to Lucknow coordinates
                    drought_data = self.drought_predictor.predict_drought_risk(
                        lat=26.8467,
                        lon=80.9462,
                        current_moisture=current_vwc * 100,
                        crop_type=crop_type,
                        soil_type=soil_type
                    )
        
        # Prepare the output with improved calculations
        output = {
            "avg_soil_moisture_pct": round(current_vwc * 100, 2),
            "rain_sum_mm": round(rain, 2),
            "et0_used_mm_per_day": round(et0, 2),
            "drought_risk": drought_data['drought_risk'] if drought_data else None,
            "drought_alert": irrigation_result["drought_alert"],
            "soil_data": drought_data['details'] if drought_data else None,
            "irrigation_needs": {
                "mode": irrigation_result["irrigation_mode"],
                "volume_mm": irrigation_result["irrigation_amount_mm"],
                "days_to_next": irrigation_result["days_to_next"]
            },
            "thresholds": irrigation_result["thresholds"],
            "root_zone": {
                "depth_mm": irrigation_result["root_depth_mm"],
                "efficiency": irrigation_result["efficiency"]
            }
        }
        
        # Calculate confidence with stricter rules
        base_confidence = 0.55 + min(0.3, 0.06 * len(values))
        
        # Reduce confidence for missing/questionable data
        if not et0 or et0 == 4.0:  # Using fallback ET0
            base_confidence = min(base_confidence, 0.5)
            
        # Reduce confidence for questionable location data    
        if drought_data and drought_data.get('details', {}).get('distance_km', 0) > 50:
            base_confidence = min(base_confidence, 0.4)
            
        # Factor in drought predictor confidence if available
        if drought_data and 'confidence' in drought_data:
            base_confidence = (base_confidence + drought_data['confidence']) / 2
            
        # Final confidence check
        final_confidence = min(0.9, base_confidence)
        if final_confidence < 0.5:
            output["warning"] = "Low confidence due to data quality issues"
            
        return {
            "output": output,
            "confidence": round(final_confidence, 2),
            "data_quality": {
                "moisture_data_points": len(values),
                "et0_quality": "fallback" if et0 == 4.0 else "actual",
                "location_quality": "fallback" if drought_data and drought_data.get('details', {}).get('distance_km', 0) > 50 else "actual"
            }
        }
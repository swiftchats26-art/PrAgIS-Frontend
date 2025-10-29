"""Soil and water management agent with improved calculations and consistent output."""
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
from ..utils.irrigation_modes import get_irrigation_mode, IRRIGATION_EFFICIENCY as MODES_EFF

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
        
        # Get irrigation mode from matrix first
        irrigation_mode = get_irrigation_mode(crop_type, soil_type)
        
        # Calculate irrigation needs using root zone method
        irrigation_result = calculate_irrigation_need(
            current_vwc=current_vwc,
            crop_type=crop_type,
            soil_type=soil_type,
            growth_stage=growth_stage,
            irrigation_mode=irrigation_mode,
            et0_mm=et0
        )
        
        # Special handling for rice flood irrigation
        if crop_type == "rice" and irrigation_mode == "flood":
            # Ensure minimum flood depth for rice
            irrigation_result["water_deficit_mm"] = max(
                irrigation_result["water_deficit_mm"],
                40.0  # Minimum flood depth for rice establishment
            )
        
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
            "drought_alert": irrigation_result["drought_alert"] or (drought_data and drought_data['drought_risk'] >= 30),
            "soil_data": drought_data['details'] if drought_data else None,
            "irrigation_needs": {
                "mode": irrigation_mode,
                "volume_mm": round(irrigation_result["water_deficit_mm"], 1),
                "days_to_next": irrigation_result["days_to_next"] if "days_to_next" in irrigation_result else None,
                "efficiency": MODES_EFF.get(irrigation_mode, IRRIGATION_EFFICIENCY.get(irrigation_mode, 0.6))
            },
            "root_zone": {
                "depth_mm": irrigation_result["root_depth_mm"],
                "current_vwc": round(current_vwc, 3),
                "target_vwc": round(irrigation_result["thresholds"]["target_vwc"], 3)
            },
            "thresholds": {
                "field_capacity_vwc": round(irrigation_result["thresholds"]["field_capacity"], 3),
                "critical_vwc": round(irrigation_result["thresholds"]["critical_point"], 3),
                "wilting_point_vwc": round(irrigation_result["thresholds"]["wilting_point"], 3)
            }
        }
        
        # Composite confidence calculation
        confidence_factors = {
            # Data availability confidence
            "moisture_data": {
                "weight": 0.3,
                "value": min(1.0, 0.4 + 0.12 * len(values))  # Scales with number of readings
            },
            # ET0 quality confidence
            "et0": {
                "weight": 0.2,
                "value": 0.95 if (et0 and et0 != 4.0) else 0.4  # High for actual ET0, low for fallback
            },
            # Location quality confidence
            "location": {
                "weight": 0.2,
                "value": 0.3 if (drought_data and drought_data.get('details', {}).get('distance_km', 0) > 50) else 0.9
            },
            # Drought prediction confidence
            "drought": {
                "weight": 0.15,
                "value": drought_data.get('confidence', 0.5) if drought_data else 0.4
            },
            # Soil parameters confidence
            "soil": {
                "weight": 0.15,
                "value": 0.8 if soil_type in SOIL_PARAMS else 0.4  # High for known soil types
            }
        }
        
        # Calculate weighted average confidence
        total_weight = sum(f["weight"] for f in confidence_factors.values())
        weighted_confidence = sum(
            f["weight"] * f["value"] for f in confidence_factors.values()
        ) / total_weight
        
        # Cap final confidence and add warning if low
        final_confidence = min(0.95, weighted_confidence)
        if final_confidence < 0.5:
            output["warning"] = "Low confidence due to data quality issues"
            
        # Store confidence factors for transparency
        output["confidence_factors"] = {
            k: {"value": v["value"], "weight": v["weight"]} 
            for k, v in confidence_factors.items()
        }
            
        return {
            "output": output,
            "confidence": round(final_confidence, 2),
            "data_quality": {
                "moisture_data_points": len(values),
                "et0_quality": "fallback" if et0 == 4.0 else "actual",
                "location_quality": "fallback" if drought_data and drought_data.get('details', {}).get('distance_km', 0) > 50 else "actual"
            }
        }
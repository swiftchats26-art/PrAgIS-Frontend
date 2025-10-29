"""Calculate irrigation requirements based on root zone water balance."""
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class SoilParams:
    """Soil water holding parameters."""
    field_capacity_vwc: float  # Volumetric water content at field capacity
    wilting_point_vwc: float  # Volumetric water content at wilting point
    critical_vwc: float       # Critical VWC below which stress occurs
    target_vwc: float        # Target VWC for irrigation
    max_vwc: float          # Maximum VWC (saturation)

# Soil parameters by texture class (all values in volumetric water content)
SOIL_PARAMS = {
    "clay": SoilParams(
        field_capacity_vwc=0.40,  # 40%
        wilting_point_vwc=0.20,   # 20%
        critical_vwc=0.30,        # 30%
        target_vwc=0.35,          # 35%
        max_vwc=0.50             # 50%
    ),
    "loam": SoilParams(
        field_capacity_vwc=0.35,  # 35%
        wilting_point_vwc=0.12,   # 12%
        critical_vwc=0.22,        # 22%
        target_vwc=0.28,          # 28%
        max_vwc=0.45             # 45%
    ),
    "sandy": SoilParams(
        field_capacity_vwc=0.20,  # 20%
        wilting_point_vwc=0.08,   # 8%
        critical_vwc=0.12,        # 12%
        target_vwc=0.16,          # 16%
        max_vwc=0.35             # 35%
    )
}

# Root zone depths by crop and growth stage (mm)
ROOT_DEPTHS = {
    "wheat": {
        "initial": 150,
        "vegetative": 300,
        "reproductive": 400,
        "ripening": 400
    },
    "rice": {
        "initial": 150,
        "vegetative": 200,
        "reproductive": 250,
        "ripening": 250
    }
}

# Irrigation efficiency by method
IRRIGATION_EFFICIENCY = {
    "flood": 0.7,
    "sprinkler": 0.85,
    "drip": 0.95
}

def calculate_irrigation_need(
    current_vwc: float,
    crop_type: str,
    soil_type: str,
    growth_stage: str,
    irrigation_mode: str,
    et0_mm: Optional[float] = None
) -> Dict:
    """Calculate irrigation requirement using root zone method.
    
    Args:
        current_vwc: Current volumetric water content (as fraction)
        crop_type: Crop type (e.g., "wheat", "rice")
        soil_type: Soil texture class
        growth_stage: Current growth stage
        irrigation_mode: Irrigation method
        et0_mm: Reference evapotranspiration (mm/day)
    
    Returns:
        Dict with irrigation recommendations and diagnostics
    """
    if soil_type not in SOIL_PARAMS:
        raise ValueError(f"Unknown soil type: {soil_type}")
    if crop_type not in ROOT_DEPTHS:
        raise ValueError(f"Unknown crop type: {crop_type}")
        
    soil = SOIL_PARAMS[soil_type]
    root_depth = ROOT_DEPTHS[crop_type][growth_stage]
    efficiency = IRRIGATION_EFFICIENCY[irrigation_mode]
    
    # Calculate water deficit based on target VWC
    target_vwc = soil.target_vwc
    if current_vwc >= target_vwc:
        # No deficit if current moisture exceeds target
        deficit_vwc = 0.0 
    else:
        deficit_vwc = target_vwc - current_vwc
    
    # Calculate required water depth
    water_needed_mm = deficit_vwc * root_depth
    
    # Account for irrigation efficiency
    # If no deficit, no irrigation required
    if water_needed_mm <= 0:
        water_needed_mm = 0.0
        applied_water_mm = 0.0
        needs_irrigation = False
    else:
        # Account for irrigation efficiency
        applied_water_mm = water_needed_mm / efficiency
        needs_irrigation = True
    
    # Calculate days until next irrigation
    days_to_next = None
    if et0_mm:
        # Assume 70% of ET0 is actual ET
        daily_depletion = et0_mm * 0.7
    if et0_mm and water_needed_mm > 0:
        # Assume 70% of ET0 is actual ET
        daily_depletion = et0_mm * 0.7
        if daily_depletion > 0:
            days_to_next = round(water_needed_mm / daily_depletion, 1)
        else:
            days_to_next = None
    
    # Determine if immediate irrigation needed (kept from earlier calculation)
    
    # Calculate drought risk based on critical point
    is_below_critical = current_vwc < soil.critical_vwc
    if is_below_critical:
        # Calculate severity based on how far below critical point
        severity = (soil.critical_vwc - current_vwc) / (soil.critical_vwc - soil.wilting_point_vwc)
        drought_risk = min(100, severity * 100)
    else:
        drought_risk = 0.0
    
    return {
        "irrigation_needed": needs_irrigation,
        "water_deficit_mm": round(max(0.0, water_needed_mm), 1),
        "irrigation_amount_mm": round(max(0.0, applied_water_mm), 1),
        "days_to_next": days_to_next,
        "drought_risk": round(drought_risk, 1),
        "drought_alert": is_below_critical,  # Direct boolean based on critical threshold
        "thresholds": {
            "current_vwc": round(current_vwc, 3),
            "field_capacity": round(soil.field_capacity_vwc, 3),
            "critical_point": round(soil.critical_vwc, 3),
            "wilting_point": round(soil.wilting_point_vwc, 3),
            "target_vwc": round(soil.target_vwc, 3)
        },
        "root_depth_mm": root_depth,
        "efficiency": efficiency
    }
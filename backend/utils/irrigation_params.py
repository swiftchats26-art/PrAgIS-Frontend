"""Soil moisture and irrigation constants for different crops and soil types."""
from typing import Dict, Any

# Field capacity and wilting points by soil type (%)
SOIL_MOISTURE_LIMITS = {
    "clay": {
        "field_capacity": 40.0,
        "wilting_point": 20.0,
        "retention_factor": 0.6
    },
    "sandy": {
        "field_capacity": 25.0,
        "wilting_point": 10.0,
        "retention_factor": 0.3
    }
}

# Crop-specific moisture needs and irrigation preferences
CROP_WATER_NEEDS = {
    "rice": {
        "min_moisture": 35.0,  # minimum for healthy growth
        "optimal_moisture": 45.0,  # saturated/flooded
        "drought_threshold": 30.0,  # below this = high drought risk
        "preferred_mode": "flood",
        "stage_factors": {
            "vegetative": 1.2,  # needs more water in vegetative stage
            "reproductive": 1.1,
            "ripening": 0.9
        }
    },
    "wheat": {
        "min_moisture": 25.0,
        "optimal_moisture": 35.0,
        "drought_threshold": 20.0,
        "preferred_mode": "sprinkler",
        "stage_factors": {
            "vegetative": 1.0,
            "reproductive": 1.1,
            "ripening": 0.8
        }
    },
    "maize": {
        "min_moisture": 30.0,
        "optimal_moisture": 40.0,
        "drought_threshold": 25.0,
        "preferred_mode": "drip",
        "stage_factors": {
            "vegetative": 1.1,
            "reproductive": 1.2,
            "ripening": 0.9
        }
    }
}

def get_drought_risk(current_moisture: float, crop_type: str, soil_type: str) -> float:
    """Calculate drought risk based on current moisture vs. crop and soil needs.
    
    Returns risk percentage (0-100). Above 70% indicates severe drought risk.
    """
    soil_limits = SOIL_MOISTURE_LIMITS[soil_type]
    crop_needs = CROP_WATER_NEEDS[crop_type]
    
    # How far below minimum moisture are we?
    moisture_deficit = max(0, crop_needs["min_moisture"] - current_moisture)
    
    # Scale against the gap between wilting point and minimum needed
    moisture_range = crop_needs["min_moisture"] - soil_limits["wilting_point"]
    
    if moisture_range <= 0:
        return 100 if current_moisture < soil_limits["wilting_point"] else 0
        
    # Base risk on how close to wilting point we are
    base_risk = min(100, (moisture_deficit / moisture_range) * 100)
    
    # Increase risk if we're below wilting point
    if current_moisture < soil_limits["wilting_point"]:
        deficit_vs_wilting = soil_limits["wilting_point"] - current_moisture
        base_risk = min(100, base_risk + (deficit_vs_wilting * 5))
        
    return round(base_risk, 1)

def get_irrigation_needs(
    et0: float,
    current_moisture: float,
    crop_type: str,
    soil_type: str,
    growth_stage: str,
    farm_area_ha: float
) -> Dict[str, Any]:
    """Calculate irrigation volume and mode based on crop-specific needs."""
    soil_limits = SOIL_MOISTURE_LIMITS[soil_type]
    crop_needs = CROP_WATER_NEEDS[crop_type]
    
    # Base need from ET0
    base_volume = et0 * 1.1  # slightly over ET0 to account for inefficiencies
    
    # Adjust for how far we are from optimal moisture
    moisture_deficit = crop_needs["optimal_moisture"] - current_moisture
    if moisture_deficit > 0:
        # Add deficit scaled by soil retention
        base_volume += (moisture_deficit * soil_limits["retention_factor"])
    
    # Apply growth stage factor
    stage_factor = crop_needs["stage_factors"].get(growth_stage, 1.0)
    base_volume *= stage_factor
    
    # Rice-specific adjustments
    if crop_type == "rice":
        # Rice needs flooding in vegetative stage unless AWD
        if growth_stage == "vegetative" and current_moisture < 35.0:
            base_volume = max(base_volume, 25.0)  # minimum flood depth
    
    # Select irrigation mode
    mode = crop_needs["preferred_mode"]
    if mode == "flood" and farm_area_ha <= 2.0:
        # Small farms might use sprinkler even for rice
        mode = "sprinkler"
    
    return {
        "volume_mm": round(base_volume, 1),
        "mode": mode
    }
"""Define irrigation mode selection matrix and efficiency factors."""

# Irrigation mode matrix by crop and soil type
IRRIGATION_MODE_MATRIX = {
    "rice": {
        "default": "flood",  # Rice always prefers flood irrigation
        "clay": "flood",
        "loam": "flood", 
        "sandy": "flood"
    },
    "wheat": {
        "default": "sprinkler",
        "clay": "sprinkler",
        "loam": "sprinkler",
        "sandy": "sprinkler"
    },
    "maize": {
        "default": "drip",  # Maize prefers precision irrigation
        "clay": "furrow",   # But use furrow on clay due to soil characteristics
        "loam": "drip",
        "sandy": "drip"     # Essential on sandy to prevent losses
    }
}

# Irrigation efficiency by method (as decimal)
IRRIGATION_EFFICIENCY = {
    "flood": 0.70,   # 70% efficiency - traditional surface flooding
    "furrow": 0.75,  # 75% efficiency - improved surface method
    "sprinkler": 0.85,  # 85% efficiency - pressurized sprinkler systems
    "drip": 0.95    # 95% efficiency - precision drip irrigation
}

def get_irrigation_mode(crop_type: str, soil_type: str) -> str:
    """Get the recommended irrigation mode for a crop-soil combination.
    
    Args:
        crop_type: The type of crop (e.g., "rice", "wheat", "maize")
        soil_type: The soil texture class (e.g., "clay", "loam", "sandy")
        
    Returns:
        str: The recommended irrigation mode
    """
    crop_modes = IRRIGATION_MODE_MATRIX.get(crop_type, {})
    # Try specific soil type first, fall back to default
    return crop_modes.get(soil_type, crop_modes.get("default", "sprinkler"))
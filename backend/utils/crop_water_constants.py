"""Constants for crop-specific water requirements and thresholds."""

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
    },
    "loam": {
        "field_capacity": 35.0,
        "wilting_point": 15.0,
        "retention_factor": 0.5
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
    }
}
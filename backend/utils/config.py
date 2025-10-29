from typing import Dict

# Configurable weights for DecisionAgent. These should reflect real-world weighting
# but are placeholders until you supply exact IRL weights. They sum to 1.0.
DEFAULT_AGENT_WEIGHTS: Dict[str, float] = {
    "climate": 0.25,
    "soil_water": 0.25,
    "crop_growth": 0.25,
    "et0": 0.25,
}

# Redis defaults for local development
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# Default irrigation mode thresholds (hectares)
DRIP_MAX_AREA_HA = 2.0

# LLM integration placeholder
LLM_ENABLED = False
LLM_PROVIDER = ""
LLM_API_KEY = ""

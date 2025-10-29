from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from typing import Optional
import uuid
from fastapi.middleware.cors import CORSMiddleware

from .schemas.farm_input import FarmInput
from .schemas.irrigation_output import IrrigationOutput
from .db.redis_client import RedisClient
from .orchestrator.orchestrator import Orchestrator
from .utils.llm_client import LLMClient
from .utils.config import DEFAULT_AGENT_WEIGHTS
from .utils.logger import get_logger

logger = get_logger()

app = FastAPI(title="PrAgIS - Multi-Agent Precision Irrigation System")

# Enable CORS for frontend during development. Update allowed origins as needed.
# Allow frontend dev servers (Vite) on common ports. Add 5174 because Vite may auto-pick an alternate port.
origins = [
    "http://localhost:5173",
    "http://localhost:5173/",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize a single Redis client instance for the app
redis_client = RedisClient()
llm_client = LLMClient()
orchestrator = Orchestrator(redis_client=redis_client, llm_client=llm_client, weights=DEFAULT_AGENT_WEIGHTS)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting PrAgIS backend - connecting Redis")
    try:
        await redis_client.connect()
    except Exception as e:
        logger.warning(f"Redis connect failed at startup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    await redis_client.close()


@app.get("/status")
async def status():
    return {"status": "ok"}


@app.get("/mock-data")
async def mock_data():
    # Returns an example input schema (no real mock files per user request)
    example = {
        "request_uuid": "<optional - server will generate if missing>",
        "farm_id": "farm-123",
        "crop_type": "wheat",
        "soil_type": "sandy",
        "sowing_date": "2025-09-01",
        "farm_area_ha": 1.5,
        "last_5_days": [
            {"date": "2025-10-22", "rainfall_mm": 0.0, "tmax_c": 28.0, "tmin_c": 18.0, "soil_moisture_pct": 32.0},
        ],
    }
    return JSONResponse(content=example)


@app.post("/predict-schedule", response_model=IrrigationOutput)
async def predict_schedule(payload: dict):
    try:
        fi = FarmInput(**payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    # ensure request uuid
    request_uuid = fi.request_uuid or str(uuid.uuid4())
    data = fi.dict()
    data["request_uuid"] = request_uuid

    # run orchestrator
    result = await orchestrator.run(data)
    
    # Debug logging
    logger.info(f"Orchestrator result: {result}")
    logger.info(f"Irrigation volume from orchestrator: {result.get('irrigation_volume_mm')}")

    # shape into output schema
    # normalize confidence naming: accept either 'confidence_score' or 'confidence'
    confidence_score = result.get("confidence") if result.get("confidence") is not None else result.get("confidence_score", 0.0)

    # Calculate days after sowing
    from datetime import datetime
    sowing_date = datetime.combine(data["sowing_date"], datetime.min.time())
    current_date = datetime.now()
    days_after_sowing = (current_date - sowing_date).days

    # Get yield index from result or calculate based on available data
    yield_index = result.get("yield_index", 0.85)  # Default to 0.85 if not provided

    # Get irrigation volume from soil water agent first, then fall back to decision agent
    irrigation_volume = 0.0
    soil_water = result.get("agents", {}).get("soil_water", {}).get("output", {})
    if soil_water and soil_water.get("irrigation_needs"):
        irrigation_volume = soil_water["irrigation_needs"].get("volume_mm", 0.0)
    else:
        irrigation_volume = result.get("irrigation_volume_mm", 0.0)

    logger.info(f"Final irrigation volume: {irrigation_volume}")
    
    soil_water_agent = result.get("agents", {}).get("soil_water", {})
    logger.info("Soil Water Agent Output:")
    logger.info(str(soil_water_agent))

    if isinstance(soil_water_agent, dict) and "output" in soil_water_agent:
        irrigation_needs = soil_water_agent["output"].get("irrigation_needs", {})
        logger.info("Irrigation Needs from Soil Water Agent:")
        logger.info(str(irrigation_needs))
        irrigation_volume = irrigation_needs.get("volume_mm", 0.0)
    else:
        irrigation_volume = 0.0

    logger.info(f"Final Irrigation Volume: {irrigation_volume}")

    out = {
        "irrigation_volume_mm": float(irrigation_volume),
        "irrigation_mode": result.get("irrigation_mode", "drip"),
        "confidence_score": confidence_score,
        "short_reasoning": result.get("short_reasoning", ""),
        "days_after_sowing": days_after_sowing,
        "yield_index": yield_index,
        "agents": result.get("agents", {}),
    }

    logger.info("Final API Response:")
    logger.info(str(out))

    return out

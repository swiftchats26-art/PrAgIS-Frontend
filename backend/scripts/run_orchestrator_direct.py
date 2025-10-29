import asyncio
import sys
from backend.db.redis_client import RedisClient
from backend.utils.llm_client import LLMClient
from backend.orchestrator.orchestrator import Orchestrator

payload = {
    "farm_id": "test-wheat-1",
    "crop_type": "wheat",
    "soil_type": "sandy",
    "sowing_date": "2025-09-20",
    "latitude": 28.0,
    "longitude": 77.0,
    "farm_area_ha": 1.8,
    "last_5_days": [
        {"date": "2025-10-23", "rainfall_mm": 0.0, "tmax_c": 32.0, "tmin_c": 20.0, "soil_moisture_pct": 15.0},
        {"date": "2025-10-24", "rainfall_mm": 0.0, "tmax_c": 32.5, "tmin_c": 20.2, "soil_moisture_pct": 14.5},
        {"date": "2025-10-25", "rainfall_mm": 0.0, "tmax_c": 33.0, "tmin_c": 20.5, "soil_moisture_pct": 14.0},
        {"date": "2025-10-26", "rainfall_mm": 0.0, "tmax_c": 33.2, "tmin_c": 20.7, "soil_moisture_pct": 13.8},
        {"date": "2025-10-27", "rainfall_mm": 0.0, "tmax_c": 33.5, "tmin_c": 21.0, "soil_moisture_pct": 13.5},
    ],
}

async def main():
    rc = RedisClient()
    llm = LLMClient()
    orchestrator = Orchestrator(redis_client=rc, llm_client=llm)
    try:
        print('Running orchestrator directly...')
        out = await orchestrator.run(payload)
        print('Result:', out)
    except Exception as e:
        print('ORCHESTRATOR ERROR:', repr(e))
        raise

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))

import asyncio
import json
import sys
from datetime import date
from ..db.redis_client import RedisClient
from ..utils.llm_client import LLMClient
from ..orchestrator.orchestrator import Orchestrator


def make_input():
    return {
        "farm_id": "test-farm-1",
        "crop_type": "rice",
        "soil_type": "clay",
        "sowing_date": "2025-10-01",
        "latitude": 26.8467,
        "longitude": 80.9462,
        "farm_area_ha": 1.0,
        "last_5_days": [
            {"date": "2025-10-23", "rainfall_mm": 0.0, "tmax_c": 30.0, "tmin_c": 22.0, "soil_moisture_pct": 28.0}
        ]
    }


async def main():
    redis = RedisClient()
    llm = LLMClient()
    orch = Orchestrator(redis_client=redis, llm_client=llm)

    fi = make_input()
    try:
        out = await orch.run(fi)
        print(json.dumps(out, indent=2, default=str))
    except Exception as e:
        print("ERROR while running orchestrator:", e)


if __name__ == '__main__':
    asyncio.run(main())

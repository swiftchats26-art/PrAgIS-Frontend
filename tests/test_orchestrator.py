import asyncio


def test_orchestrator_runs_end_to_end():
    from backend.orchestrator.orchestrator import Orchestrator
    from backend.utils.llm_client import LLMClient

    # Create a fake Redis client with async set_json to avoid external dependency
    class FakeRedis:
        async def connect(self):
            return None

        async def set_json(self, request_uuid, name, value):
            return None

        async def get_json(self, request_uuid, name):
            return None

        async def close(self):
            return None

    fake_redis = FakeRedis()
    llm = LLMClient()
    orch = Orchestrator(redis_client=fake_redis, llm_client=llm)

    payload = {
        "request_uuid": "test-1",
        "farm_id": "farm-1",
        "crop_type": "wheat",
        "soil_type": "sandy",
        "sowing_date": "2025-09-01",
        "farm_area_ha": 1.5,
        "last_5_days": [
            {"date": "2025-10-22", "rainfall_mm": 0.0, "tmax_c": 28.0, "tmin_c": 18.0, "soil_moisture_pct": 32.0},
            {"date": "2025-10-23", "rainfall_mm": 0.0, "tmax_c": 27.0, "tmin_c": 17.0, "soil_moisture_pct": 31.5},
        ],
    }

    out = asyncio.run(orch.run(payload))
    assert "irrigation_volume_mm" in out and "irrigation_mode" in out

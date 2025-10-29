import asyncio


def test_climate_agent_runs():
    from backend.agents.climate_agent import ClimateAgent

    data = {
        "last_5_days": [
            {"tmax_c": 25.0, "tmin_c": 15.0, "rainfall_mm": 0.0},
            {"tmax_c": 26.0, "tmin_c": 16.0, "rainfall_mm": 1.0},
        ]
    }
    out = asyncio.run(ClimateAgent().run(data))
    assert isinstance(out, dict)
    assert "output" in out and "confidence" in out


def test_soil_water_agent_runs():
    from backend.agents.soil_water_agent import SoilWaterAgent

    data = {"last_5_days": [{"soil_moisture_pct": 30.0}, {"soil_moisture_pct": 32.0}]}
    out = asyncio.run(SoilWaterAgent().run(data))
    assert "output" in out and "confidence" in out


def test_crop_growth_agent_runs():
    from backend.agents.crop_growth_agent import CropGrowthAgent
    data = {"sowing_date": "2025-09-01"}
    out = asyncio.run(CropGrowthAgent().run(data))
    assert "output" in out and "confidence" in out


def test_et0_agent_runs():
    from backend.agents.et0_agent import ET0Agent
    data = {"last_5_days": [{"tmax_c": 30.0}, {"tmax_c": 28.0}]}
    out = asyncio.run(ET0Agent().run(data))
    assert "output" in out and "confidence" in out


def test_decision_agent_basic():
    from backend.agents.decision_agent import DecisionAgent

    agents_outputs = {
        "climate": {"output": {}, "confidence": 0.9},
        "soil_water": {"output": {"avg_soil_moisture_pct": 30.0}, "confidence": 0.8},
        "crop_growth": {"output": {}, "confidence": 0.85},
        "et0": {"output": {"et0_mm_per_day": 5.0}, "confidence": 0.9},
    }
    farm_input = {"farm_area_ha": 1.0}
    out = asyncio.run(DecisionAgent().run(agents_outputs, farm_input))
    assert "irrigation_volume_mm" in out and "irrigation_mode" in out

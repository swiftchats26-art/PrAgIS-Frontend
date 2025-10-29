import asyncio
import sys
from typing import Any, Dict
import httpx

async def main():
    url = "http://localhost:8000/predict-schedule"
    payload: Dict[str, Any] = {
        "farm_id": "test-wheat-1",
        "crop_type": "wheat",
        "soil_type": "sandy",
        "sowing_date": "2025-09-20",
        "latitude": 28.0,
        "longitude": 77.0,
        "farm_area_ha": 1.8,
        # Optional: small synthetic last_5_days to help agents
        "last_5_days": [
            {"date": "2025-10-23", "rainfall_mm": 0.0, "tmax_c": 32.0, "tmin_c": 20.0, "soil_moisture_pct": 15.0},
            {"date": "2025-10-24", "rainfall_mm": 0.0, "tmax_c": 32.5, "tmin_c": 20.2, "soil_moisture_pct": 14.5},
            {"date": "2025-10-25", "rainfall_mm": 0.0, "tmax_c": 33.0, "tmin_c": 20.5, "soil_moisture_pct": 14.0},
            {"date": "2025-10-26", "rainfall_mm": 0.0, "tmax_c": 33.2, "tmin_c": 20.7, "soil_moisture_pct": 13.8},
            {"date": "2025-10-27", "rainfall_mm": 0.0, "tmax_c": 33.5, "tmin_c": 21.0, "soil_moisture_pct": 13.5},
        ],
    }

    print("Sending payload to backend /predict-schedule:\n", payload)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            print(f"Response status: {resp.status_code}")
            text = await resp.aread()
            try:
                # try decode as json
                import json as _json
                parsed = _json.loads(text)
                print("\nResponse JSON:\n", parsed)
            except Exception:
                print("\nResponse text:\n", text.decode(errors='replace'))
            if resp.status_code >= 400:
                return 1
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))

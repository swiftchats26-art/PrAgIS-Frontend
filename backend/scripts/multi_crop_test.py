"""Multi-crop test harness.

This script accepts a JSON file of test cases or runs built-in examples. Each case should include:
  - crop_type (e.g., "wheat", "rice")
  - soil_type (e.g., "loam", "clay", "sandy")
  - sowing_date (YYYY-MM-DD)
  - farm_area_ha (float)
  - latitude, longitude (floats)

Example usage:
  python -m backend.scripts.multi_crop_test --cases-file ./tests/cases.json

If no file is provided the script will run a small set of example cases.
"""
import argparse
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any

from ..agents.soil_water_agent_v3 import SoilWaterAgent
from ..agents.decision_agent import DecisionAgent


def make_default_last5(current_moisture_pct: float) -> List[Dict[str, Any]]:
    # Create a simple declining last-5-days moisture sequence
    return [
        {
            "date": (datetime.utcnow()).strftime("%Y-%m-%d"),
            "soil_moisture_pct": max(1.0, current_moisture_pct - i * 0.5),
            "rainfall_mm": 0.0
        }
        for i in range(5)
    ]


async def run_case(case: Dict[str, Any]) -> Dict[str, Any]:
    soil_agent = SoilWaterAgent()
    decision_agent = DecisionAgent()

    # Fill defaults
    crop_type = case.get("crop_type", "wheat")
    soil_type = case.get("soil_type", "loam")
    sowing_date = case.get("sowing_date")
    farm_area = case.get("farm_area_ha", 1.0)
    lat = case.get("latitude", 26.8467)
    lon = case.get("longitude", 80.9462)

    # days since sowing
    try:
        days_since_sowing = None
        if sowing_date:
            sd = datetime.strptime(sowing_date, "%Y-%m-%d")
            days_since_sowing = (datetime.utcnow() - sd).days
    except Exception:
        days_since_sowing = None

    # Provide a plausible current moisture if not provided
    current_moisture_pct = case.get("current_moisture_pct", 22.0)
    last_5 = case.get("last_5_days") or make_default_last5(current_moisture_pct)

    et0 = case.get("et0") or {"et0_mm_per_day": 4.0}

    farm_input = {
        "latitude": lat,
        "longitude": lon,
        "crop_type": crop_type,
        "soil_type": soil_type,
        "growth_stage": case.get("growth_stage", "vegetative"),
        "days_since_planting": days_since_sowing,
        "farm_area_ha": farm_area,
        "last_5_days": last_5,
        "et0": et0
    }

    soil_result = await soil_agent.run(farm_input)

    # Prepare decision agent input
    try:
        decision_input = {**farm_input, "soil_analysis": soil_result.get("output")}
        # Pass full soil_result (including confidence) to DecisionAgent
        decision_result = await decision_agent.run(farm_input=decision_input, agents_outputs={"soil_water": soil_result})
    except TypeError:
        # Fallback if decision agent has a different signature
        decision_result = await decision_agent.run(farm_input=decision_input)
    except Exception as e:
        decision_result = {"error": str(e)}

    # Consistency checks
    inconsistencies = []
    try:
        soil_vol = None
        dec_vol = None
        if soil_result and isinstance(soil_result, dict):
            out = soil_result.get("output") or {}
            soil_vol = out.get("irrigation_needs", {}).get("volume_mm")
            soil_mode = out.get("irrigation_needs", {}).get("mode")
            soil_conf = soil_result.get("confidence")
        if decision_result and isinstance(decision_result, dict):
            # DecisionAgent sometimes returns output key; tolerate both
            dec_out = decision_result.get("output") or decision_result
            dec_vol = dec_out.get("irrigation_volume_mm") or dec_out.get("irrigation_volume") or dec_out.get("irrigation_volume_mm_per_event")
            dec_mode = dec_out.get("irrigation_mode")
            dec_conf = dec_out.get("confidence_score") or dec_out.get("confidence")
            # ET0 propagation check
            et0_in = farm_input.get('et0') if 'farm_input' in locals() else None
        # Volume mismatch
        if soil_vol is not None and dec_vol is not None:
            if abs(float(soil_vol) - float(dec_vol)) > 5.0:
                inconsistencies.append(f"Irrigation volume mismatch: soil_agent={soil_vol} mm vs decision={dec_vol} mm")
            if float(dec_vol) == 0 and float(soil_vol) > 0:
                inconsistencies.append("DecisionAgent returned zero irrigation while SoilAgent recommended >0")
        # Mode mismatch
        if 'soil_mode' in locals() and 'dec_mode' in locals():
            if soil_mode and dec_mode and soil_mode != dec_mode:
                inconsistencies.append(f"Irrigation mode mismatch: soil_agent={soil_mode} vs decision={dec_mode}")
        # Confidence mismatch
        if 'soil_conf' in locals() and 'dec_conf' in locals() and soil_conf is not None and dec_conf is not None:
            try:
                if abs(float(soil_conf) - float(dec_conf)) > 0.25:
                    inconsistencies.append(f"Confidence mismatch: soil={soil_conf} vs decision={dec_conf}")
            except Exception:
                pass
        # ET0 mismatch
        if et0_in is not None:
            # If decision reasoning contained ET0=0.0 still, flag
            if isinstance(decision_result, dict) and 'short_reasoning' in decision_result:
                if 'ET0=0.0' in decision_result['short_reasoning']:
                    inconsistencies.append('DecisionAgent reasoning shows ET0=0.0 despite input ET0 present')
    except Exception:
        pass

    return {
        "case": case,
        "soil_result": soil_result,
        "decision_result": decision_result,
        "inconsistencies": inconsistencies
    }


async def main(args):
    cases = None
    if args.cases_file:
        with open(args.cases_file, 'r') as f:
            cases = json.load(f)
    else:
        # Example cases
        cases = [
            {
                "crop_type": "wheat",
                "soil_type": "loam",
                "sowing_date": "2025-09-22",
                "farm_area_ha": 2.5,
                "latitude": 26.8467,
                "longitude": 80.9462,
                "current_moisture_pct": 13.5
            },
            {
                "crop_type": "rice",
                "soil_type": "clay",
                "sowing_date": "2025-07-01",
                "farm_area_ha": 1.2,
                "latitude": 26.8467,
                "longitude": 80.9462,
                "current_moisture_pct": 28.0
            },
            {
                "crop_type": "maize",
                "soil_type": "sandy",
                "sowing_date": "2025-06-15",
                "farm_area_ha": 3.0,
                "latitude": 26.8467,
                "longitude": 80.9462,
                "current_moisture_pct": 20.0
            }
        ]

    results = []
    for case in cases:
        print(f"\n--- Running case: {case.get('crop_type')} on {case.get('soil_type')} ---")
        res = await run_case(case)
        print(json.dumps(res, indent=2, default=str))
        results.append(res)

    if args.outfile:
        with open(args.outfile, 'w') as f:
            json.dump(results, f, indent=2, default=str)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run multi-crop tests')
    parser.add_argument('--cases-file', help='JSON file with list of cases')
    parser.add_argument('--outfile', help='Optional output file to write results')
    args = parser.parse_args()
    asyncio.run(main(args))
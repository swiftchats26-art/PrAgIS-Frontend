"""Test script for wheat crop prediction with sandy loam soil."""
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from ..agents.decision_agent import DecisionAgent
from ..agents.soil_water_agent_v2 import SoilWaterAgent  # Using improved agent

async def main():
    # Initialize agents
    soil_agent = SoilWaterAgent()
    decision_agent = DecisionAgent()
    
    # Test data for wheat in UP (planted Sept 22, 2025)
    planting_date = datetime(2025, 9, 22)
    current_date = datetime(2025, 10, 28)  # Today
    days_since_planting = (current_date - planting_date).days
    
    # Wheat is in vegetative stage (tillering) at ~36 days
    test_data = {
        "latitude": 26.8467,    # UP coordinates
        "longitude": 80.9462,
        "crop_type": "wheat",
        "soil_type": "loam",    # Sandy loam to clay loam is ideal for wheat
        "growth_stage": "vegetative",
        "days_since_planting": days_since_planting,
        "farm_area_ha": 2.5,
        "last_5_days": [
            {
                "date": (current_date - timedelta(days=i)).strftime("%Y-%m-%d"),
                "soil_moisture_pct": 22.0 - (i * 0.5),  # Declining moisture
                "rainfall_mm": 0.0 if i > 2 else 2.0,   # Light rain 3 days ago
                "max_temp_c": 28 + (i % 2),            # Typical UP October temps
                "min_temp_c": 15 + (i % 2)
            }
            for i in range(5)
        ],
        "et0": {
            "et0_mm_per_day": 4.2  # Higher ET0 due to dry October weather
        }
    }
    
    print("\n=== Testing Wheat Crop Management ===")
    print(f"Planting Date: {planting_date.strftime('%Y-%m-%d')}")
    print(f"Current Date: {current_date.strftime('%Y-%m-%d')}")
    print(f"Days Since Planting: {days_since_planting}")
    print("\n1. Soil Moisture Analysis:")
    
    # Get soil moisture analysis
    soil_result = await soil_agent.run(test_data)
    print(json.dumps(soil_result["output"], indent=2))
    
    print("\n2. Decision Agent Analysis:")
    
    # Get irrigation decision
    test_data["soil_analysis"] = soil_result["output"]
    decision_result = await decision_agent.run(
        farm_input=test_data,
        agents_outputs={"soil_water": soil_result["output"]}
    )
    print(json.dumps(decision_result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
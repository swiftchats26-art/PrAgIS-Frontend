import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List

import httpx

def generate_last_5_days() -> List[Dict[str, Any]]:
    """Generate realistic 5-day history for North India October weather."""
    days = []
    base_date = datetime(2025, 10, 23)  # 5 days before current test date
    
    # Realistic values for late October in UP/Bihar rice belt
    for i in range(5):
        date = base_date + timedelta(days=i)
        days.append({
            "date": date.strftime("%Y-%m-%d"),
            "rainfall_mm": 0.0 if i != 2 else 2.5,  # small rain on middle day
            "tmax_c": 30.0 + (i * 0.5),  # slight warming trend
            "tmin_c": 18.0 + (i * 0.3),  # nights also warming
            "soil_moisture_pct": 35.0 - (i * 0.8)  # gradual drying
        })
    return days

def make_test_payload() -> Dict[str, Any]:
    """Create a realistic test payload for rice farming in UP."""
    return {
        "farm_id": "test-farm-1",
        "crop_type": "rice",  # late rice crop
        "soil_type": "clay",  # typical UP rice soil
        "sowing_date": "2025-10-01",
        "latitude": 26.8467,  # Lucknow area coordinates
        "longitude": 80.9462,
        "farm_area_ha": 1.0,
        "last_5_days": generate_last_5_days()
    }

def analyze_response(resp: Dict[str, Any]) -> str:
    """Generate human-readable analysis of the orchestrator response."""
    lines = []
    
    # Overall decision
    lines.append("\n=== Irrigation Decision ===")
    lines.append(f"Recommended: {resp['irrigation_volume_mm']:.1f}mm via {resp['irrigation_mode']}")
    lines.append(f"Confidence: {resp['confidence_score']*100:.1f}%")
    
    if resp.get('short_reasoning'):
        lines.append(f"Reasoning: {resp['short_reasoning']}")
        
    # Climate conditions
    if 'agents' in resp and 'climate' in resp['agents']:
        climate = resp['agents']['climate']['output']
        lines.append("\n=== Climate Conditions ===")
        lines.append(f"Average Max Temp: {climate.get('avg_tmax_c', 'N/A')}°C")
        lines.append(f"Average Min Temp: {climate.get('avg_tmin_c', 'N/A')}°C")
        lines.append(f"Total Rainfall: {climate.get('total_rainfall_mm', 0):.1f}mm")
        lines.append(f"Confidence: {resp['agents']['climate']['confidence']*100:.1f}%")
        
    # Soil & Water status    
    if 'agents' in resp and 'soil_water' in resp['agents']:
        soil = resp['agents']['soil_water']['output']
        lines.append("\n=== Soil & Water Status ===")
        lines.append(f"Current Soil Moisture: {soil.get('avg_soil_moisture_pct', 'N/A')}%")
        if soil.get('drought_risk') is not None:
            lines.append(f"Drought Risk: {soil['drought_risk']:.1f}%")
            if soil.get('drought_alert'):
                lines.append("⚠️ DROUGHT ALERT ACTIVE")
        lines.append(f"Confidence: {resp['agents']['soil_water']['confidence']*100:.1f}%")
        
    # ET0 Analysis
    if 'agents' in resp and 'et0' in resp['agents']:
        et0 = resp['agents']['et0']['output']
        lines.append("\n=== Evapotranspiration ===")
        lines.append(f"ET0 Rate: {et0.get('et0_mm_per_day', 'N/A')} mm/day")
        if et0.get('kc_factor'):
            lines.append(f"Crop Coefficient (Kc): {et0['kc_factor']:.2f}")
        lines.append(f"Confidence: {resp['agents']['et0']['confidence']*100:.1f}%")
        
    # Crop Growth    
    if 'agents' in resp and 'crop_growth' in resp['agents']:
        crop = resp['agents']['crop_growth']['output']
        lines.append("\n=== Crop Status ===")
        lines.append(f"Growth Stage: {crop.get('growth_stage', 'N/A')}")
        if crop.get('days_after_sowing'):
            lines.append(f"Days After Sowing: {crop['days_after_sowing']}")
        lines.append(f"Confidence: {resp['agents']['crop_growth']['confidence']*100:.1f}%")
        
    # Location Adjustments
    if 'time_factors' in resp:
        tf = resp['time_factors']
        lines.append("\n=== Location & Time Factors ===")
        lines.append(f"Climate Zone: {tf.get('location_band', 'N/A')}")
        lines.append(f"Season: {tf.get('season', 'N/A')}")
        lines.append(f"Water Need Adjustment: {tf.get('water_need', 1.0):.2f}x")
        lines.append(f"Growth Rate Adjustment: {tf.get('growth_rate', 1.0):.2f}x")
        
    return "\n".join(lines)

async def main():
    """Test the orchestrator with a realistic payload."""
    url = "http://localhost:8000/predict-schedule"
    payload = make_test_payload()
    
    print("\nSending test request to orchestrator...")
    print(f"Farm: {payload['farm_area_ha']}ha {payload['crop_type']} on {payload['soil_type']} soil")
    print(f"Location: {payload['latitude']:.4f}°N, {payload['longitude']:.4f}°E")
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            print("\n=== ORCHESTRATOR RESPONSE ANALYSIS ===")
            print(analyze_response(data))
            
    except Exception as e:
        print(f"\nERROR: Failed to get prediction: {e}")
        return 1
        
    return 0

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))

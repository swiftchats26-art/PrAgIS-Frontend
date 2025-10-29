"""Test script to verify API connections are working."""
import asyncio
import os
import logging
from datetime import datetime
from pathlib import Path
import sys

# Add the project root to the Python path
project_root = str(Path(__file__).parents[2])  # project root (AI-FARMING)
sys.path.insert(0, project_root)

from backend.services.weather_service import WeatherService
from backend.utils.llm_client import LLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_weather_api():
    """Test the Open-Meteo (free) API connection."""
    weather_service = WeatherService()
    test_lat, test_lon = 51.5074, -0.1278  # London coordinates
    
    logger.info("Testing Open-Meteo (free) API connection...")
    try:
        weather_data = await weather_service.get_weather(test_lat, test_lon)
        logger.info("Successfully retrieved weather data:")
        logger.info(f"Temperature: {weather_data.get('tmax_c')}°C")
        logger.info(f"Relative Humidity: {weather_data.get('rh_percent')}%")
        logger.info(f"ET0: {weather_data.get('et0_mm')} mm/day")
        return True
    except Exception as e:
        logger.error(f"Failed to get weather data: {e}")
        return False

async def test_llm_api():
    """Test the Gemini API connection."""
    llm_client = LLMClient()
    
    logger.info("Testing Gemini API connection...")
    try:
        test_context = {
            "irrigation_volume_mm": 25.0,
            "confidence": 0.85,
            "timestamp": datetime.now().isoformat()
        }
        summary = await llm_client.summarize(test_context)
        logger.info("Successfully got LLM response:")
        logger.info(summary)
        return True
    except Exception as e:
        logger.error(f"Failed to test LLM API: {e}")
        return False

async def main():
    """Run all API connection tests."""
    logger.info("Starting API connection tests...")
    
    weather_ok = await test_weather_api()
    llm_ok = await test_llm_api()
    
    if weather_ok and llm_ok:
        logger.info("✅ All API connections working!")
    else:
        logger.error("❌ Some API connections failed!")
        if not weather_ok:
            logger.error("- Weather API failed. Open-Meteo is free (no key). Check network or python-weather installation.")
        if not llm_ok:
            logger.error("- LLM API failed. Check GEMINI_API_KEY in .env")

if __name__ == "__main__":
    asyncio.run(main())
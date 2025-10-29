from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import date


class DayDatum(BaseModel):
    date: str  # YYYY-MM-DD
    rainfall_mm: Optional[float] = None
    tmax_c: Optional[float] = None
    tmin_c: Optional[float] = None
    soil_moisture_pct: Optional[float] = None


class FarmInput(BaseModel):
    request_uuid: Optional[str] = Field(None, description="optional UUID to namespace state; server will generate if missing")
    farm_id: Optional[str] = None
    crop_type: Literal["wheat", "maize", "rice"]
    soil_type: Literal["sandy", "clay"]
    sowing_date: date
    latitude: Optional[float] = Field(None, description="Latitude of the farm/plot, required for climate API calls")
    longitude: Optional[float] = Field(None, description="Longitude of the farm/plot, required for climate API calls")
    farm_area_ha: Optional[float] = Field(None, description="Area in hectares")
    # last 5 days of intermediate agent data (frontend SHOULD provide these)
    last_5_days: Optional[List[DayDatum]] = None

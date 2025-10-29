from pydantic import BaseModel
from typing import Literal, Optional


class IrrigationOutput(BaseModel):
    irrigation_volume_mm: float
    irrigation_mode: Literal["drip", "sprinkler", "flood"]
    confidence_score: float
    short_reasoning: str
    days_after_sowing: int
    yield_index: float
    agents: Optional[dict] = None

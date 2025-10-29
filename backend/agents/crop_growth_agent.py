from typing import Dict, Any
from datetime import date


class CropGrowthAgent:
    """Placeholder Crop Growth Agent.

    Infers a simple growth stage from sowing_date vs today. Returns growth_stage
    and a confidence.
    """
    def __init__(self, config: Dict = None):
        self.config = config or {}

    async def run(self, input_data: Dict[str, Any]) -> Dict:
        sowing = input_data.get("sowing_date")
        stage = "unknown"
        confidence = 0.5
        try:
            if isinstance(sowing, str):
                sow = date.fromisoformat(sowing)
            elif isinstance(sowing, date):
                sow = sowing
            else:
                sow = None
            if sow:
                days = (date.today() - sow).days
                if days < 20:
                    stage = "emergence"
                elif days < 60:
                    stage = "vegetative"
                elif days < 100:
                    stage = "reproductive"
                else:
                    stage = "maturity"
                confidence = min(0.95, 0.6 + 0.01 * min(days, 60))
        except Exception:
            pass

        output = {"growth_stage": stage}
        return {"output": output, "confidence": round(confidence, 2)}

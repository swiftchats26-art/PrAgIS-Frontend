from typing import Dict, Any
from ..agents.climate_agent import ClimateAgent
from ..agents.soil_water_agent import SoilWaterAgent
from ..agents.crop_growth_agent import CropGrowthAgent
from ..agents.et0_agent import ET0Agent
from ..agents.decision_agent import DecisionAgent
from ..db.redis_client import RedisClient
from ..utils.llm_client import LLMClient


class Orchestrator:
    def __init__(self, redis_client: RedisClient, llm_client: LLMClient = None, weights: Dict[str, float] = None):
        self.redis = redis_client
        self.llm = llm_client or LLMClient()
        self.weights = weights

    async def run(self, farm_input: Dict[str, Any]) -> Dict[str, Any]:
        request_uuid = farm_input.get("request_uuid")

        # instantiate agents
        climate = ClimateAgent()
        soil = SoilWaterAgent()
        crop = CropGrowthAgent()
        et0 = ET0Agent()
        decision = DecisionAgent(weights=self.weights)

        # sequential processing
        agents_outputs = {}
        # Climate first - enriches input for other agents
        agents_outputs["climate"] = await climate.run(farm_input)

        # supply climate outputs to ET0 agent
        enriched_input = dict(farm_input)
        enriched_input.update({"climate": agents_outputs["climate"].get("output")})

        agents_outputs["et0"] = await et0.run(enriched_input)

        # supply et0 into soil agent for moisture estimation
        enriched_input.update({"et0": agents_outputs["et0"].get("output")})
        agents_outputs["soil_water"] = await soil.run(enriched_input)

        # crop growth can use climate too
        enriched_input.update({"soil_water": agents_outputs["soil_water"].get("output")})
        agents_outputs["crop_growth"] = await crop.run(enriched_input)

        # persist intermediate states (soil moisture, growth stage)
        try:
            await self.redis.set_json(request_uuid or "no_uuid", "soil_water", agents_outputs["soil_water"])
            await self.redis.set_json(request_uuid or "no_uuid", "crop_growth", agents_outputs["crop_growth"])
        except Exception:
            # don't block decision-making on Redis errors
            pass

        # Decision
        decision_out = await decision.run(agents_outputs, farm_input)

        # Create LLM summary (stub)
        try:
            # normalize confidence naming for LLM context
            conf_score = decision_out.get("confidence_score") if decision_out.get("confidence_score") is not None else decision_out.get("confidence")
            summary = await self.llm.summarize({"decision": decision_out, "agents": agents_outputs, "confidence_score": conf_score})
        except Exception:
            summary = ""

        decision_out["short_reasoning"] = summary or decision_out.get("short_reasoning")

        return decision_out

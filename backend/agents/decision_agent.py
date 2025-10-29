from typing import Dict, Any
from datetime import datetime
import os
from ..utils.config import DEFAULT_AGENT_WEIGHTS, DRIP_MAX_AREA_HA
from ..utils.time_match import TimeMatch

# Optional Gemini client for richer reasoning (if installed and API key present)
_HAS_GENAI = False
try:
    from google import genai
    _HAS_GENAI = True
except Exception:
    _HAS_GENAI = False


class DecisionAgent:
    """Aggregates agent outputs and returns final irrigation decision.

    Uses TimeMatch for location-based adjustments to irrigation schedules.
    NOTE: This uses placeholder logic. Real-world deployment must replace these
    heuristics with validated agronomic formulas and provided IRL weights.
    """
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or DEFAULT_AGENT_WEIGHTS
        self.time_match = TimeMatch()

    async def run(self, agents_outputs: Dict[str, Dict[str, Any]], farm_input: Dict[str, Any]) -> Dict:
        """Produce a final irrigation decision.

        This method tolerates agent outputs provided either as full agent results
        (with 'output' and 'confidence') or as raw output dicts. It prefers
        soil agent recommendations when available.
        """
        # Normalize agents_outputs: allow values to be either full result or output
        normalized: Dict[str, Dict[str, Any]] = {}
        for name, val in (agents_outputs or {}).items():
            if isinstance(val, dict) and 'output' in val:
                # Keep original structure
                normalized[name] = val
            else:
                # wrap raw output into expected shape
                normalized[name] = {'output': val or {}, 'confidence': (val.get('confidence') if isinstance(val, dict) else 0.0)}

        # compute weighted confidence using available confidences (weights must sum to <=1)
        total_conf = 0.0
        weight_sum = 0.0
        for name, out_wrapped in normalized.items():
            w = float(self.weights.get(name, 0.0))
            conf = float(out_wrapped.get('confidence') or 0.0)
            total_conf += w * conf
            weight_sum += w
        aggregated_confidence = (total_conf / weight_sum) if weight_sum > 0 else 0.0

        # Data-quality based caps: if any upstream agent reports fallback location or missing ET0,
        # reduce overall confidence to <= 0.5 (conservative behavior)
        try:
            soil_data_q = normalized.get('soil_water', {}).get('data_quality', {}) or normalized.get('soil_water', {}).get('output', {}).get('data_quality', {})
            et0_info = farm_input.get('et0')
            if isinstance(soil_data_q, dict) and soil_data_q.get('location_quality') == 'fallback':
                aggregated_confidence = min(aggregated_confidence, 0.5)
            if et0_info is None:
                aggregated_confidence = min(aggregated_confidence, 0.5)
        except Exception:
            pass

        # choose irrigation mode: prefer soil agent's suggested mode
        area = float(farm_input.get("farm_area_ha") or 0.0)
        default_mode = "drip" if area <= DRIP_MAX_AREA_HA else "sprinkler"
        soil_out = normalized.get('soil_water', {}).get('output', {})
        soil_irrigation = soil_out.get('irrigation_needs') or {}
        soil_volume = soil_irrigation.get('volume_mm')
        soil_mode = soil_irrigation.get('mode')

        # Respect soil agent recommendation when present and confidence is reasonable
        soil_conf = float(normalized.get('soil_water', {}).get('confidence') or 0.0)
        irrigation_volume_mm = 0.0
        irrigation_mode = default_mode
        if soil_volume is not None:
            try:
                irrigation_volume_mm = round(float(soil_volume), 2)
            except Exception:
                irrigation_volume_mm = 0.0
            irrigation_mode = soil_mode or default_mode
            # If soil confidence is very low, don't blindly accept volume
            if soil_conf < 0.35:
                # reduce volume proportionally to confidence
                irrigation_volume_mm = round(irrigation_volume_mm * soil_conf, 2)
        else:
            # fallback heuristic using farm_input ET0 and soil moisture
            et0 = None
            # Prefer ET0 from farm_input
            if isinstance(farm_input.get('et0'), dict):
                et0 = farm_input.get('et0', {}).get('et0_mm_per_day')
            else:
                et0 = farm_input.get('et0')
            et0 = et0 or normalized.get('et0', {}).get('output', {}).get('et0_mm_per_day') or 0.0

            soil_moisture = soil_out.get('avg_soil_moisture_pct')
            base_need = float(et0) * 1.0
            if soil_moisture is not None:
                base_need = max(0.0, base_need - (float(soil_moisture) / 100.0) * base_need)
            irrigation_volume_mm = round(base_need, 2)
            irrigation_mode = default_mode

        # Apply location-based schedule adjustments
        lat = farm_input.get("latitude")
        lon = farm_input.get("longitude")
        time_factors = {}
        if lat is not None and lon is not None:
            current_date = datetime.now()
            if farm_input.get("current_date"):
                try:
                    current_date = datetime.fromisoformat(farm_input["current_date"])
                except (ValueError, TypeError):
                    pass
            base_schedule = {"irrigation_volume_mm": irrigation_volume_mm, "irrigation_mode": irrigation_mode}
            adjusted = self.time_match.adjust_schedule(base_schedule, lat, lon)
            irrigation_volume_mm = adjusted.get("irrigation_volume_mm", irrigation_volume_mm)
            irrigation_mode = adjusted.get("irrigation_mode", irrigation_mode)
            time_factors = adjusted.get('adjustment_factors', {})
            if time_factors.get('confidence'):
                aggregated_confidence = (aggregated_confidence + time_factors['confidence']) / 2

        # Build concise, accurate reasoning — prefer Gemini-generated reasoning if available
        et0_used = None
        if isinstance(farm_input.get('et0'), dict):
            et0_used = farm_input.get('et0', {}).get('et0_mm_per_day')
        else:
            et0_used = farm_input.get('et0')
        et0_used = et0_used if et0_used is not None else normalized.get('et0', {}).get('output', {}).get('et0_mm_per_day', 0.0)

        reasoning = None
        # Build a compact prompt for Gemini if available
        prompt = (
            f"You are an agronomic decision assistant. Given farm input: {farm_input} and agent outputs: {normalized}, "
            f"produce a short JSON with keys: reasoning (text), recommended_volume_mm (number), recommended_mode (string), confidence (0-1). "
            f"Be concise and reference ET0={et0_used} mm/day and soil_moisture={soil_out.get('avg_soil_moisture_pct')}%."
        )
        gemini_model = os.environ.get('GENIE_MODEL_NAME', 'gen-lang-client-0633492165')
        if _HAS_GENAI and os.environ.get('GEMINI_API_KEY'):
            try:
                client = genai.Client()
                resp = client.models.generate_content(model=gemini_model, contents=prompt)
                reasoning = resp.text
            except Exception:
                reasoning = None

        if not reasoning:
            reasoning = (
                f"Aggregated confidence {round(aggregated_confidence,2)}. ET0={et0_used} mm/day; "
                f"soil_moisture={soil_out.get('avg_soil_moisture_pct')}%. Mode={irrigation_mode}."
            )
            if time_factors:
                reasoning += (
                    f" Location adjustments: {time_factors.get('location_band')} zone, {time_factors.get('season')} season."
                )

        # Inconsistency detection
        inconsistencies = []
        try:
            soil_vol = soil_out.get('irrigation_needs', {}).get('volume_mm') if isinstance(soil_out.get('irrigation_needs'), dict) else None
            if soil_vol is not None and abs(float(soil_vol) - float(irrigation_volume_mm)) > max(5.0, 0.1 * float(soil_vol)):
                inconsistencies.append('Significant volume mismatch between SoilAgent and DecisionAgent')
            # ET0 propagation check
            if et0_used == 0 or et0_used is None:
                inconsistencies.append('ET0 missing or zero in decision layer')
        except Exception:
            pass

        return {
            "irrigation_volume_mm": float(irrigation_volume_mm),
            "irrigation_mode": irrigation_mode,
            "confidence": round(aggregated_confidence, 2),
            "reasoning": reasoning,
            "time_factors": time_factors,
            "agents": normalized,
            "inconsistencies": inconsistencies,
        }

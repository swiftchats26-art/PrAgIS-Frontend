"""LLM client with Gemini Flash integration.

Uses Google's Gemini 2.0 Flash model for quick summarization with fallback to deterministic summary.
Set GEMINI_API_KEY in environment or pass during initialization.
"""
from typing import Optional, Dict
import os
import json
import httpx
from .config import LLM_ENABLED, LLM_API_KEY

# Gemini Flash API configuration
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Prompts
SUMMARY_PROMPT = """
Analyze this irrigation decision data and provide a brief, clear explanation (1-2 sentences) focusing on:
1. The recommended irrigation amount and method
2. Key factors that influenced this decision (weather, soil moisture, crop stage)
3. Any special considerations or warnings

Context data:
{context}
"""


class LLMClient:
    def __init__(self, provider: Optional[str] = None, api_key: Optional[str] = None):
        self.provider = provider or "gemini"
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or LLM_API_KEY
        self.enabled = LLM_ENABLED and bool(self.api_key)
        
        # Initialize HTTP client for Gemini API calls
        if self.enabled and self.provider == "gemini":
            self.http_client = httpx.AsyncClient(
                headers={
                    "Content-Type": "application/json",
                    "X-goog-api-key": self.api_key
                },
                timeout=30.0
            )

    async def summarize(self, context: Dict) -> str:
        """Generate a concise summary of the irrigation decision using Gemini Flash.
        
        Falls back to deterministic summary if Gemini is unavailable.
        """
        if self.enabled and self.provider == "gemini":
            try:
                # Extract relevant details for the prompt
                decision = context.get("decision", {})
                agents = context.get("agents", {})
                
                # Build a structured context for the LLM
                prompt_context = {
                    "irrigation_volume": decision.get("irrigation_volume_mm"),
                    "irrigation_mode": decision.get("irrigation_mode"),
                    "confidence": context.get("confidence_score"),
                    "climate": agents.get("climate", {}).get("output", {}),
                    "soil_water": agents.get("soil_water", {}).get("output", {}),
                    "crop_growth": agents.get("crop_growth", {}).get("output", {})
                }
                
                # Generate summary with Gemini Flash
                summary = await self._call_gemini(
                    SUMMARY_PROMPT.format(context=json.dumps(prompt_context, indent=2))
                )
                return summary.strip() if summary else self._deterministic_summary(context)
                
            except Exception as e:
                print(f"Gemini summarization failed: {e}")
                return self._deterministic_summary(context)
        
        return self._deterministic_summary(context)

    async def _call_gemini(self, prompt: str) -> str:
        """Make an async call to Gemini Flash API"""
        try:
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            async with self.http_client as client:
                response = await client.post(GEMINI_API_URL, json=payload)
                response.raise_for_status()
                
                data = response.json()
                # Extract text from Gemini response
                if data.get("candidates"):
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                return ""
                
        except Exception as e:
            print(f"Gemini API call failed: {e}")
            return ""

    def _deterministic_summary(self, context: Dict) -> str:
        """Fallback deterministic summary when Gemini is unavailable"""
        parts = []
        if "decision" in context:
            d = context["decision"]
            parts.append(f"Irrigation: {d.get('irrigation_volume_mm')} mm via {d.get('irrigation_mode')}")
        if "agents" in context:
            ag = context["agents"]
            parts.append(f"Confidence: {context.get('confidence_score', 'n/a')}")
            # small highlight of agents
            for name, out in ag.items():
                parts.append(f"{name}: conf {out.get('confidence')}")
        return " | ".join(parts)

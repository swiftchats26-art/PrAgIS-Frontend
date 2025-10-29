# PrAgIS - Multi-Agent Precision Irrigation System (backend)

This is a FastAPI-based backend prototype for PrAgIS. It implements a modular
agent pipeline with placeholder logic and Redis state storage.

Quick start (development):

1. Install dependencies into your Python 3.10+ environment:

```powershell
python -m pip install -r backend/requirements.txt
```

2. Run the app with Uvicorn:

```powershell
uvicorn backend.main:app --reload
```

Endpoints:
- `GET /status` - health check
- `GET /mock-data` - returns an example input payload
- `POST /predict-schedule` - run the orchestration. Supply JSON matching `schemas/farm_input.py`.

Notes:
- Agents return placeholder outputs and confidence scores. Decision weights are configurable in `backend/utils/config.py`.
- Redis defaults are localhost:6379 and used for intermediate state; change values in `backend/utils/config.py` if needed.
- LLM integration is a stub in `backend/utils/llm_client.py` and disabled by default.

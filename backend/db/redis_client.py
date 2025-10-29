"""Async Redis client wrapper used by the orchestrator and agents.

Uses redis.asyncio (redis-py) for async operations. Keeps key namespace by
request UUID (or farm_id if provided).
"""
from typing import Optional
import json
import asyncio
import redis.asyncio as redis
from ..utils.config import REDIS_HOST, REDIS_PORT, REDIS_DB


class RedisClient:
    def __init__(self, host: str = REDIS_HOST, port: int = REDIS_PORT, db: int = REDIS_DB):
        self._client: Optional[redis.Redis] = None
        self.host = host
        self.port = port
        self.db = db

    async def connect(self):
        if self._client is None:
            self._client = redis.Redis(host=self.host, port=self.port, db=self.db)
            # ping to ensure connection (non-blocking)
            try:
                await self._client.ping()
            except Exception:
                # connection errors will surface on usage
                pass

    async def close(self):
        if self._client is not None:
            await self._client.close()
            self._client = None

    def _key(self, request_uuid: str, name: str) -> str:
        return f"pragis:{request_uuid}:{name}" if request_uuid else f"pragis:{name}"

    async def set_json(self, request_uuid: str, name: str, value) -> None:
        await self.connect()
        key = self._key(request_uuid, name)
        await self._client.set(key, json.dumps(value))

    async def get_json(self, request_uuid: str, name: str):
        await self.connect()
        key = self._key(request_uuid, name)
        raw = await self._client.get(key)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

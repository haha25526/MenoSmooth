"""
Redis client for caching and session management
"""
import redis.asyncio as redis
from redis.asyncio import ConnectionPool, Redis
from app.config import settings

_redis_pool: ConnectionPool | None = None
_redis_client: Redis | None = None

def _get_pool() -> ConnectionPool:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            socket_keepalive=True,
            socket_connect_timeout=5,
        )
    return _redis_pool

def _get_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis(connection_pool=_get_pool())
    return _redis_client

async def init_redis():
    _get_client()

async def get_redis() -> Redis:
    return _get_client()

async def close_redis():
    global _redis_client, _redis_pool
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
    if _redis_pool is not None:
        await _redis_pool.disconnect()
        _redis_pool = None

redis_client = _get_client()

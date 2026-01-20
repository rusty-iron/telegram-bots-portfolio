from __future__ import annotations

import redis

from ..config import settings


def create_redis_client(redis_url: str) -> redis.Redis:
    return redis.from_url(redis_url, decode_responses=True)


def get_redis_client() -> redis.Redis:
    """Получить клиент Redis"""
    return create_redis_client(str(settings.redis_url))


def check_redis_connection(client: redis.Redis) -> bool:
    try:
        return client.ping()
    except Exception:
        return False

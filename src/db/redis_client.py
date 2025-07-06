"""Redis connection and utilities."""

import json
from typing import Any

import redis

from src.config import CACHE_TTL, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW, REDIS_CONFIG


class RedisClient:
    def __init__(self):
        self.client = redis.Redis(**REDIS_CONFIG)

    def get_json(self, key: str) -> Any | None:
        """Get JSON data from Redis."""
        data = self.client.get(key)
        return json.loads(data) if data else None

    def set_json(self, key: str, value: Any, ttl: int = CACHE_TTL) -> bool:
        """Set JSON data in Redis with TTL."""
        return self.client.setex(key, ttl, json.dumps(value))

    def add_to_cart(self, user_id: str, product_id: str, quantity: int):
        """Add item to user's cart."""
        cart_key = f"cart:{user_id}"
        # Increment or set product quantity
        self.client.hincrby(cart_key, product_id, quantity)
        # Set TTL for cart
        self.client.expire(cart_key, CACHE_TTL)

    def rate_limit_check(self, user_id: str, endpoint: str) -> bool:
        """Check if user has exceeded rate limit."""
        key = f"rate_limit:{user_id}:{endpoint}"
        current = self.client.incr(key)
        if current == 1:
            self.client.expire(key, RATE_LIMIT_WINDOW)
        return current <= RATE_LIMIT_REQUESTS


# Singleton instance
redis_client = RedisClient()

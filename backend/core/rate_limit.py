from fastapi import Request, Depends
import redis.asyncio as redis
from core.config import settings
from core.exceptions import AppException
from api.deps import get_current_user

redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

class RateLimitExceeded(AppException):
    def __init__(self):
        super().__init__("Too many requests", "TOO_MANY_REQUESTS", 429)

def rate_limit_ip(times: int, seconds: int):
    async def _rate_limit(request: Request):
        identifier = request.client.host if request.client else "unknown"
        key = f"rate_limit:{request.url.path}:{identifier}"
        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, seconds)
        if current > times:
            raise RateLimitExceeded()
    return _rate_limit

def rate_limit_user(times: int, seconds: int):
    async def _rate_limit(request: Request, current_user = Depends(get_current_user)):
        identifier = str(current_user.id)
        key = f"rate_limit:{request.url.path}:{identifier}"
        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, seconds)
        if current > times:
            raise RateLimitExceeded()
    return _rate_limit

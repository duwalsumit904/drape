from redis.asyncio import Redis
from app.core.config import settings

async def get_redis():
    from main import redis_pool    # import here to avoid circular import
    client = Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.aclose()
import logging
from redis.asyncio import Redis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global redis client variable
redis_client: Redis = None

async def init_redis():
    global redis_client
    redis_client = Redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        socket_timeout=2.0 # 2 seconds timeout for fast failure
    )
    # Ping to ensure connection
    try:
        await redis_client.ping()
        logger.info(f"Connected to Redis at {settings.REDIS_URL}")
    except Exception as e:
        logger.error(f"Could not connect to Redis: {e}")
        raise

async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Closed Redis connection")

async def get_redis():
    return redis_client

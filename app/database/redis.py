import redis.asyncio as redis
from app.config import settings

class RedisClient:
    _instance = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        if cls._instance is None:
            cls._instance = redis.from_url(
                settings.redis_url, 
                encoding="utf-8", 
                decode_responses=True
            )
        return cls._instance

    @classmethod
    async def initialize(cls):
        # Test connection
        client = cls.get_client()
        await client.ping()

    @classmethod
    async def close(cls):
        if cls._instance:
            await cls._instance.close()
            cls._instance = None

# Client instance
redis_client = RedisClient.get_client()
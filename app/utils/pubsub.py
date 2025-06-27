from app.database.redis import redis_client

async def publish(channel: str, message: str):
    await redis_client.publish(channel, message)
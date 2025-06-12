from fastapi import FastAPI, HTTPException
from app.database import supabase, redis

app = FastAPI()

@app.get("/test/supabase")
async def test_supabase():
    try:
        result = supabase.sb_client.table('categories').select("*").execute()
        return {"status": "success", "data": result.data}
    except Exception as e:
        raise HTTPException(500, f"Supabase error: {str(e)}")

@app.get("/test/redis")
async def test_redis():
    try:
        await redis.redis_client.set("test_key", "Hello Redis!")
        value = await redis.redis_client.get("test_key")
        return {"status": "success", "key": "test_key", "value": value}
    except Exception as e:
        raise HTTPException(500, f"Redis error: {str(e)}")
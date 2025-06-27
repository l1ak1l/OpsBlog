from fastapi import FastAPI, HTTPException
from app.database import supabase, redis
from app.routes import auth
from fastapi import FastAPI
from app.database.supabase import SupabaseClient
from app.database.redis import redis_client
from app.routes import auth, posts, comments, ws
from app.services.post import sync_views_to_db
from app.config import settings
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await SupabaseClient.connect()
    await redis_client.initialize()
    
    # Start background tasks
    background_task = asyncio.create_task(periodic_sync_views())
    
    print("✅ Connected to databases")
    
    yield
    
    # Shutdown
    # Cancel background task
    background_task.cancel()
    try:
        await background_task
    except asyncio.CancelledError:
        pass
    
    # Sync views one last time
    await sync_views_to_db()
    
    # Close connections
    await SupabaseClient.disconnect()
    await redis_client.close()
    
    print("❌ Disconnected from databases")

app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(ws.router)

async def periodic_sync_views():
    """Periodically sync view counts to database"""
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        try:
            await sync_views_to_db()
        except Exception as e:
            print(f"Error syncing views: {str(e)}")

@app.get("/")
def health_check():
    return {
        "status": "running",
        "version": "1.0.0",
        "services": {
            "supabase": "connected",
            "redis": "connected"
        }
    }
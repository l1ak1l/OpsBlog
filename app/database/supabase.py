import os
from supabase import create_client, Client
from app.config import settings

class SupabaseClient:
    _instance = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            cls._instance = create_client(
                settings.supabase_url, 
                settings.supabase_key
            )
        return cls._instance

    @classmethod
    async def connect(cls):
        # Supabase client is synchronous, so no async connect needed
        cls.get_client()

    @classmethod
    async def disconnect(cls):
        # Supabase client doesn't have explicit disconnect
        cls._instance = None

# Initialize on import
sb_client = SupabaseClient.get_client()
# app/utils/supabase_client.py
from supabase import create_client, Client
from api.config import settings
from functools import lru_cache


@lru_cache()
def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_KEY
    )


supabase: Client = get_supabase_client()

# from supabase import create_client
# import os
# from dotenv import load_dotenv

# load_dotenv()  # Load environment variables

# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

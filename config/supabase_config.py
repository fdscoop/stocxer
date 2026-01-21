"""
Supabase Configuration
"""
import os
from supabase import create_client, Client
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase credentials from .env
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")

# Initialize Supabase clients
_supabase_client: Optional[Client] = None
_supabase_admin_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get or create Supabase client instance (uses anon key for auth operations)"""
    global _supabase_client

    if _supabase_client is None:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

    return _supabase_client


def get_supabase_admin_client() -> Client:
    """Get or create Supabase admin client (uses service role key to bypass RLS)"""
    global _supabase_admin_client

    if _supabase_admin_client is None:
        # Use service key if available, otherwise fall back to anon key
        key = SUPABASE_SERVICE_KEY or SUPABASE_KEY
        _supabase_admin_client = create_client(SUPABASE_URL, key)

    return _supabase_admin_client


# Initialize on import
supabase: Client = get_supabase_client()
supabase_admin: Client = get_supabase_admin_client()

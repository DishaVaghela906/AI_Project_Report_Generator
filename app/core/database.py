"""
Supabase client singleton.
"""
from supabase import create_client, Client
from app.core.config import settings
from loguru import logger

_client: Client | None = None


def get_supabase() -> Client:
    """Returns (or lazily initialises) the shared Supabase client."""
    global _client
    if _client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set in .env"
            )
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("Supabase client initialised")
    return _client

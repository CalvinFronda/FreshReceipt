from supabase import Client, create_client

from app.core.config import settings


def get_supabase_client() -> Client:
    """
    Create and return a Supabase client instance.
    Uses service role key for admin operations.
    """
    return create_client(
        supabase_url=settings.SUPABASE_URL, supabase_key=settings.SUPABASE_ANON_KEY
    )


# Singleton instance for dependency injection
supabase: Client = get_supabase_client()

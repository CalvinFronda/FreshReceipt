from supabase import Client, create_client

from app.core.config import settings


def get_supabase_client() -> Client:
    """
    Create and return a Supabase client instance.
    Uses anon key (respects RLS policies).
    """
    return create_client(
        supabase_url=settings.SUPABASE_URL, supabase_key=settings.SUPABASE_ANON_KEY
    )


def get_supabase_admin_client() -> Client:
    """
    Create and return a Supabase admin client instance.
    Uses service role key to bypass RLS (for backend operations).
    """
    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY not found in settings")
    return create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY,
    )


# Singleton instances for dependency injection
supabase: Client = get_supabase_client()  # Anon key (respects RLS)
supabase_admin: Client = get_supabase_admin_client()  # Service role (bypasses RLS)

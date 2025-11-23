from typing import Optional

from fastapi import Request
from supabase import Client, create_client

from app.core.config import settings


def get_supabase_client(access_token: Optional[str] = None) -> Client:
    """
    Create and return a Supabase client instance.
    Uses anon key (respects RLS policies).
    """
    client = create_client(
        supabase_url=settings.SUPABASE_URL, supabase_key=settings.SUPABASE_ANON_KEY
    )

    if access_token:
        client.auth.set_session(access_token, "")

    return client


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


supabase_admin: Client = get_supabase_admin_client()  # Service role (bypasses RLS)


def get_authenticated_supabase(request: Request) -> Client:
    """
    Get a supabase client authenticated with the user's JWT token from the request.
    """
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header else None
    return get_supabase_client(access_token=token)


supabase: Client = get_supabase_client()  # Anon key (respects RLS)

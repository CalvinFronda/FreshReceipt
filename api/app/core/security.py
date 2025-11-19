import asyncio
from typing import Any, Dict

from fastapi import HTTPException, status

from app.core.supabase import supabase


async def verify_supabase_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token issued by Supabase Auth.

    Args:
        token: JWT access token from Supabase

    Returns:
        User data from token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # The Supabase Python client is synchronous. Run the call in a thread
        # so this function can remain async and callers can `await` it.
        response = await asyncio.to_thread(lambda: supabase.auth.get_user(token))

        # `response` is an APIResponse; if no user, treat as unauthorized
        user = getattr(response, "user", None)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Return user data
        return {
            "id": user.id,
            "email": user.email,
            "user_metadata": getattr(user, "user_metadata", None),
            "created_at": getattr(user, "created_at").isoformat(),
        }

    except Exception as e:
        # Handle various auth errors
        if "invalid" in str(e).lower() or "expired" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is invalid or expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Generic error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
        # Verify token with Supabase Auth API
        response = supabase.auth.get_user(token)

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Return user data
        return {
            "id": response.user.id,
            "email": response.user.email,
            "user_metadata": response.user.user_metadata,
            "created_at": response.user.created_at.isoformat(),
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

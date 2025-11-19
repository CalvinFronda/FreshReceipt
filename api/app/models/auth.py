from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    """User model from Subabase Auth"""

    id: str
    email: EmailStr
    user_metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Response model for user data"""

    id: str
    email: str
    created_at: Optional[str] = None


class TokenPayload(BaseModel):
    """JWT token payload"""

    sub: str  # User ID
    email: Optional[str] = None
    exp: Optional[int] = None  # Expiration time

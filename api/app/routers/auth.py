from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.models.auth import User, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    get auth user's information.

    Requires valid JWT token in Auth header

    """
    return UserResponse(
        id=current_user.id, email=current_user.email, created_at=current_user.created_at
    )


@router.get("/verify")
async def verify_token(current_user: User = Depends(get_current_user)):
    """
    Checks if provided token is valid
    """
    return {"valid": True, "user_id": current_user.id, "email": current_user.email}

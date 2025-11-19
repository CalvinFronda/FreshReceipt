from app.core.security import verify_supabase_token
from app.models.auth import User
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """
    get the current auth user

    @app.get("/protected")
    async def protected__route(user: User: = Depends(get_current_user)):
        return {"user_id" : user.id}
    """
    token = credentials.credentials

    # Verify token and get user data

    user_data = await verify_supabase_token(token)

    return User(**user_data)


async def get_current_user_id(current_user: User = Depends(get_current_user)) -> str:
    """
    gets user id
    """

    return current_user.id

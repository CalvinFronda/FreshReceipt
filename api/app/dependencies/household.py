import asyncio
from typing import Optional

from fastapi import Depends, HTTPException, Request, status

from app.core.supabase import supabase_admin
from app.dependencies.auth import get_current_user
from app.models.auth import User


async def get_user_households(current_user: User = Depends(get_current_user)) -> list:
    """
    Get all households that the current user belongs to.
    """
    try:
        result = await asyncio.to_thread(
            lambda: (
                supabase_admin.table("household_members")
                .select("household_id, role, households(*)")
                .eq("user_id", current_user.id)
                .execute()
            )
        )

        return result.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch households: {str(e)}",
        )


async def get_user_primary_household(
    current_user: User = Depends(get_current_user),
) -> str:
    """
    Get the user's primary (first) household ID.
    Creates one if the user has no households using the DB RPC.
    """
    try:
        # Check if user has any households
        result = await asyncio.to_thread(
            lambda: (
                supabase_admin.table("household_members")
                .select("household_id")
                .eq("user_id", current_user.id)
                .limit(1)
                .execute()
            )
        )

        if result.data and len(result.data) > 0:
            hid = result.data[0]["household_id"]
            return hid

        # Create a default household using the RPC

        rpc_result = await asyncio.to_thread(
            lambda: supabase_admin.rpc(
                "create_household_with_member",
                {
                    "payload": {
                        "user_id": current_user.id,
                        "email": current_user.email,
                        "name": f"{current_user.email}'s Household",
                    }
                },
            ).execute()
        )

        if hasattr(rpc_result, "error") and rpc_result.error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create household: {rpc_result.error}",
            )

        # Extract household id from RPC response
        rpc_data = getattr(rpc_result, "data", None) or (
            rpc_result.get("data") if isinstance(rpc_result, dict) else None
        )
        if not rpc_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create household: no data returned",
            )

        # Normalize: RPC returns a household row (dict or object)
        if isinstance(rpc_data, dict):
            household_id = rpc_data.get("id")
        else:
            household_id = getattr(rpc_data, "id", None)

        if not household_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to extract household id from RPC response",
            )

        return household_id

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get/create household: {str(e)}",
        )


async def get_current_household(
    household_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get the current household.
    """
    if household_id:
        await verify_household_access(household_id, current_user)
        return household_id

    return await get_user_primary_household(current_user)


async def verify_household_access(
    household_id: str,
    current_user: User = Depends(get_current_user),
    required_role: Optional[str] = None,
) -> dict:
    """
    Verify that the user has access to a household.
    Optionally check if they have a specific role.

    Args:
        household_id: The household to check access for
        current_user: Current authenticated user
        required_role: Optional role requirement ('owner', 'admin')

    Returns:
        dict with household_id and user's role

    Raises:
        HTTPException: If user doesn't have access or required role
    """
    try:
        result = await asyncio.to_thread(
            lambda: (
                supabase_admin.table("household_members")
                .select("role")
                .eq("household_id", household_id)
                .eq("user_id", current_user.id)
                .execute()
            )
        )
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this household",
            )

        user_role = result.data[0]["role"]

        # Check role requirement if specified
        if required_role:
            role_hierarchy = {"owner": 3, "admin": 2, "member": 1}
            if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You need {required_role} role to perform this action",
                )

        return {"household_id": household_id, "role": user_role}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify household access: {str(e)}",
        )


# TODO: Maybe this is extra?
def get_household_header(request: Request) -> str:
    """
    Extract household ID from X-Household-ID header.
    """
    household_id = request.headers.get("X-Household-ID")
    if not household_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Household-ID header is required",
        )
    return household_id


async def verify_header_household_access(
    household_id: str = Depends(get_household_header),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Verify access to the household specified in the header.
    """
    return await verify_household_access(household_id, current_user)

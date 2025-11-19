from typing import Optional

from fastapi import Depends, HTTPException, status

from app.core.supabase import supabase
from app.dependencies.auth import get_current_user
from app.models.auth import User


async def get_user_households(current_user: User = Depends(get_current_user)) -> list:
    """
    Get all households that the current user belongs to.
    """
    try:
        result = (
            supabase.table("household_members")
            .select("household_id, role, households(*)")
            .eq("user_id", current_user.id)
            .execute()
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
    Creates one if the user has no households.
    """
    try:
        # Check if user has any households
        result = (
            supabase.table("household_members")
            .select("household_id")
            .eq("user_id", current_user.id)
            .limit(1)
            .execute()
        )

        if result.data and len(result.data) > 0:
            return result.data[0]["household_id"]

        # Create a default household for the user
        household_result = (
            supabase.table("households")
            .insert(
                {
                    "name": f"{current_user.email}'s Household",
                    "created_by": current_user.id,
                }
            )
            .execute()
        )

        household_id = household_result.data[0]["id"]

        # Add user as owner
        supabase.table("household_members").insert(
            {"household_id": household_id, "user_id": current_user.id, "role": "owner"}
        ).execute()

        return household_id

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get/create household: {str(e)}",
        )


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
        result = (
            supabase.table("household_members")
            .select("role")
            .eq("household_id", household_id)
            .eq("user_id", current_user.id)
            .execute()
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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify household access: {str(e)}",
        )

# api/app/routers/households.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.supabase import supabase
from app.dependencies.auth import get_current_user
from app.dependencies.household import (
    get_user_households,
    verify_household_access,
)
from app.models.auth import User
from app.models.household import (
    HouseholdCreate,
    HouseholdMember,
    HouseholdWithRole,
    InviteMemberRequest,
)
from app.services.households import (
    get_or_create_primary_household,
    get_primary_household_id,
)


router = APIRouter(prefix="/households", tags=["Households"])


@router.get("", response_model=List[HouseholdWithRole])
async def list_user_households(current_user: User = Depends(get_current_user)):
    """
    Get all households that the current user is a member of.
    """
    try:
        result = get_user_households(current_user)

        households = []
        for item in result.data:
            household_data = item["households"]
            households.append({**household_data, "role": item["role"]})

        return households

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch households: {str(e)}",
        )


@router.post("", response_model=HouseholdWithRole, status_code=status.HTTP_201_CREATED)
async def create_household(
    household_data: HouseholdCreate, current_user: User = Depends(get_current_user)
):
    """
    Create a new household. The creator becomes the owner.
    """
    try:
        # Create or fetch primary household
        household_result = await get_or_create_primary_household(current_user, household_data.name)

        # Support different return shapes: dict (created row), APIResponse-like
        if hasattr(household_result, "data"):
            household_row = household_result.data[0]
        elif isinstance(household_result, dict):
            household_row = household_result
        elif isinstance(household_result, list):
            household_row = household_result[0]
        else:
            # Fallback: try to use as-is
            household_row = household_result

        # Ensure we have a plain dict for the response
        if hasattr(household_row, "dict"):
            household_dict = household_row.dict()
        else:
            household_dict = dict(household_row)

        return {**household_dict, "role": "owner"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed in create_household: {str(e)}",
        )


@router.get("/{household_id}", response_model=HouseholdWithRole)
async def get_household(
    household_id: str,
    access: dict = Depends(verify_household_access),
    current_user: User = Depends(get_current_user),
):
    """
    Get details of a specific household.
    """
    try:
        result = get_primary_household_id(current_user)

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Household not found"
            )

        return {**result.data[0], "role": access["role"]}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch household: {str(e)}",
        )


@router.get("/{household_id}/members", response_model=List[HouseholdMember])
async def list_household_members(
    household_id: str, access: dict = Depends(verify_household_access)
):
    """
    Get all members of a household.
    """
    try:
        result = (
            supabase.table("household_members")
            .select("*")
            .eq("household_id", household_id)
            .execute()
        )

        # Fetch user emails for each member
        members = []
        for member in result.data:
            # Get user email from auth.users
            user_result = supabase.auth.admin.get_user_by_id(member["user_id"])
            members.append(
                {
                    **member,
                    "email": user_result.user.email if user_result.user else None,
                }
            )

        return members

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch household members: {str(e)}",
        )


@router.post("/{household_id}/members", status_code=status.HTTP_201_CREATED)
async def invite_member(
    household_id: str,
    invite_data: InviteMemberRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Invite a user to join the household by email.
    Requires admin or owner role.
    """
    # Verify user has admin/owner role
    access = await verify_household_access(
        household_id=household_id, current_user=current_user, required_role="admin"
    )

    try:
        # Find user by email
        # Note: This requires service role key to access auth.users
        user_result = supabase.auth.admin.list_users()
        target_user = None

        for user in user_result:
            if user.email == invite_data.email:
                target_user = user
                break

        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {invite_data.email} not found",
            )

        # Check if already a member
        existing = (
            supabase.table("household_members")
            .select("id")
            .eq("household_id", household_id)
            .eq("user_id", target_user.id)
            .execute()
        )

        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this household",
            )

        # Add member
        result = (
            supabase.table("household_members")
            .insert(
                {
                    "household_id": household_id,
                    "user_id": target_user.id,
                    "role": invite_data.role,
                }
            )
            .execute()
        )

        return {
            "message": f"Successfully invited {invite_data.email}",
            "member": result.data[0],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invite member: {str(e)}",
        )


@router.delete(
    "/{household_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_member(
    household_id: str, user_id: str, current_user: User = Depends(get_current_user)
):
    """
    Remove a member from the household.
    Requires admin or owner role, or user can remove themselves.
    """
    # Allow user to remove themselves, or require admin role
    if user_id != current_user.id:
        await verify_household_access(
            household_id=household_id, current_user=current_user, required_role="admin"
        )
    else:
        # Still need to verify they're in the household
        await verify_household_access(
            household_id=household_id, current_user=current_user
        )

    try:
        result = (
            supabase.table("household_members")
            .delete()
            .eq("household_id", household_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove member: {str(e)}",
        )

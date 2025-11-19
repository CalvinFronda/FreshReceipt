import asyncio
from typing import Any, Dict, Optional

from fastapi import HTTPException

from app.core.supabase import supabase
from app.models.auth import User, UserResponse


def _resp_data(resp: Any) -> Optional[Any]:
    """Return the `.data` from an APIResponse or dict-safe `data` key."""
    if resp is None:
        return None
    if hasattr(resp, "data"):
        return getattr(resp, "data")
    if isinstance(resp, Dict) or isinstance(resp, dict):
        return resp.get("data")
    return None


def _resp_error(resp: Any) -> Optional[Any]:
    """Return the `.error` from an APIResponse or dict-safe `error` key."""
    if resp is None:
        return None
    if hasattr(resp, "error"):
        return getattr(resp, "error")
    if isinstance(resp, Dict) or isinstance(resp, dict):
        return resp.get("error")
    return None


async def get_primary_household_id(user: User) -> UserResponse | None:
    result = await asyncio.to_thread(
        lambda: (
            supabase.table("household_members")
            .select("household_id")
            .eq("user_id", user.id)
            .limit(1)
            .execute()
        )
    )

    data = _resp_data(result)
    if data:
        return data

    return None


async def create_default_household(user: User, name: str):
    # Use DB-side RPC to create the household and member in one atomic operation.
    # This ensures the DB sets `created_by` (so RLS WITH CHECK passes) and
    # avoids any client-side mismatch with auth.uid().
    rpc_result = await asyncio.to_thread(
        lambda: supabase.rpc(
            "create_household_with_member",
            {"payload": {"user_id": user.id, "email": user.email, "name": name}},
        ).execute()
    )

    rpc_err = _resp_error(rpc_result)
    if rpc_err:
        raise HTTPException(
            status_code=500, detail=f"Failed in create_household: {rpc_err}"
        )

    rpc_data = _resp_data(rpc_result)
    if not rpc_data:
        raise HTTPException(
            status_code=500, detail="Failed in create_household: no data returned"
        )

    household_row = rpc_data[0] if isinstance(rpc_data, list) else rpc_data
    return household_row


async def get_or_create_primary_household(user: User, name: str):
    household_id = await get_primary_household_id(user)

    if household_id:
        return household_id

    return await create_default_household(user, name)

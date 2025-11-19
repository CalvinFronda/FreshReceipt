from typing import Optional

from pydantic import BaseModel


class HouseholdBase(BaseModel):
    """Base household model"""

    name: str


class HouseholdCreate(HouseholdBase):
    """model for creating a new household"""

    name: str


class Household(HouseholdBase):
    """Household model"""

    id: str
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class HouseholdMember(BaseModel):
    """Household memeber model"""

    id: str
    household_id: str
    user_id: str
    role: str
    joined_at: Optional[str] = None

    class Config:
        from_attributes = True


class HouseholdWithRole(Household):
    """Household with user's role"""

    role: str


class InviteMemberRequest(BaseModel):
    """Request to invite a member to household"""

    email: str
    role: str = "member"

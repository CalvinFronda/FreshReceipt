"""Food items models for receipt line items."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FoodItemBase(BaseModel):
    """Base food item model."""

    household_id: str
    receipt_id: str
    added_by: str
    name: str
    category_id: str
    price: float
    quantity: int
    unit: Optional[str] = None
    purchase_date: datetime
    storage_location: Optional[str] = None


class FoodItemCreate(FoodItemBase):
    """Model for creating a food item."""

    expiry_date: Optional[datetime] = None
    manual_expiry: bool = False


class FoodItem(FoodItemCreate):
    """Food item model with database fields."""

    id: str
    is_consumed: bool = False
    consumed_date: Optional[datetime] = None
    consumed_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ReceiptBase(BaseModel):
    """Base receipt model"""

    household_id: str
    purchase_date: datetime
    store_name: Optional[str] = None
    total_amount: Optional[float] = None


class ReceiptCreate(ReceiptBase):
    """Model for creating a new receipt"""

    image_url: Optional[str] = None


class ReceiptUpdate(BaseModel):
    """Model for updating a receipt"""

    store_name: Optional[str] = None
    total_amount: Optional[float] = None
    purchase_date: Optional[datetime] = None
    ocr_status: Optional[str] = None
    ocr_confidence: Optional[float] = None
    processing_error: Optional[str] = None


class Receipt(ReceiptBase):
    """Receipt model"""

    id: str
    image_url: Optional[str] = None
    ocr_status: Optional[str] = None
    ocr_confidence: Optional[float] = None
    processing_error: Optional[str] = None
    uploaded_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class ReceiptUploadResponse(BaseModel):
    """Response model for receipt upload"""

    id: str
    image_url: str
    household_id: str
    purchase_date: datetime
    ocr_status: Optional[str] = None
    created_at: Optional[str] = None


class ReceiptUploadRequest(BaseModel):
    """Request model for receipt upload (form data)"""

    household_id: str
    purchase_date: datetime

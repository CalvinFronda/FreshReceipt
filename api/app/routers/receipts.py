import asyncio
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.supabase import supabase
from app.dependencies.auth import get_current_user
from app.dependencies.household import get_current_household, verify_household_access
from app.models.auth import User
from app.models.receipt import Receipt, ReceiptUploadResponse
from app.services.storage_service import upload_receipt_image

router = APIRouter(prefix="/receipts", tags=["Receipts"])

# Allowed image MIME types
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}

# Allowed file extensions
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename."""
    if "." not in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have an extension",
        )
    return filename.rsplit(".", 1)[1].lower()


@router.post(
    "/upload", response_model=ReceiptUploadResponse, status_code=status.HTTP_201_CREATED
)
async def upload_receipt(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    household: str = Depends(get_current_household),
):
    """
    Upload a receipt image and create a receipt record.

    Requires:
    - Valid JWT token
    - User must be a member of the household
    - Image file (JPEG, PNG, or WebP)
    """
    try:
        # Validate file type
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}",
            )

        # Get file extension
        file_extension = get_file_extension(file.filename)

        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        # Read file content
        file_content = await file.read()

        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 10MB limit",
            )

        # Upload image to Supabase Storage
        image_url = await upload_receipt_image(
            file_content=file_content,
            file_extension=file_extension,
            current_user=current_user,
            household_id=household,
        )

        from app.core.supabase import supabase_admin

        # Create receipt record in database
        purchase_date = (
            datetime.now(timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )

        receipt_data = {
            "household_id": household,
            "purchase_date": purchase_date,
            "image_url": image_url,
            "uploaded_by": current_user.id,
            "ocr_status": "pending",
        }

        result = await asyncio.to_thread(
            lambda: supabase_admin.table("receipts").insert(receipt_data).execute()
        )

        if hasattr(result, "error") and result.error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create receipt record: {result.error}",
            )

        receipt = result.data[0] if result.data else None
        if not receipt:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create receipt record",
            )

        return ReceiptUploadResponse(
            id=receipt["id"],
            image_url=receipt["image_url"],
            household_id=receipt["household_id"],
            purchase_date=datetime.fromisoformat(receipt["purchase_date"]),
            ocr_status=receipt.get("ocr_status"),
            created_at=receipt.get("created_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload receipt: {str(e)}",
        )


@router.get("", response_model=List[Receipt])
async def list_receipts(
    household_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get all receipts for a household.

    Requires:
    - Valid JWT token
    - User must be a member of the household
    """
    try:
        # Verify user has access to the household
        await verify_household_access(
            household_id=household_id, current_user=current_user
        )

        import asyncio

        result = await asyncio.to_thread(
            lambda: (
                supabase.table("receipts")
                .select("*")
                .eq("household_id", household_id)
                .order("created_at")
                .execute()
            )
        )

        if hasattr(result, "error") and result.error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch receipts: {result.error}",
            )

        return result.data or []

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch receipts: {str(e)}",
        )


@router.get("/{receipt_id}", response_model=Receipt)
async def get_receipt(
    receipt_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific receipt by ID.

    Requires:
    - Valid JWT token
    - User must be a member of the household that owns the receipt
    """
    try:
        import asyncio

        # First, get the receipt to find its household_id
        result = await asyncio.to_thread(
            lambda: (
                supabase.table("receipts")
                .select("*")
                .eq("id", receipt_id)
                .single()
                .execute()
            )
        )

        if hasattr(result, "error") and result.error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found"
            )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found"
            )

        receipt = result.data

        # Verify user has access to the household
        await verify_household_access(
            household_id=receipt["household_id"], current_user=current_user
        )

        return receipt

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch receipt: {str(e)}",
        )


@router.post(
    "/{receipt_id}/process-ocr", response_model=Receipt, status_code=status.HTTP_200_OK
)
async def process_receipt_ocr(
    receipt_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Trigger OCR processing for a receipt using Veryfi API.

    This endpoint processes the receipt image and extracts data like:
    - Store name
    - Total amount
    - Tax information
    - Line items
    - Confidence score

    Requires:
    - Valid JWT token
    - User must be a member of the household that owns the receipt
    - Receipt must have an image_url
    """
    try:
        from app.services.ocr_service import ocr_service

        # First, get the receipt to find its household_id and image_url
        result = await asyncio.to_thread(
            lambda: (
                supabase.table("receipts")
                .select("*")
                .eq("id", receipt_id)
                .single()
                .execute()
            )
        )

        if hasattr(result, "error") and result.error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found"
            )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found"
            )

        receipt = result.data

        # Verify user has access to the household
        await verify_household_access(
            household_id=receipt["household_id"], current_user=current_user
        )

        # Verify receipt has an image
        if not receipt.get("image_url"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Receipt does not have an image",
            )

        # Trigger OCR processing (non-blocking - process in background)
        # In production, this could be queued to a background task
        try:
            await ocr_service.process_receipt_from_url(
                image_url=receipt["image_url"],
                receipt_id=receipt_id,
                household_id=receipt["household_id"],
                user_id=current_user.id,
            )

            # Fetch and return updated receipt
            updated_result = await asyncio.to_thread(
                lambda: (
                    supabase.table("receipts")
                    .select("*")
                    .eq("id", receipt_id)
                    .single()
                    .execute()
                )
            )

            if hasattr(updated_result, "error") and updated_result.error:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch updated receipt",
                )

            return updated_result.data

        except Exception as e:
            # OCR processing failed, but receipt still exists
            # The error has been stored in the receipt record
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OCR processing failed: {str(e)}",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process receipt OCR: {str(e)}",
        )

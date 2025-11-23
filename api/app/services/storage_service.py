import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.supabase import supabase_admin
from app.models.auth import User

EXPIRES_IN = 300


async def upload_receipt_image(
    file_content: bytes,
    file_extension: str,
    current_user: User,
    household_id: str,
) -> str:
    """
    Upload a receipt image to Supabase Storage.

    Args:
        file_content: The image file content as bytes
        file_extension: File extension (e.g., 'jpg', 'png', 'jpeg')
        current_user: The authenticated user object
        household_id: The household ID to organize the upload

    Returns:
        Storage path of the uploaded image

    Raises:
        HTTPException: If upload fails
    """
    try:
        # Resolve user_id from the authenticated user
        user_id = getattr(current_user, "id", None) or (
            current_user.get("id") if isinstance(current_user, dict) else None
        )
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated user required for upload",
            )

        if not household_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="household_id required for upload",
            )

        # Generate unique filename: receipts/{household_id}/{user_id}/{timestamp}_{uuid}.{ext}
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"receipts/{household_id}/{timestamp}_{unique_id}.{file_extension}"

        # Upload to Supabase Storage bucket 'receipts'
        result = await asyncio.to_thread(
            lambda: supabase_admin.storage.from_("receipts").upload(
                path=filename,
                file=file_content,
                file_options={"content-type": f"image/{file_extension}"},
            )
        )

        # Check for errors - Supabase storage returns dict with 'error' key or raises exception
        if isinstance(result, dict) and result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image: {result['error']}",
            )

        # Get public URL - Supabase storage.create_signed_url
        # expires in a 5 mins
        signed_url_result = await asyncio.to_thread(
            lambda: supabase_admin.storage.from_("receipts").create_signed_url(
                filename, EXPIRES_IN
            )
        )

        # Handle different response formats
        if isinstance(signed_url_result, dict):
            if signed_url_result.get("error"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get signed URL: {signed_url_result['error']}",
                )

            signed_url = signed_url_result.get("signedURL")

            if signed_url:
                return signed_url

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage upload error: {str(e)}",
        )


async def delete_receipt_image(image_url: str) -> bool:
    """
    Delete a receipt image from Supabase Storage.

    Args:
        image_url: The public URL of the image to delete

    Returns:
        True if deletion was successful

    Raises:
        HTTPException: If deletion fails
    """
    try:
        # Extract path from URL
        # Supabase Storage URLs are typically: {SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}
        if "/storage/v1/object/public/receipts/" not in image_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image URL format",
            )

        path = image_url.split("/storage/v1/object/public/receipts/")[1]

        result = await asyncio.to_thread(
            lambda: supabase_admin.storage.from_("receipts").remove([path])
        )

        if hasattr(result, "error") and result.error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete image: {result.error}",
            )

        return True

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage deletion error: {str(e)}",
        )

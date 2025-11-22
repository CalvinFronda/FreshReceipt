"""
OCR Service for processing receipts using Veryfi API.
Handles document upload, processing, and data extraction.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.core.supabase import supabase

logger = logging.getLogger(__name__)


def get_nested(data, path, default=None):
    keys = path.split(".")
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return default
        if data is None:
            return default
    return data


class VeryfiOCRService:
    """Service for handling Veryfi OCR operations."""

    def __init__(self):
        """Initialize Veryfi OCR service with credentials from config."""
        self.client_id = settings.VERYFI_CLIENT_ID
        self.api_key = settings.VERYFI_API_KEY
        self.username = settings.VERYFI_USERNAME
        self.base_url = settings.VERYFI_URL

    def _get_auth_header(self) -> str:
        """
        Generate Veryfi authorization header.

        Returns:
            Authorization header value in format "apikey {username}:{api_key}"
        """
        return f"apikey {self.username}:{self.api_key}"

    async def process_receipt_from_url(
        self,
        image_url: str,
        receipt_id: str,
        household_id: str,
    ) -> Dict[str, Any]:
        """
        Process a receipt image from a URL using Veryfi OCR.

        Args:
            image_url: The public URL of the receipt image (from Supabase Storage)
            receipt_id: The ID of the receipt record in the database
            household_id: The household ID for the receipt

        Returns:
            Dictionary with OCR results containing extracted data

        Raises:
            Exception: If OCR processing fails
        """
        try:
            # Update receipt status to "processing"
            await self._update_receipt_status(receipt_id, "processing")

            # Call Veryfi API
            ocr_response = await self._call_veryfi_api(image_url)

            if not ocr_response:
                raise Exception("Empty response from Veryfi API")

            # Extract relevant data from Veryfi response
            extracted_data = self._extract_data_from_response(ocr_response)

            # Update receipt with OCR results
            await self._update_receipt_with_ocr_data(receipt_id, extracted_data)

            # Update receipt status to "completed"
            await self._update_receipt_status(receipt_id, "completed")

            return extracted_data

        except Exception as e:
            logger.error(f"OCR processing failed for receipt {receipt_id}: {str(e)}")
            # Update receipt status to "failed" and store error
            await self._update_receipt_status(
                receipt_id, "failed", error_message=str(e)
            )
            raise

    async def _call_veryfi_api(self, image_url: str) -> Dict[str, Any]:
        """
        Call Veryfi API with the image URL.

        Args:
            image_url: The public URL of the receipt image

        Returns:
            The JSON response from Veryfi API

        Raises:
            Exception: If API call fails
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "CLIENT-ID": self.client_id,
            "AUTHORIZATION": self._get_auth_header(),
        }

        payload = {
            "file_url": image_url,
            "categories": [],
            "tags": [],
            "compute": True,
            "country": "US",
            "document_type": "receipt",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                )

                # Check for HTTP errors
                if response.status_code >= 400:
                    logger.error(
                        f"Veryfi API error {response.status_code}: {response.text}"
                    )
                    raise Exception(
                        f"Veryfi API error: {response.status_code} - {response.text}"
                    )

                return response.json()

        except httpx.RequestError as e:
            logger.error(f"Veryfi API request failed: {str(e)}")
            raise Exception(f"Failed to connect to Veryfi API: {str(e)}")
        except Exception as e:
            logger.error(f"Veryfi API call error: {str(e)}")
            raise

    def _extract_data_from_response(
        self, veryfi_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract relevant data from Veryfi API response.

        Veryfi response format includes:
        - vendor/merchant info (name, phone, website)
        - line items
        - totals
        - tax information
        - date/time
        - payment method
        - etc.

        Args:
            veryfi_response: The full response from Veryfi API

        Returns:
            Simplified dictionary with extracted data
        """
        try:
            # Extract key fields from Veryfi response

            extracted = {
                "store_name": get_nested(
                    veryfi_response, "vendor.name.value", "Unknown"
                ),
                "total_amount": get_nested(veryfi_response, "total.value", None),
                "subtotal": get_nested(veryfi_response, "subtotal.value", None),
                "tax": get_nested(veryfi_response, "tax.value", None),
                "currency": get_nested(veryfi_response, "currency_code.value", None),
                "purchase_date": get_nested(veryfi_response, "date.value", None),
                "line_items": veryfi_response.get("line_items", []),
                "payment_method": get_nested(
                    veryfi_response, "payment.type.value", None
                ),
                "document_reference": get_nested(
                    veryfi_response, "invoice_number.value", None
                ),
                "ocr_confidence": get_nested(
                    veryfi_response, "meta.exif.AFConfidence", None
                ),
                "raw_response": veryfi_response,  # Store full response for debugging
            }

            return extracted

        except Exception as e:
            logger.error(f"Error extracting data from Veryfi response: {str(e)}")
            raise

    async def _update_receipt_status(
        self,
        receipt_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Update the OCR status of a receipt in the database.

        Args:
            receipt_id: The ID of the receipt record
            status: The new OCR status ("pending", "processing", "completed", "failed")
            error_message: Optional error message if status is "failed"
        """
        try:
            update_data = {
                "ocr_status": status,
                "updated_at": datetime.now(timezone.utc)
                .isoformat(timespec="microseconds")
                .replace("+00:00", "Z"),
            }

            if error_message:
                update_data["processing_error"] = error_message

            def update_receipt():
                return (
                    supabase.table("receipts")
                    .update(update_data)
                    .eq("id", receipt_id)
                    .execute()
                )

            result = await asyncio.to_thread(update_receipt)

            if hasattr(result, "error") and result.error:
                logger.error(f"Failed to update receipt status: {result.error}")
                raise Exception(f"Database error: {result.error}")

        except Exception as e:
            logger.error(f"Error updating receipt status: {str(e)}")
            # Don't re-raise here as this is an internal operation

    async def _update_receipt_with_ocr_data(
        self,
        receipt_id: str,
        extracted_data: Dict[str, Any],
    ) -> None:
        """
        Update the receipt record with extracted OCR data.

        Args:
            receipt_id: The ID of the receipt record
            extracted_data: The extracted data from OCR processing
        """
        try:
            # Prepare update payload with extracted OCR data
            update_data = {
                "store_name": extracted_data.get("store_name"),
                "total_amount": extracted_data.get("total_amount"),
                "ocr_confidence": extracted_data.get("ocr_confidence", 0),
                "updated_at": datetime.now(timezone.utc)
                .isoformat(timespec="microseconds")
                .replace("+00:00", "Z"),
            }

            def update_receipt():
                return (
                    supabase.table("receipts")
                    .update(update_data)
                    .eq("id", receipt_id)
                    .execute()
                )

            result = await asyncio.to_thread(update_receipt)

            if hasattr(result, "error") and result.error:
                logger.error(f"Failed to update receipt with OCR data: {result.error}")
                raise Exception(f"Database error: {result.error}")

            logger.info(f"Receipt {receipt_id} updated with OCR data")

        except Exception as e:
            logger.error(f"Error updating receipt with OCR data: {str(e)}")
            raise


# Global instance
ocr_service = VeryfiOCRService()

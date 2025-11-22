import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from helpers import get_nested

from app.core.config import settings
from app.core.supabase import supabase

logger = logging.getLogger(__name__)


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
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Process a receipt image from a URL using Veryfi OCR.

        Args:
            image_url: The public URL of the receipt image (from Supabase Storage)
            receipt_id: The ID of the receipt record in the database
            household_id: The household ID for the receipt
            user_id: The ID of the user who uploaded the receipt (for added_by)

        Returns:
            Dictionary with OCR results containing extracted data
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

            try:
                await self._create_food_items_from_receipt(
                    receipt_id=receipt_id,
                    household_id=household_id,
                    user_id=user_id,
                    extracted_data=extracted_data,
                )
            except Exception as e:
                logger.error(
                    f"Failed to create food items for receipt {receipt_id}: {str(e)}"
                )

            await self._update_receipt_status(receipt_id, "completed")

            return extracted_data

        except Exception as e:
            logger.error(f"OCR processing failed for receipt {receipt_id}: {str(e)}")
            await self._update_receipt_status(
                receipt_id, "failed", error_message=str(e)
            )
            raise

    async def _call_veryfi_api(self, image_url: str) -> Dict[str, Any]:
        """
        Call Veryfi API with the image as base64-encoded data.

        Downloads the image from the provided URL, encodes it as base64,
        and sends it to Veryfi API in the JSON payload.

        Args:
            image_url: The public URL of the receipt image

        Returns:
            The JSON response from Veryfi API
        """
        headers = {
            "Accept": "application/json",
            "CLIENT-ID": self.client_id,
            "AUTHORIZATION": self._get_auth_header(),
            "Content-Type": "application/json",
        }
        payload = {
            "file_urls": [image_url],
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

        Args:
            veryfi_response: The full response from Veryfi API

        Returns:
            Simplified dictionary with extracted data
        """
        try:
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

    async def _create_food_items_from_receipt(
        self,
        receipt_id: str,
        household_id: str,
        user_id: str,
        extracted_data: Dict[str, Any],
    ) -> None:
        """
        Create food items from receipt line items.

        Args:
            receipt_id: The ID of the receipt
            household_id: The household ID
            user_id: The user ID (added_by)
            extracted_data: The extracted data from OCR processing
        """
        try:
            line_items = extracted_data.get("line_items", [])
            if not line_items:
                logger.info(f"No line items found for receipt {receipt_id}")
                return

            # Fetch the purchase date from extracted data
            purchase_date = extracted_data.get("purchase_date")
            if isinstance(purchase_date, str):
                purchase_date = datetime.fromisoformat(
                    purchase_date.replace("Z", "+00:00")
                )
            elif isinstance(purchase_date, datetime):
                pass
            else:
                # Fallback to now if not available
                purchase_date = datetime.now(timezone.utc)

            # Hardcoded constants going to change when we get categories working
            OTHER_CATEGORY_ID = "1884005d-dcbe-4632-b99e-ad379778e500"
            DEFAULT_STORAGE = "fridge"
            DEFAULT_EXPIRY_DAYS = 30  # Fallback: 30 days if category has no default

            # Fetch default expiry days for the "other" category
            default_expiry_days = await self._get_category_default_expiry(
                OTHER_CATEGORY_ID
            )

            # Use fallback if category default not found
            if default_expiry_days is None:
                default_expiry_days = DEFAULT_EXPIRY_DAYS
                logger.info(f"Using fallback expiry days: {DEFAULT_EXPIRY_DAYS} days")

            # Transform line items to food items
            food_items = []
            for line_item in line_items:
                try:
                    name = self._extract_line_item_name(line_item)
                    if not name:
                        logger.warning(f"Skipping line item with no name: {line_item}")
                        continue

                    price = self._extract_line_item_price(line_item)
                    quantity = self._extract_line_item_quantity(line_item)

                    # Calculate expiry date - always provide a value
                    if default_expiry_days and default_expiry_days > 0:
                        from datetime import timedelta

                        expiry_date = purchase_date + timedelta(
                            days=default_expiry_days
                        )
                    else:
                        # Fallback: use 30 days if somehow it's still invalid
                        from datetime import timedelta

                        expiry_date = purchase_date + timedelta(days=30)

                    food_item = {
                        "household_id": household_id,
                        "receipt_id": receipt_id,
                        "added_by": user_id,
                        "name": name,
                        "category_id": OTHER_CATEGORY_ID,
                        "price": price,
                        "quantity": quantity,
                        "unit": None,
                        "purchase_date": purchase_date.isoformat(
                            timespec="microseconds"
                        ).replace("+00:00", "Z"),
                        "expiry_date": expiry_date.isoformat(
                            timespec="microseconds"
                        ).replace("+00:00", "Z"),
                        "manual_expiry": False,
                        "is_consumed": False,
                        "storage_location": DEFAULT_STORAGE,
                    }
                    food_items.append(food_item)

                except Exception as e:
                    logger.warning(f"Error processing line item: {str(e)}, skipping...")
                    continue

            if not food_items:
                logger.info(f"No valid food items to create for receipt {receipt_id}")
                return

            # Batch insert food items
            def insert_food_items():
                return supabase.table("food_items").insert(food_items).execute()

            result = await asyncio.to_thread(insert_food_items)

            if hasattr(result, "error") and result.error:
                raise Exception(f"Database error: {result.error}")

            logger.info(
                f"Created {len(food_items)} food items for receipt {receipt_id}"
            )

        except Exception as e:
            logger.error(f"Error creating food items from receipt: {str(e)}")
            raise

    async def _get_category_default_expiry(self, category_id: str) -> Optional[int]:
        """
        Get the default shelf life days for a food category.

        Args:
            category_id: The ID of the food category

        Returns:
            The default shelf life days, or None if not found
        """
        try:

            def fetch_category():
                return (
                    supabase.table("food_categories")
                    .select("default_shelf_life_days")
                    .eq("id", category_id)
                    .single()
                    .execute()
                )

            result = await asyncio.to_thread(fetch_category)

            if hasattr(result, "error") and result.error:
                logger.warning(
                    f"Could not fetch category {category_id}: {result.error}"
                )
                return None

            if result.data:
                return result.data.get("default_shelf_life_days")
            return None

        except Exception as e:
            logger.warning(f"Error fetching category default expiry: {str(e)}")
            return None

    def _extract_line_item_name(self, line_item: Dict[str, Any]) -> Optional[str]:
        """
        Extract the item name from a Veryfi line item.

        Args:
            line_item: The line item from Veryfi response

        Returns:
            The item name, or None if not found
        """
        # Try different possible name fields
        name = (
            line_item.get("description")
            or line_item.get("full_description")
            or line_item.get("normalized_description")
            or get_nested(line_item, "product_info.expanded_description")
        )
        return name.strip() if name else None

    def _extract_line_item_price(self, line_item: Dict[str, Any]) -> float:
        """
        Extract the price from a Veryfi line item.

        Defaults to 1 if not found.

        Args:
            line_item: The line item from Veryfi response

        Returns:
            The price, or 1.0 if not found
        """
        price = line_item.get("total") or line_item.get("price")
        try:
            return float(price) if price else 1.0
        except (ValueError, TypeError):
            return 1.0

    def _extract_line_item_quantity(self, line_item: Dict[str, Any]) -> int:
        """
        Extract the quantity from a Veryfi line item.

        Defaults to 1 if not found.

        Args:
            line_item: The line item from Veryfi response

        Returns:
            The quantity, or 1 if not found
        """
        quantity = line_item.get("quantity")
        try:
            return int(quantity) if quantity else 1
        except (ValueError, TypeError):
            return 1


ocr_service = VeryfiOCRService()

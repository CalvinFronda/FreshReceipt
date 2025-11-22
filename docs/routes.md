# Routes

/api/v1/receipts/{receipt_id}/process-ocr
With a receipt ID this will look into the database, check if ID is valid then find the url saved in the table. That url should point to the supabase storage bucket and send that url to veryfi. We run the OCR in the background and save each item in the reciept in food_items table.

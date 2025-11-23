# Learnings

Heres some stuff im learning while building this project.

## RLS (Row Level Security)

postgresSQL has RLS. For any frontend facing APIs - you need to either be authenticated or part of a service role see `api/app/core/supabase.py`

`get_authenticated_supabase` will always be looking for the JWT token in the request
`get_supabase_admin_client` will bypass all RLS policies. This should only be used for backend operations like running the ocr after a user uploads a receipt.

Its important to remember the two types of clients. You never want to have a client making a request to the `get_supabase_admin_client` since they will basically have access to do whatever.

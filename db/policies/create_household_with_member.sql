-- Creates a DB-side RPC to atomically create a household and its initial member.
-- This function accepts a single JSONB parameter so PostgREST/Supabase can call it
-- with named keys: supabase.rpc('create_household_with_member', { payload: { user_id: ..., email: ..., name: ... } })

BEGIN;

CREATE OR REPLACE FUNCTION public.create_household_with_member(payload jsonb)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  uid uuid;
  user_email text;
  household_name text;
  h_row public.households%ROWTYPE;
BEGIN
  -- extract and validate inputs
  uid := (payload ->> 'user_id')::uuid;
  user_email := payload ->> 'email';
  household_name := COALESCE(payload ->> 'name', concat(user_email, '''s Household'));

  -- create household and set created_by to the provided user id
  INSERT INTO public.households (name, created_by)
  VALUES (household_name, uid)
  RETURNING * INTO h_row;

  -- add the initial member as owner
  INSERT INTO public.household_members (household_id, user_id, role)
  VALUES (h_row.id, uid, 'owner');

  -- return the created household row as JSON
  RETURN row_to_json(h_row)::jsonb;
END;
$$;

COMMIT;


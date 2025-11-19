-- Purpose: Replace recursive RLS policies that query `household_members` from within
-- `household_members` policies (causes infinite recursion). Create a
-- SECURITY DEFINER helper for cross-table checks and safe policies.

BEGIN;

-- 1) Helper: safe, SECURITY DEFINER function to check membership
-- Important: this function must be owned by a role that can bypass RLS
-- (typically the DB owner / postgres). If you run this as the DB owner,
-- the ALTER FUNCTION OWNER TO <owner> line will succeed; otherwise remove it
-- or set appropriately.
CREATE OR REPLACE FUNCTION public.is_household_member(hid uuid, uid uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.household_members
    WHERE household_id = hid AND user_id = uid
  );
$$;

-- Optional: set function owner to the DB owner so it runs with an account
-- that has BYPASSRLS. Replace "postgres" below with your DB owner if needed.
-- Execute this line as the DB owner (or remove if you can't).
-- ALTER FUNCTION public.is_household_member(uuid, uuid) OWNER TO postgres;

-- 2) Remove any old policies that may reference household_members recursively.
DROP POLICY IF EXISTS household_members_select ON public.household_members;
DROP POLICY IF EXISTS household_members_insert ON public.household_members;
DROP POLICY IF EXISTS household_members_update ON public.household_members;
DROP POLICY IF EXISTS household_members_delete ON public.household_members;

-- 3) Create safe policies for household_members that do NOT query the same table.
-- These allow authenticated users to read/modify their own membership rows only.
CREATE POLICY household_members_select ON public.household_members
  FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY household_members_insert ON public.household_members
  FOR INSERT
  TO authenticated
  WITH CHECK (user_id = auth.uid());

CREATE POLICY household_members_update ON public.household_members
  FOR UPDATE
  TO authenticated
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY household_members_delete ON public.household_members
  FOR DELETE
  TO authenticated
  USING (user_id = auth.uid());

-- 4) Policies for households: allow access if the caller is a member.
-- Use the helper function to check membership. Because the function is
-- SECURITY DEFINER and owned by the DB owner, it will not re-trigger the
-- household_members policies and avoids recursion.
DROP POLICY IF EXISTS households_select_if_member ON public.households;
CREATE POLICY households_select_if_member ON public.households
  FOR SELECT
  TO authenticated
  USING (public.is_household_member(id, auth.uid()));

-- Example: allow inserts to households only to authenticated users,
-- typically handled by your application logic; here we permit inserts
-- if created_by equals auth.uid(). Adjust as needed for your app.
DROP POLICY IF EXISTS households_insert ON public.households;
CREATE POLICY households_insert ON public.households
  FOR INSERT
  TO authenticated
  WITH CHECK (created_by = auth.uid());

COMMIT;

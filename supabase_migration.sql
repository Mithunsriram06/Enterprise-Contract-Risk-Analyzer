-- ═══════════════════════════════════════════════════════════════════════════
--  Enterprise Contract Risk Analyzer — Supabase Database Migration
--  Run this entire script in: Supabase Dashboard → SQL Editor → New Query
--  It is idempotent: safe to run multiple times (uses IF NOT EXISTS guards).
-- ═══════════════════════════════════════════════════════════════════════════


-- ── 1. PROFILES TABLE ────────────────────────────────────────────────────────
-- Stores a lightweight user profile mirroring auth.users.
-- The `id` column is a foreign key to Supabase's internal auth.users table.

CREATE TABLE IF NOT EXISTS public.profiles (
    id          UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email       TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index on email for fast lookups
CREATE INDEX IF NOT EXISTS profiles_email_idx ON public.profiles(email);

-- Automatically create a profile row whenever a new user signs up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, email)
    VALUES (NEW.id, NEW.email)
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

-- Attach the trigger to auth.users (drop first to avoid duplicates on re-run)
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();


-- ── 2. CONTRACT_LOGS TABLE ────────────────────────────────────────────────────
-- Stores every AI analysis result, linked to the user who ran it.
-- `analysis_payload` holds the full JSON returned by Gemini.

CREATE TABLE IF NOT EXISTS public.contract_logs (
    id                BIGSERIAL   PRIMARY KEY,
    user_id           UUID        NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    document_name     TEXT        NOT NULL,
    risk_score        INTEGER     NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    analysis_payload  JSONB       NOT NULL DEFAULT '{}'::JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Composite index: fast per-user history queries ordered by recency
CREATE INDEX IF NOT EXISTS contract_logs_user_created_idx
    ON public.contract_logs(user_id, created_at DESC);

-- GIN index: enables fast JSONB containment queries if needed later
CREATE INDEX IF NOT EXISTS contract_logs_payload_gin_idx
    ON public.contract_logs USING GIN (analysis_payload);


-- ── 3. ROW LEVEL SECURITY (RLS) ───────────────────────────────────────────────
-- RLS ensures users can only read and write their own data, even if the
-- Supabase anon key is exposed in the frontend bundle.

-- profiles: each user may only see and update their own profile row
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "profiles_select_own" ON public.profiles;
CREATE POLICY "profiles_select_own"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

DROP POLICY IF EXISTS "profiles_update_own" ON public.profiles;
CREATE POLICY "profiles_update_own"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- The INSERT is handled by the trigger which runs as SECURITY DEFINER,
-- so no explicit INSERT policy is needed for the anon role.


-- contract_logs: each user may only read and insert their own rows
ALTER TABLE public.contract_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "logs_select_own" ON public.contract_logs;
CREATE POLICY "logs_select_own"
    ON public.contract_logs FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "logs_insert_own" ON public.contract_logs;
CREATE POLICY "logs_insert_own"
    ON public.contract_logs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Prevent any user from deleting or modifying historical audit records
-- (omitting DELETE and UPDATE policies achieves this by default under RLS)


-- ── 4. GRANT PERMISSIONS ─────────────────────────────────────────────────────
-- Grant the anon and authenticated roles access to the public schema tables.
-- Supabase creates these roles automatically; we just grant table-level perms.

GRANT USAGE ON SCHEMA public TO anon, authenticated;

GRANT SELECT, INSERT, UPDATE ON public.profiles TO authenticated;
GRANT SELECT, INSERT           ON public.contract_logs TO authenticated;

-- Allow the sequence behind BIGSERIAL to be incremented by authenticated users
GRANT USAGE, SELECT ON SEQUENCE public.contract_logs_id_seq TO authenticated;


-- ── 5. VERIFICATION QUERY ─────────────────────────────────────────────────────
-- Run this separately after the migration to confirm everything was created.
/*
SELECT
    table_name,
    pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) AS size
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('profiles', 'contract_logs')
ORDER BY table_name;
*/

-- ─────────────────────────────────────────────────────────────────────────────
-- Migration complete.
-- ─────────────────────────────────────────────────────────────────────────────

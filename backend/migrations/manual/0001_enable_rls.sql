-- Enable Row Level Security on every NeetiAi table (run once; idempotent).
--
-- Why: the Supabase anon key ships to the browser (and is in this public repo's
-- history). With RLS off, that key alone can read and write every table through
-- Supabase's auto-generated REST API (/rest/v1/...). Enabling RLS with no
-- policies denies all anon/authenticated access via that API. The FastAPI backend
-- connects as the postgres role, which bypasses RLS, so the app is unaffected.
--
-- Non-destructive: no data or tables are changed. Phase 2 moves this into Alembic.
ALTER TABLE public."user"              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public."transaction"       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.budget              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chatlog             ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.investmentwatchlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.modelmetadata       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.incomesource        ENABLE ROW LEVEL SECURITY;

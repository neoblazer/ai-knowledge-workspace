-- Back up the database before applying this existing-database migration.
-- Legacy rows remain unowned until an administrator assigns a Clerk user_id.

begin;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'documents'
          AND column_name = 'id'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'documents'
          AND column_name = 'document_id'
    ) THEN
        ALTER TABLE public.documents
        RENAME COLUMN id TO document_id;
    END IF;
END $$;


-- Add Clerk ownership to documents.
ALTER TABLE public.documents
    ADD COLUMN IF NOT EXISTS user_id text;


-- Add ownership, document relationship, and citations to chat history.
ALTER TABLE public.chat_history
    ADD COLUMN IF NOT EXISTS user_id text,
    ADD COLUMN IF NOT EXISTS document_id uuid,
    ADD COLUMN IF NOT EXISTS citations jsonb NOT NULL DEFAULT '[]'::jsonb;


-- Add chat history -> document foreign key.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chat_history_document_id_fkey'
    ) THEN
        ALTER TABLE public.chat_history
            ADD CONSTRAINT chat_history_document_id_fkey
            FOREIGN KEY (document_id)
            REFERENCES public.documents(document_id)
            ON DELETE CASCADE
            NOT VALID;
    END IF;
END $$;


-- Indexes for user-scoped document and chat queries.
CREATE INDEX IF NOT EXISTS documents_user_id_idx
    ON public.documents(user_id);

CREATE UNIQUE INDEX IF NOT EXISTS documents_user_document_id_idx
    ON public.documents(user_id, document_id);

CREATE INDEX IF NOT EXISTS chat_history_user_document_idx
    ON public.chat_history(user_id, document_id, created_at DESC);


-- Enable Row Level Security.
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history ENABLE ROW LEVEL SECURITY;


-- Remove the old permissive development policies.
DROP POLICY IF EXISTS "Allow document insert"
    ON public.documents;

DROP POLICY IF EXISTS "Allow document select"
    ON public.documents;

DROP POLICY IF EXISTS "Allow chat insert"
    ON public.chat_history;

DROP POLICY IF EXISTS "Allow chat select"
    ON public.chat_history;

DROP POLICY IF EXISTS "Users manage their documents"
    ON public.documents;

DROP POLICY IF EXISTS "Users manage their chat history"
    ON public.chat_history;


-- Anonymous clients must not access these tables directly.
REVOKE ALL ON public.documents FROM anon;
REVOKE ALL ON public.chat_history FROM anon;


-- These policies apply if Clerk is configured as a Supabase
-- third-party authentication provider.
--
-- The current FastAPI backend uses a Supabase server-side secret/service-role
-- key, which bypasses RLS. FastAPI therefore performs its own mandatory
-- ownership checks using the verified Clerk user_id.

CREATE POLICY "Users manage their documents"
ON public.documents
FOR ALL
TO authenticated
USING (
    (auth.jwt() ->> 'sub') = user_id
)
WITH CHECK (
    (auth.jwt() ->> 'sub') = user_id
);


CREATE POLICY "Users manage their chat history"
ON public.chat_history
FOR ALL
TO authenticated
USING (
    (auth.jwt() ->> 'sub') = user_id
)
WITH CHECK (
    (auth.jwt() ->> 'sub') = user_id
);


-- The FastAPI backend connects with the Supabase service_role / secret key.
-- Explicitly grant the table privileges required by the backend.
--
-- RLS is still bypassed by service_role, so every backend database operation
-- must remain scoped by the verified Clerk user_id.

GRANT USAGE ON SCHEMA public TO service_role;

GRANT SELECT, INSERT, UPDATE, DELETE
ON TABLE public.documents
TO service_role;

GRANT SELECT, INSERT, UPDATE, DELETE
ON TABLE public.chat_history
TO service_role;


commit;


-- ---------------------------------------------------------------------------
-- FINAL VALIDATION
-- ---------------------------------------------------------------------------
--
-- After assigning every retained legacy row to its real Clerk user and
-- document UUID, or after deleting legacy development data and starting fresh,
-- enforce these constraints:
--
-- ALTER TABLE public.documents
--     ALTER COLUMN user_id SET NOT NULL;
--
-- ALTER TABLE public.chat_history
--     ALTER COLUMN user_id SET NOT NULL;
--
-- ALTER TABLE public.chat_history
--     ALTER COLUMN document_id SET NOT NULL;
--
-- ALTER TABLE public.chat_history
--     VALIDATE CONSTRAINT chat_history_document_id_fkey;
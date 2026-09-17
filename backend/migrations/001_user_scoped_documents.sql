-- Back up the database before applying this existing-database migration.
-- Legacy rows remain unowned until an administrator assigns a Clerk user_id.

begin;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'documents' AND column_name = 'id'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'documents' AND column_name = 'document_id'
    ) THEN
        ALTER TABLE public.documents RENAME COLUMN id TO document_id;
    END IF;
END $$;

ALTER TABLE public.documents ADD COLUMN IF NOT EXISTS user_id text;
ALTER TABLE public.chat_history
    ADD COLUMN IF NOT EXISTS user_id text,
    ADD COLUMN IF NOT EXISTS document_id uuid,
    ADD COLUMN IF NOT EXISTS citations jsonb NOT NULL DEFAULT '[]'::jsonb;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chat_history_document_id_fkey'
    ) THEN
        ALTER TABLE public.chat_history
            ADD CONSTRAINT chat_history_document_id_fkey
            FOREIGN KEY (document_id)
            REFERENCES public.documents(document_id)
            ON DELETE CASCADE
            NOT VALID;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS documents_user_id_idx ON public.documents(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS documents_user_document_id_idx
    ON public.documents(user_id, document_id);
CREATE INDEX IF NOT EXISTS chat_history_user_document_idx
    ON public.chat_history(user_id, document_id, created_at DESC);

ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow document insert" ON public.documents;
DROP POLICY IF EXISTS "Allow document select" ON public.documents;
DROP POLICY IF EXISTS "Allow chat insert" ON public.chat_history;
DROP POLICY IF EXISTS "Allow chat select" ON public.chat_history;
DROP POLICY IF EXISTS "Users manage their documents" ON public.documents;
DROP POLICY IF EXISTS "Users manage their chat history" ON public.chat_history;

REVOKE ALL ON public.documents FROM anon;
REVOKE ALL ON public.chat_history FROM anon;

-- These policies apply if Clerk is configured as a Supabase third-party auth
-- provider. The current service-role backend bypasses RLS and enforces the same
-- ownership checks in every query.
CREATE POLICY "Users manage their documents"
ON public.documents
FOR ALL
TO authenticated
USING ((auth.jwt() ->> 'sub') = user_id)
WITH CHECK ((auth.jwt() ->> 'sub') = user_id);

CREATE POLICY "Users manage their chat history"
ON public.chat_history
FOR ALL
TO authenticated
USING ((auth.jwt() ->> 'sub') = user_id)
WITH CHECK ((auth.jwt() ->> 'sub') = user_id);

commit;

-- After assigning every retained legacy row to its real Clerk user, enforce:
-- ALTER TABLE public.documents ALTER COLUMN user_id SET NOT NULL;
-- ALTER TABLE public.chat_history ALTER COLUMN user_id SET NOT NULL;
-- ALTER TABLE public.chat_history ALTER COLUMN document_id SET NOT NULL;
-- ALTER TABLE public.chat_history VALIDATE CONSTRAINT chat_history_document_id_fkey;

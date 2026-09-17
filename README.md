# AI Knowledge Workspace

AI Knowledge Workspace is an authenticated full-stack retrieval-augmented generation (RAG) application. Users upload PDFs, search only documents they own, ask grounded questions, receive page-aware citations, and review persistent chat history.

The project remains a practical two-process portfolio application: React/Vite provides the UI, FastAPI exposes the API, Clerk supplies identity, PyPDF extracts pages, Sentence Transformers and ChromaDB provide local semantic retrieval, Gemini generates grounded answers, and Supabase stores relational metadata.

## Features

- Clerk sign-in in React and verified Clerk session JWTs in FastAPI
- Bearer authentication on every document and chat endpoint
- Backend-enforced per-user document and chat-history isolation
- UUID `document_id` values across Supabase, ChromaDB, APIs, and browser selection
- Safe UUID-based server filenames; original names are display metadata only
- PDF extension, MIME, signature, size, and extractable-text validation
- Page-by-page extraction and page-aware chunks/citations
- Configurable embedding model, chunking, top-k, optional distance threshold, CORS, and API URL
- Duplicate retrieval suppression
- Gemini answers constrained to retrieved context with safe failure responses
- Owner-only deletion of vectors, chat history, local PDF, and document metadata
- Mocked backend tests that need no real external services or credentials

## Architecture

```text
React + Vite + Clerk
  |  getToken() -> Authorization: Bearer <session JWT>
  v
FastAPI
  |-- Clerk authenticate_request() -> verified JWT `sub` -> trusted user_id
  |-- Upload: validate -> UUID file -> page extraction -> chunks
  |           -> MiniLM embeddings -> scoped Chroma -> scoped Supabase row
  |-- Ask: ownership check -> scoped retrieval -> Gemini -> citations/history
  `-- Delete: ownership check -> Chroma -> history -> PDF -> metadata
```

The browser never sends a trusted user ID. The backend derives identity from the verified token and adds that ID to every Supabase and Chroma ownership query.

## Stack

### Frontend

- React 19, Vite 8, React Router 7
- Clerk React, Axios
- Tailwind CSS 4, Lucide React, React Hot Toast
- ESLint

### Backend

- Python 3.10+ (developed with Python 3.11)
- FastAPI, Uvicorn, Pydantic
- Official `clerk-backend-api` SDK
- PyPDF
- ChromaDB and Sentence Transformers (`all-MiniLM-L6-v2` by default)
- Google Gen AI SDK (`gemini-2.5-flash` by default)
- Supabase PostgreSQL
- pytest

## Project structure

```text
ai-knowledge-workspace/
|-- README.md
|-- .gitignore
|-- backend/
|   |-- main.py
|   |-- config.py                    # Central environment configuration
|   |-- auth.py                      # Reusable Clerk dependency
|   |-- schemas.py                   # Typed request/citation models
|   |-- requirements.txt
|   |-- requirements-dev.txt
|   |-- .env.example
|   |-- routes/
|   |   |-- document_routes.py       # Upload, list, delete
|   |   `-- chat_routes.py           # Ask and history
|   |-- services/
|   |   |-- pdf_service.py           # Page extraction and chunking
|   |   |-- rag_service.py           # Embeddings and Chroma operations
|   |   |-- gemini_service.py        # Grounded answer generation
|   |   `-- db_service.py            # Scoped Supabase operations
|   |-- migrations/
|   |   `-- 001_user_scoped_documents.sql
|   `-- tests/
|       |-- conftest.py
|       |-- test_auth.py
|       |-- test_documents.py
|       |-- test_rag.py
|       `-- test_chat.py
`-- frontend/
    |-- .env.example
    |-- package.json
    |-- vite.config.js
    |-- eslint.config.js
    `-- src/
        |-- main.jsx
        |-- App.jsx
        |-- index.css
        `-- api/api.js
```

## Authentication flow

1. Clerk React signs the user in.
2. Each protected frontend call obtains a current token with `getToken()`.
3. Axios sends `Authorization: Bearer <token>`.
4. FastAPI's `get_current_user()` calls Clerk's `authenticate_request()` and accepts only session tokens.
5. Clerk verifies signature, expiry, and `azp` against `CLERK_AUTHORIZED_PARTIES`.
6. The verified `sub` claim becomes the only trusted `user_id`.
7. Missing or invalid tokens return HTTP 401 without internal details.

`CLERK_JWT_KEY` enables networkless signature verification. Keep `CLERK_SECRET_KEY` and the JWT public key in backend configuration only.

## Document identity, RAG, and citations

Each upload generates a UUID. Chroma chunk IDs are:

```text
<document_id>_chunk_<chunk_index>
```

Chunk metadata contains `document_id`, verified `user_id`, original filename, one-based page number, and global chunk index. Retrieval filters on both `document_id` and `user_id`, suppresses duplicate text/page results, and optionally drops results beyond `RAG_MAX_DISTANCE`.

Citation response example:

```json
{
  "document_id": "4e11f51d-fbcd-4a03-b46b-27d5f1350c2f",
  "filename": "example.pdf",
  "page": 5,
  "chunk_index": 12,
  "distance": 0.21
}
```

The UI displays `example.pdf — Page 5`. Page numbers come from actual page-by-page extraction and are never fabricated.

## Environment variables

Copy the examples to `.env`; never commit the real files.

### Backend (`backend/.env`)

| Variable | Required | Purpose |
|---|---:|---|
| `GEMINI_API_KEY` | Yes | Gemini credential |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Backend-only Supabase key |
| `CLERK_SECRET_KEY` | Yes | Clerk backend SDK credential |
| `CLERK_JWT_KEY` | Recommended | PEM public key; escaped `\n` is supported |
| `CLERK_AUTHORIZED_PARTIES` | Yes | Comma-separated trusted frontend origins |
| `ALLOWED_ORIGINS` | Yes | Comma-separated CORS origins |
| `MAX_UPLOAD_SIZE_MB` | No | Default `10` |
| `UPLOAD_DIR` | No | Default `backend/uploads` |
| `CHROMA_PATH` | No | Default `backend/chroma_db` |
| `EMBEDDING_MODEL` | No | Default `all-MiniLM-L6-v2` |
| `CHUNK_SIZE` | No | Default `800` characters |
| `CHUNK_OVERLAP` | No | Default `150`; must be smaller than chunk size |
| `RAG_TOP_K` | No | Default `3` unique chunks |
| `RAG_MAX_DISTANCE` | No | Blank disables thresholding |
| `GEMINI_MODEL` | No | Default `gemini-2.5-flash` |

`SUPABASE_KEY` is retained as a compatibility fallback, but new deployments should use `SUPABASE_SERVICE_ROLE_KEY`. Never expose a service-role key to Vite or the browser.

### Frontend (`frontend/.env`)

| Variable | Required | Purpose |
|---|---:|---|
| `VITE_CLERK_PUBLISHABLE_KEY` | Yes | Public Clerk frontend key |
| `VITE_API_BASE_URL` | No | FastAPI URL; local fallback is `http://127.0.0.1:8000` |

## Supabase migration and RLS

Back up the database, then apply [`backend/migrations/001_user_scoped_documents.sql`](backend/migrations/001_user_scoped_documents.sql) in the Supabase SQL editor.

The migration:

- Renames `documents.id` to `document_id` when upgrading the original schema.
- Adds `user_id` to documents.
- Adds `user_id`, `document_id`, and JSONB `citations` to chat history.
- Adds a cascading document foreign key and ownership indexes.
- removes permissive anonymous policies/grants.
- Adds authenticated policies based on `auth.jwt() ->> 'sub'`.

The migration does not guess ownership. Assign retained legacy rows to their real Clerk user and document UUID, or delete development data and re-upload it. After backfilling, run the commented `NOT NULL`/constraint-validation statements at the end of the migration.

Legacy Chroma chunks are filename-addressed and lack ownership/page metadata, so secure queries intentionally cannot see them. Re-upload/re-index legacy PDFs, verify the new records, and then remove obsolete vector data.

The current FastAPI client uses the service-role key, which bypasses RLS; backend ownership filters are therefore mandatory and implemented. The included RLS policies support defense in depth if Clerk is later configured as a Supabase third-party auth provider. The browser does not access Supabase directly.

## Local development

### Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Configure backend/.env
uvicorn main:app --reload
```

- API: `http://127.0.0.1:8000`
- OpenAPI: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

### Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
# Configure frontend/.env
npm run dev
```

Frontend: `http://localhost:5173`

## API

Document/chat endpoints require a valid Clerk bearer token.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Public process message |
| GET | `/health` | Public process-level health response |
| POST | `/documents/upload` | Validate, store, chunk, embed, and register an owned PDF |
| GET | `/documents/` | List only the current user's documents |
| DELETE | `/documents/{document_id}` | Delete an owned document and related data |
| POST | `/chat/ask` | Ask against one owned document UUID |
| GET | `/chat/history?document_id=<uuid>` | Get scoped history |

Example:

```http
POST /chat/ask
Authorization: Bearer <clerk-session-token>
Content-Type: application/json
```

```json
{
  "question": "What is the main conclusion?",
  "document_id": "4e11f51d-fbcd-4a03-b46b-27d5f1350c2f"
}
```

Upload responses do not expose server filesystem paths.

## Tests and checks

Backend tests mock Clerk, Gemini, Supabase, embeddings, and Chroma; no real keys are required.

```powershell
cd backend
venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pytest -q
```

```powershell
cd frontend
npm run lint
npm run build
```

## Manual Clerk configuration

1. Create appropriate development/production Clerk instances.
2. Put only the publishable key in the frontend environment.
3. Put the secret key and JWT public key in the backend secret store.
4. Add exact frontend origins to `CLERK_AUTHORIZED_PARTIES`.
5. Add frontend domains and redirect URLs in the Clerk dashboard.
6. A custom JWT template is not required; the API reads the standard verified `sub` claim.

## Deployment

### Frontend (for example Vercel or Netlify)

- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- Configure `VITE_CLERK_PUBLISHABLE_KEY` and public HTTPS `VITE_API_BASE_URL`.
- Add the deployed origin to Clerk, `CLERK_AUTHORIZED_PARTIES`, and `ALLOWED_ORIGINS`.

### Backend (for example Render, Railway, Fly.io, or a VM)

- Use Python 3.11 or another tested Python 3.10+ runtime.
- Install `backend/requirements.txt`.
- Start from `backend`: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- Configure secrets through the hosting platform, never repository files.
- Use HTTPS and mount durable storage for uploads and Chroma.
- Start with one replica because local files/Chroma are not shared.
- Back up Supabase and persistent storage and monitor errors/latency.

Do not use stateless serverless hosting for FastAPI while the project depends on local PDFs and ChromaDB.

## Known limitations

- Local files/Chroma require persistent disk and limit horizontal scaling.
- Ingestion runs inside the request worker rather than a background queue.
- PyPDF has no OCR and may not preserve complex tables/layouts.
- Character chunks preserve pages but not semantic/token boundaries.
- Retrieval has no reranker or hybrid keyword search.
- Distance thresholds need corpus-specific evaluation.
- Multi-store ingestion/deletion is compensating logic, not a distributed transaction.
- The health endpoint does not probe external dependencies or disk.
- There is no browser E2E suite, rate limiter, malware scanner, or observability stack.
- Prompt instructions reduce but cannot eliminate document prompt injection.

## Production-aware backlog

- Add background ingestion and processing status.
- Add rate limiting, structured logs, request IDs, metrics, and dependency health checks.
- Add optional OCR for scanned PDFs.
- Move PDFs to object storage and vectors to a shared store before multi-replica deployment.
- Add browser E2E tests and CI.
- Evaluate chunking, top-k, and thresholds against a representative benchmark.
- Add retention/export controls and account-data deletion workflows.

## Research scope

This is a secure, explainable baseline RAG system, not a novel model or retrieval algorithm. Its portfolio value is the end-to-end engineering: verified identity propagation, multi-store authorization, UUID identity, page citations, grounded generation, safe failures, and mocked tests. Research claims would require datasets, baselines, metrics, and reproducible experiments beyond this application.

# AI Knowledge Workspace

AI Knowledge Workspace is a full-stack GenAI-powered RAG platform where users can upload PDF documents and chat with them using AI.

The system extracts text from PDFs, splits the content into chunks, generates embeddings, stores them in ChromaDB, retrieves relevant chunks based on user questions, and generates answers using Gemini AI.

## Features

- Clerk login and signup
- Protected dashboard, upload, and chat pages
- Upload PDF documents
- Extract PDF text using PyPDF
- Split extracted text into chunks
- Generate embeddings using Sentence Transformers
- Store embeddings in ChromaDB
- Ask questions from selected PDF
- Generate answers using Gemini API
- Show source document name
- Store document metadata in Supabase PostgreSQL
- Store chat history in Supabase
- View uploaded documents on dashboard
- View previous chat history

## Tech Stack

### Frontend

- React
- Vite
- Tailwind CSS
- Clerk Authentication
- Axios
- React Router
- Lucide React
- React Hot Toast

### Backend

- FastAPI
- Python
- PyPDF
- ChromaDB
- Sentence Transformers
- Gemini API
- Supabase PostgreSQL

## Project Structure

```txt
ai-knowledge-workspace/
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── .env.example
│   └── package.json
│
├── backend/
│   ├── routes/
│   │   ├── document_routes.py
│   │   └── chat_routes.py
│   ├── services/
│   │   ├── pdf_service.py
│   │   ├── rag_service.py
│   │   ├── gemini_service.py
│   │   └── db_service.py
│   ├── uploads/
│   ├── chroma_db/
│   ├── .env.example
│   ├── main.py
│   └── requirements.txt
│
├── .gitignore
└── README.md
```

## Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file inside the `backend` folder:

```env
GEMINI_API_KEY=your_gemini_api_key_here
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_KEY=your_supabase_anon_key_here
```

Run backend:

```bash
uvicorn main:app --reload
```

Backend will run on:

```txt
http://127.0.0.1:8000
```

Swagger API docs:

```txt
http://127.0.0.1:8000/docs
```

## Frontend Setup

```bash
cd frontend
npm install
```

Create a `.env` file inside the `frontend` folder:

```env
VITE_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key_here
```

Run frontend:

```bash
npm run dev
```

Frontend will run on:

```txt
http://localhost:5173
```

## Supabase Tables

### documents

```sql
create table documents (
  id uuid primary key default gen_random_uuid(),
  filename text not null,
  file_path text not null,
  characters_extracted int default 0,
  chunks_stored int default 0,
  created_at timestamp with time zone default now()
);

alter table documents enable row level security;

grant usage on schema public to anon;
grant select, insert on public.documents to anon;

create policy "Allow document insert"
on documents
for insert
to anon
with check (true);

create policy "Allow document select"
on documents
for select
to anon
using (true);
```

### chat_history

```sql
create table chat_history (
  id uuid primary key default gen_random_uuid(),
  filename text not null,
  question text not null,
  answer text not null,
  sources text[],
  created_at timestamp with time zone default now()
);

alter table chat_history enable row level security;

grant usage on schema public to anon;
grant select, insert on public.chat_history to anon;

create policy "Allow chat insert"
on chat_history
for insert
to anon
with check (true);

create policy "Allow chat select"
on chat_history
for select
to anon
using (true);
```

## RAG Flow

```txt
PDF Upload
↓
Text Extraction
↓
Text Chunking
↓
Embedding Generation
↓
ChromaDB Storage
↓
Question Asked
↓
Relevant Chunks Retrieved
↓
Gemini Answer Generated
↓
Answer + Source Displayed
```

## Main API Endpoints

### Document Upload

```txt
POST /documents/upload
```

Uploads a PDF, extracts text, stores chunks in ChromaDB, and saves metadata in Supabase.

### Get Documents

```txt
GET /documents/
```

Returns uploaded document metadata from Supabase.

### Ask Question

```txt
POST /chat/ask
```

Asks a question from the selected PDF using RAG and Gemini.

Example request:

```json
{
  "question": "What is this document about?",
  "filename": "example.pdf"
}
```

### Chat History

```txt
GET /chat/history?filename=example.pdf
```

Returns previous questions and answers for the selected PDF.

## Environment Variables

### Backend

```env
GEMINI_API_KEY=your_gemini_api_key_here
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_KEY=your_supabase_anon_key_here
```

### Frontend

```env
VITE_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key_here
```

## Important Notes

- Do not push real `.env` files to GitHub.
- `backend/uploads/` is used only for local PDF storage.
- `backend/chroma_db/` stores local ChromaDB vector data.
- For production, Supabase Storage can be added for PDF file storage.
- Current RLS policies are suitable for MVP/local development. For production, add `user_id` and user-specific access policies.

## Resume Description

Built a full-stack GenAI-powered RAG platform using React, Vite, FastAPI, Clerk, Gemini API, ChromaDB, Sentence Transformers, and Supabase PostgreSQL. The platform allows users to upload PDFs, extract content, perform semantic search, chat with selected documents, and store document metadata and chat history.
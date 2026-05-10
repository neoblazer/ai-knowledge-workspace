import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is missing in .env file")

if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY is missing in .env file")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def save_document_metadata(
    filename: str,
    file_path: str,
    characters_extracted: int,
    chunks_stored: int,
):
    data = {
        "filename": filename,
        "file_path": file_path,
        "characters_extracted": characters_extracted,
        "chunks_stored": chunks_stored,
    }

    response = supabase.table("documents").insert(data).execute()
    return response.data


def get_all_documents():
    response = (
        supabase.table("documents")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data

def save_chat_history(
    filename: str,
    question: str,
    answer: str,
    sources: list,
):
    data = {
        "filename": filename,
        "question": question,
        "answer": answer,
        "sources": sources,
    }

    response = supabase.table("chat_history").insert(data).execute()
    return response.data


def get_chat_history(filename: str | None = None):
    query = supabase.table("chat_history").select("*").order("created_at", desc=True)

    if filename:
        query = query.eq("filename", filename)

    response = query.execute()
    return response.data
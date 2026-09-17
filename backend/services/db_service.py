from functools import lru_cache
from uuid import UUID

from supabase import Client, create_client

from config import get_settings


@lru_cache
def get_supabase_client() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError("Supabase backend configuration is missing")
    return create_client(settings.supabase_url, settings.supabase_key)


def save_document_metadata(
    document_id: UUID,
    user_id: str,
    filename: str,
    file_path: str,
    characters_extracted: int,
    chunks_stored: int,
):
    data = {
        "document_id": str(document_id),
        "user_id": user_id,
        "filename": filename,
        "file_path": file_path,
        "characters_extracted": characters_extracted,
        "chunks_stored": chunks_stored,
    }
    response = get_supabase_client().table("documents").insert(data).execute()
    return response.data


def get_all_documents(user_id: str):
    response = (
        get_supabase_client()
        .table("documents")
        .select("document_id,filename,characters_extracted,chunks_stored,created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def get_document(document_id: UUID | str, user_id: str):
    response = (
        get_supabase_client()
        .table("documents")
        .select("*")
        .eq("document_id", str(document_id))
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def delete_document_metadata(document_id: UUID | str, user_id: str):
    response = (
        get_supabase_client()
        .table("documents")
        .delete()
        .eq("document_id", str(document_id))
        .eq("user_id", user_id)
        .execute()
    )
    return response.data


def save_chat_history(
    user_id: str,
    document_id: UUID | str,
    filename: str,
    question: str,
    answer: str,
    citations: list[dict],
):
    data = {
        "user_id": user_id,
        "document_id": str(document_id),
        "filename": filename,
        "question": question,
        "answer": answer,
        "citations": citations,
    }
    response = get_supabase_client().table("chat_history").insert(data).execute()
    return response.data


def get_chat_history(user_id: str, document_id: UUID | str | None = None):
    query = (
        get_supabase_client()
        .table("chat_history")
        .select("id,document_id,filename,question,answer,citations,created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
    )
    if document_id:
        query = query.eq("document_id", str(document_id))
    response = query.execute()
    return response.data or []


def delete_chat_history_for_document(document_id: UUID | str, user_id: str):
    response = (
        get_supabase_client()
        .table("chat_history")
        .delete()
        .eq("document_id", str(document_id))
        .eq("user_id", user_id)
        .execute()
    )
    return response.data

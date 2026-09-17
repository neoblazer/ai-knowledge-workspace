from functools import lru_cache
from uuid import UUID

import chromadb
from sentence_transformers import SentenceTransformer

from config import get_settings
from services.pdf_service import DocumentChunk


@lru_cache
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(get_settings().embedding_model)


@lru_cache
def get_collection():
    settings = get_settings()
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(settings.chroma_path))
    return client.get_or_create_collection(name="documents")


def store_document_in_chroma(
    document_id: UUID | str,
    user_id: str,
    filename: str,
    chunks: list[DocumentChunk],
):
    if not chunks:
        return {"chunks_stored": 0, "message": "No text chunks found"}

    document_id_text = str(document_id)
    texts = [chunk.text for chunk in chunks]
    embeddings = get_embedding_model().encode(texts, normalize_embeddings=True).tolist()
    ids = [f"{document_id_text}_chunk_{chunk.chunk_index}" for chunk in chunks]
    metadatas = [
        {
            "document_id": document_id_text,
            "user_id": user_id,
            "filename": filename,
            "page": chunk.page_number,
            "chunk_index": chunk.chunk_index,
        }
        for chunk in chunks
    ]
    get_collection().add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return {
        "chunks_stored": len(chunks),
        "message": "Document stored in ChromaDB successfully",
    }


def search_relevant_chunks(
    question: str,
    document_id: UUID | str,
    user_id: str,
    top_k: int | None = None,
):
    settings = get_settings()
    result_count = top_k or settings.rag_top_k
    question_embedding = get_embedding_model().encode(
        [question], normalize_embeddings=True
    ).tolist()[0]
    where = {
        "$and": [
            {"document_id": str(document_id)},
            {"user_id": user_id},
        ]
    }
    results = get_collection().query(
        query_embeddings=[question_embedding],
        n_results=max(result_count * 2, result_count),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    chunks: list[str] = []
    citations: list[dict] = []
    seen: set[tuple[str, int | None]] = set()

    for document, metadata, distance in zip(documents, metadatas, distances):
        if settings.rag_max_distance is not None and distance > settings.rag_max_distance:
            continue
        key = (document.strip(), metadata.get("page"))
        if not key[0] or key in seen:
            continue
        seen.add(key)
        chunks.append(document)
        citations.append(
            {
                "document_id": metadata["document_id"],
                "filename": metadata["filename"],
                "page": metadata.get("page"),
                "chunk_index": metadata["chunk_index"],
                "distance": float(distance) if distance is not None else None,
            }
        )
        if len(chunks) >= result_count:
            break
    return {"chunks": chunks, "citations": citations}


def delete_document_from_chroma(document_id: UUID | str, user_id: str) -> None:
    get_collection().delete(
        where={
            "$and": [
                {"document_id": str(document_id)},
                {"user_id": user_id},
            ]
        }
    )

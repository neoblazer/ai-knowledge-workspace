import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "documents"

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)


def split_text_into_chunks(text: str, chunk_size: int = 800, overlap: int = 150):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk.strip())

        start += chunk_size - overlap

    return chunks


def store_document_in_chroma(filename: str, text: str):
    chunks = split_text_into_chunks(text)

    if not chunks:
        return {
            "chunks_stored": 0,
            "message": "No text chunks found",
        }

    embeddings = embedding_model.encode(chunks).tolist()

    ids = [f"{filename}_chunk_{i}" for i in range(len(chunks))]

    metadatas = [
        {
            "filename": filename,
            "chunk_index": i,
        }
        for i in range(len(chunks))
    ]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return {
        "chunks_stored": len(chunks),
        "message": "Document stored in ChromaDB successfully",
    }


def search_relevant_chunks(question: str, filename: str | None = None, top_k: int = 3):
    question_embedding = embedding_model.encode([question]).tolist()[0]

    query_args = {
        "query_embeddings": [question_embedding],
        "n_results": top_k,
    }

    if filename:
        query_args["where"] = {"filename": filename}

    results = collection.query(**query_args)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    sources = []

    for metadata in metadatas:
        sources.append(metadata.get("filename", "Unknown"))

    return {
        "chunks": documents,
        "sources": list(set(sources)),
    }
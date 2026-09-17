from types import SimpleNamespace

from services.pdf_service import DocumentChunk, PageText, create_chunks_from_pages
import services.rag_service as rag


class Encoded:
    def __init__(self, value):
        self.value = value

    def tolist(self):
        return self.value


class FakeModel:
    def encode(self, texts, normalize_embeddings=False):
        assert normalize_embeddings is True
        return Encoded([[0.1, 0.2] for _ in texts])


class FakeCollection:
    def __init__(self):
        self.added = None
        self.queried = None
        self.deleted = None

    def add(self, **kwargs):
        self.added = kwargs

    def query(self, **kwargs):
        self.queried = kwargs
        return {
            "documents": [["first context", "first context", "second context"]],
            "metadatas": [[
                {"document_id": "doc-1", "user_id": "user-1", "filename": "notes.pdf", "page": 1, "chunk_index": 0},
                {"document_id": "doc-1", "user_id": "user-1", "filename": "notes.pdf", "page": 1, "chunk_index": 1},
                {"document_id": "doc-1", "user_id": "user-1", "filename": "notes.pdf", "page": 2, "chunk_index": 2},
            ]],
            "distances": [[0.1, 0.2, 0.3]],
        }

    def delete(self, **kwargs):
        self.deleted = kwargs


def test_chunk_creation_preserves_page_and_global_chunk_index():
    chunks = create_chunks_from_pages(
        [PageText(page_number=2, text="abcdefghij"), PageText(page_number=4, text="klmnop")],
        chunk_size=6,
        overlap=2,
    )
    assert [chunk.page_number for chunk in chunks] == [2, 2, 2, 4, 4]
    assert [chunk.chunk_index for chunk in chunks] == list(range(5))


def test_store_uses_document_uuid_and_user_metadata(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(rag, "get_embedding_model", lambda: FakeModel())
    monkeypatch.setattr(rag, "get_collection", lambda: collection)
    chunks = [
        DocumentChunk(text="one", page_number=1, chunk_index=0),
        DocumentChunk(text="two", page_number=2, chunk_index=1),
    ]
    result = rag.store_document_in_chroma("doc-1", "user-1", "notes.pdf", chunks)
    assert result["chunks_stored"] == 2
    assert collection.added["ids"] == ["doc-1_chunk_0", "doc-1_chunk_1"]
    assert collection.added["metadatas"][1] == {
        "document_id": "doc-1", "user_id": "user-1", "filename": "notes.pdf", "page": 2, "chunk_index": 1,
    }


def test_retrieval_is_scoped_and_suppresses_duplicates(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(rag, "get_embedding_model", lambda: FakeModel())
    monkeypatch.setattr(rag, "get_collection", lambda: collection)
    monkeypatch.setattr(rag, "get_settings", lambda: SimpleNamespace(rag_top_k=3, rag_max_distance=None))
    result = rag.search_relevant_chunks("question", "doc-1", "user-1")
    assert result["chunks"] == ["first context", "second context"]
    assert collection.queried["where"] == {"$and": [{"document_id": "doc-1"}, {"user_id": "user-1"}]}
    assert result["citations"][1]["page"] == 2
    assert result["citations"][1]["distance"] == 0.3


def test_delete_is_scoped_to_document_and_user(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(rag, "get_collection", lambda: collection)
    rag.delete_document_from_chroma("doc-1", "user-1")
    assert collection.deleted["where"] == {"$and": [{"document_id": "doc-1"}, {"user_id": "user-1"}]}

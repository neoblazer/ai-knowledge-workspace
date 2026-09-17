from dataclasses import replace
from pathlib import Path

from config import get_settings
from services.pdf_service import PageText


def _test_settings(tmp_path: Path):
    return replace(
        get_settings(),
        upload_dir=tmp_path,
        max_upload_size_bytes=1024 * 1024,
        chunk_size=20,
        chunk_overlap=5,
    )


def test_valid_pdf_upload_is_owned_and_uses_uuid(authenticated_client, monkeypatch, tmp_path):
    import routes.document_routes as routes

    monkeypatch.setattr(routes, "get_settings", lambda: _test_settings(tmp_path))
    monkeypatch.setattr(
        routes,
        "extract_pages_from_pdf",
        lambda _path: [PageText(page_number=1, text="A useful page of PDF text")],
    )
    captured = {}

    def fake_store(**kwargs):
        captured["store"] = kwargs
        return {"chunks_stored": len(kwargs["chunks"])}

    def fake_save(**kwargs):
        captured["save"] = kwargs
        return [kwargs]

    monkeypatch.setattr(routes, "store_document_in_chroma", fake_store)
    monkeypatch.setattr(routes, "save_document_metadata", fake_save)
    response = authenticated_client.post(
        "/documents/upload",
        files={"file": ("notes.pdf", b"%PDF-mocked", "application/pdf")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "notes.pdf"
    assert body["document_id"] == str(captured["store"]["document_id"])
    assert captured["store"]["user_id"] == "user_test"
    assert captured["save"]["user_id"] == "user_test"
    assert Path(captured["save"]["file_path"]).name == f"{body['document_id']}.pdf"
    assert "file_path" not in body


def test_invalid_file_type_is_rejected(authenticated_client):
    response = authenticated_client.post(
        "/documents/upload",
        files={"file": ("notes.txt", b"not pdf", "text/plain")},
    )
    assert response.status_code == 400


def test_pdf_without_extractable_text_is_rejected(
    authenticated_client, monkeypatch, tmp_path
):
    import routes.document_routes as routes

    monkeypatch.setattr(routes, "get_settings", lambda: _test_settings(tmp_path))
    monkeypatch.setattr(routes, "extract_pages_from_pdf", lambda _path: [])
    response = authenticated_client.post(
        "/documents/upload",
        files={"file": ("scan.pdf", b"%PDF-mocked", "application/pdf")},
    )
    assert response.status_code == 422
    assert not list(tmp_path.glob("*.pdf"))


def test_document_listing_is_scoped_to_current_user(authenticated_client, monkeypatch):
    import routes.document_routes as routes

    observed = {}

    def fake_list(user_id):
        observed["user_id"] = user_id
        return [{"document_id": "4e11f51d-fbcd-4a03-b46b-27d5f1350c2f"}]

    monkeypatch.setattr(routes, "get_all_documents", fake_list)
    response = authenticated_client.get("/documents/")
    assert response.status_code == 200
    assert observed["user_id"] == "user_test"


def test_document_owner_can_delete(authenticated_client, monkeypatch, tmp_path):
    import routes.document_routes as routes

    document_id = "4e11f51d-fbcd-4a03-b46b-27d5f1350c2f"
    stored_file = tmp_path / f"{document_id}.pdf"
    stored_file.write_bytes(b"%PDF-mocked")
    monkeypatch.setattr(routes, "get_settings", lambda: _test_settings(tmp_path))
    monkeypatch.setattr(
        routes,
        "get_document",
        lambda requested_id, user_id: {
            "document_id": str(requested_id),
            "user_id": user_id,
            "file_path": str(stored_file),
        },
    )
    calls = []
    monkeypatch.setattr(
        routes,
        "delete_document_from_chroma",
        lambda requested_id, user_id: calls.append(("chroma", str(requested_id), user_id)),
    )
    monkeypatch.setattr(
        routes,
        "delete_chat_history_for_document",
        lambda requested_id, user_id: calls.append(("chat", str(requested_id), user_id)),
    )
    monkeypatch.setattr(
        routes,
        "delete_document_metadata",
        lambda requested_id, user_id: calls.append(("document", str(requested_id), user_id)),
    )
    response = authenticated_client.delete(f"/documents/{document_id}")
    assert response.status_code == 200
    assert not stored_file.exists()
    assert [call[0] for call in calls] == ["chroma", "chat", "document"]
    assert all(call[2] == "user_test" for call in calls)


def test_another_users_document_cannot_be_deleted(authenticated_client, monkeypatch):
    import routes.document_routes as routes

    monkeypatch.setattr(routes, "get_document", lambda _document_id, _user_id: None)
    response = authenticated_client.delete(
        "/documents/4e11f51d-fbcd-4a03-b46b-27d5f1350c2f"
    )
    assert response.status_code == 404

def test_malformed_pdf_returns_422(authenticated_client, monkeypatch, tmp_path):
    import routes.document_routes as routes
    from pypdf.errors import PdfReadError

    monkeypatch.setattr(routes, "get_settings", lambda: _test_settings(tmp_path))
    monkeypatch.setattr(
        routes,
        "extract_pages_from_pdf",
        lambda _path: (_ for _ in ()).throw(PdfReadError("malformed")),
    )
    response = authenticated_client.post(
        "/documents/upload",
        files={"file": ("broken.pdf", b"%PDF-mocked", "application/pdf")},
    )
    assert response.status_code == 422
    assert not list(tmp_path.glob("*.pdf"))

from types import SimpleNamespace

import auth
from fastapi.testclient import TestClient

from main import app


def test_missing_token_returns_401():
    with TestClient(app) as client:
        response = client.get("/documents/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_invalid_token_returns_401(monkeypatch):
    monkeypatch.setattr(
        auth,
        "get_settings",
        lambda: SimpleNamespace(
            clerk_secret_key="test_secret",
            clerk_jwt_key="test_public_key",
            clerk_authorized_parties=("http://localhost:5173",),
        ),
    )
    monkeypatch.setattr(
        auth,
        "authenticate_request",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("bad token")),
    )
    with TestClient(app) as client:
        response = client.get(
            "/documents/", headers={"Authorization": "Bearer invalid"}
        )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired authentication token"


def test_valid_token_allows_authenticated_request(monkeypatch):
    import routes.document_routes as document_routes

    monkeypatch.setattr(
        auth,
        "get_settings",
        lambda: SimpleNamespace(
            clerk_secret_key="test_secret",
            clerk_jwt_key="test_public_key",
            clerk_authorized_parties=("http://localhost:5173",),
        ),
    )
    monkeypatch.setattr(
        auth,
        "authenticate_request",
        lambda *_args, **_kwargs: SimpleNamespace(
            is_signed_in=True,
            payload={"sub": "user_verified", "sid": "session_verified"},
        ),
    )
    observed = {}

    def fake_get_all_documents(user_id):
        observed["user_id"] = user_id
        return []

    monkeypatch.setattr(document_routes, "get_all_documents", fake_get_all_documents)
    with TestClient(app) as client:
        response = client.get(
            "/documents/", headers={"Authorization": "Bearer valid"}
        )
    assert response.status_code == 200
    assert observed["user_id"] == "user_verified"

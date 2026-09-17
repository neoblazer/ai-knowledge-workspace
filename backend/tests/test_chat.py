from services.gemini_service import AnswerGenerationError


DOCUMENT_ID = "4e11f51d-fbcd-4a03-b46b-27d5f1350c2f"


def _owned_document(document_id, user_id):
    return {"document_id": str(document_id), "user_id": user_id, "filename": "notes.pdf"}


def test_authenticated_question_is_scoped_and_saved(authenticated_client, monkeypatch):
    import routes.chat_routes as routes

    monkeypatch.setattr(routes, "get_document", _owned_document)
    observed = {}

    def fake_search(**kwargs):
        observed["search"] = kwargs
        return {
            "chunks": ["retrieved context"],
            "citations": [{"document_id": DOCUMENT_ID, "filename": "notes.pdf", "page": 5, "chunk_index": 3, "distance": 0.2}],
        }

    monkeypatch.setattr(routes, "search_relevant_chunks", fake_search)
    monkeypatch.setattr(routes, "generate_answer_from_context", lambda question, context: "Grounded answer")
    monkeypatch.setattr(routes, "save_chat_history", lambda **kwargs: observed.setdefault("saved", kwargs))
    response = authenticated_client.post(
        "/chat/ask", json={"question": "What is it?", "document_id": DOCUMENT_ID}
    )
    assert response.status_code == 200
    assert response.json()["answer"] == "Grounded answer"
    assert response.json()["citations"][0]["page"] == 5
    assert observed["search"]["user_id"] == "user_test"
    assert observed["saved"]["user_id"] == "user_test"
    assert str(observed["saved"]["document_id"]) == DOCUMENT_ID


def test_no_context_returns_grounded_fallback(authenticated_client, monkeypatch):
    import routes.chat_routes as routes

    monkeypatch.setattr(routes, "get_document", _owned_document)
    monkeypatch.setattr(routes, "search_relevant_chunks", lambda **_kwargs: {"chunks": [], "citations": []})
    monkeypatch.setattr(routes, "save_chat_history", lambda **_kwargs: None)
    response = authenticated_client.post(
        "/chat/ask", json={"question": "Unknown?", "document_id": DOCUMENT_ID}
    )
    assert response.status_code == 200
    assert "could not find" in response.json()["answer"].lower()


def test_gemini_failure_returns_safe_503(authenticated_client, monkeypatch):
    import routes.chat_routes as routes

    monkeypatch.setattr(routes, "get_document", _owned_document)
    monkeypatch.setattr(
        routes,
        "search_relevant_chunks",
        lambda **_kwargs: {
            "chunks": ["context"],
            "citations": [{"document_id": DOCUMENT_ID, "filename": "notes.pdf", "page": 1, "chunk_index": 0, "distance": 0.1}],
        },
    )
    monkeypatch.setattr(
        routes,
        "generate_answer_from_context",
        lambda *_args: (_ for _ in ()).throw(AnswerGenerationError()),
    )
    response = authenticated_client.post(
        "/chat/ask", json={"question": "Question", "document_id": DOCUMENT_ID}
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "Unable to generate an answer right now. Please try again."


def test_chat_history_is_scoped_to_user_and_document(authenticated_client, monkeypatch):
    import routes.chat_routes as routes

    monkeypatch.setattr(routes, "get_document", _owned_document)
    observed = {}

    def fake_history(user_id, document_id):
        observed["user_id"] = user_id
        observed["document_id"] = str(document_id)
        return []

    monkeypatch.setattr(routes, "get_chat_history", fake_history)
    response = authenticated_client.get(f"/chat/history?document_id={DOCUMENT_ID}")
    assert response.status_code == 200
    assert observed == {"user_id": "user_test", "document_id": DOCUMENT_ID}


def test_question_for_another_users_document_is_hidden(authenticated_client, monkeypatch):
    import routes.chat_routes as routes

    monkeypatch.setattr(routes, "get_document", lambda _document_id, _user_id: None)
    response = authenticated_client.post(
        "/chat/ask", json={"question": "Question", "document_id": DOCUMENT_ID}
    )
    assert response.status_code == 404

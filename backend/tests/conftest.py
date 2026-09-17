import pytest
from fastapi.testclient import TestClient

from auth import CurrentUser, get_current_user
from main import app


@pytest.fixture
def authenticated_client():
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id="user_test", session_id="session_test"
    )
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

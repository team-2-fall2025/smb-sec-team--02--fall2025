from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from backend import app


client = TestClient(app.app)


def test_root_endpoint():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "FastAPI is running"}


def test_version_endpoint():
    resp = client.get("/version")
    assert resp.status_code == 200
    data = resp.json()
    assert "version" in data


def test_seed_endpoint_get_and_post_mocked():
    # Patch the seed_main coroutine so the endpoint does not run heavy I/O
    patched = AsyncMock(return_value=None)
    with patch("backend.routers.seed.seed_main", patched):
        get_resp = client.get("/api/db/seed")
        assert get_resp.status_code == 200
        assert get_resp.json().get("status") == "ok"

        post_resp = client.post("/api/db/seed")
        assert post_resp.status_code == 200
        assert post_resp.json().get("status") == "ok"

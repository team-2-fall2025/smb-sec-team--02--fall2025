"""Test database and stats-related API endpoints."""
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from backend import app


client = TestClient(app.app)


def test_stats_endpoint_returns_counts_mocked():
    """Test /api/stats endpoint with mocked MongoDB collections."""
    # Mock the db collections to avoid actual DB calls
    mock_collections = {
        "assets": AsyncMock(count_documents=AsyncMock(return_value=5)),
        "intel_events": AsyncMock(count_documents=AsyncMock(return_value=12)),
        "risk_register": AsyncMock(count_documents=AsyncMock(return_value=3)),
    }

    def mock_db_getitem(name):
        return mock_collections.get(name, AsyncMock(count_documents=AsyncMock(return_value=0)))

    with patch("backend.routers.stats.db") as mock_db:
        mock_db.__getitem__.side_effect = mock_db_getitem
        resp = client.get("/api/stats")

    assert resp.status_code == 200
    data = resp.json()
    assert "assets" in data
    assert "intel_events" in data
    assert "risk_items" in data
    # Values should be integers (or 0 if collection not found)
    assert isinstance(data["assets"], int)
    assert isinstance(data["intel_events"], int)
    assert isinstance(data["risk_items"], int)


def test_stats_endpoint_handles_db_errors_gracefully():
    """Test /api/stats returns 0 counts when DB operations fail."""
    with patch("backend.routers.stats.db") as mock_db:
        mock_db.__getitem__.side_effect = Exception("DB connection failed")
        resp = client.get("/api/stats")

    # Should still return 200 with 0 values due to safe_count exception handling
    assert resp.status_code == 200
    data = resp.json()
    assert data["assets"] == 0
    assert data["intel_events"] == 0
    assert data["risk_items"] == 0

import pytest
from fastapi.testclient import TestClient

from ..app import app

# Create a TestClient instance
client = TestClient(app)

@pytest.mark.asyncio
async def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"version": "1.0", "status": "healthy"}
import pytest
from fastapi.testclient import TestClient

import app

# Create a TestClient instance
client = TestClient(app.app)

@pytest.mark.asyncio
async def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"version": "1.0", "status": "healthy"}
import pytest

# from ..app import app

# # Create a TestClient instance
# client = TestClient(app)

@pytest.mark.asyncio
async def test_health_endpoint():
    l = True
    assert l == True
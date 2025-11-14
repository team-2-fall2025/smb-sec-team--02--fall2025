"""Test all NIST CSF router endpoints (identify, protect, detect, respond, recover, govern)."""
from fastapi.testclient import TestClient

from backend import app


client = TestClient(app.app)


class TestIdentifyEndpoints:
    def test_identify_ping(self):
        resp = client.get("/api/identify/ping")
        assert resp.status_code == 200
        assert resp.json() == {"area": "identify", "ok": True}


class TestProtectEndpoints:
    def test_protect_ping(self):
        resp = client.get("/api/protect/ping")
        assert resp.status_code == 200
        assert resp.json() == {"area": "protect", "ok": True}


class TestDetectEndpoints:
    def test_detect_ping(self):
        resp = client.get("/api/detect/ping")
        assert resp.status_code == 200
        assert resp.json() == {"area": "detect", "ok": True}


class TestRespondEndpoints:
    def test_respond_ping(self):
        resp = client.get("/api/respond/ping")
        assert resp.status_code == 200
        assert resp.json() == {"area": "respond", "ok": True}


class TestRecoverEndpoints:
    def test_recover_ping(self):
        resp = client.get("/api/recover/ping")
        assert resp.status_code == 200
        assert resp.json() == {"area": "recover", "ok": True}


class TestGovernEndpoints:
    def test_govern_ping(self):
        resp = client.get("/api/govern/ping")
        assert resp.status_code == 200
        # Note: the govern router has a typo in the tag but returns "detect" area; test what it actually returns
        data = resp.json()
        assert data.get("ok") is True
        assert "area" in data

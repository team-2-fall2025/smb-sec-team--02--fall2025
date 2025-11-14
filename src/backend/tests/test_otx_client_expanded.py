"""Expanded OTXClient unit tests with edge cases and error handling."""
import pytest
from unittest.mock import Mock, patch

from backend.services.osint.otx_client import OTXClient


class TestOTXClientNormalize:
    """Test OTXClient.normalize edge cases."""

    def test_normalize_returns_expected_structure(self):
        raw = {
            "pulse_info": {"count": 1},
            "base_indicator": {"indicator": "1.2.3.4"}
        }
        result = OTXClient.normalize(raw, "1.2.3.4")

        assert isinstance(result, dict)
        assert result["source"] == "otx"
        assert result["ioc_type"] == "ipv4"
        assert result["indicator"] == "1.2.3.4"
        assert isinstance(result["severity"], int)
        assert result["raw"] is raw

    def test_normalize_with_empty_raw(self):
        """Test normalize with empty raw data."""
        raw = {}
        result = OTXClient.normalize(raw, "8.8.8.8")

        assert result["source"] == "otx"
        assert result["indicator"] == "8.8.8.8"
        assert result["raw"] == {}

    def test_normalize_preserves_raw_data_reference(self):
        """Verify that normalize stores the exact raw dict reference."""
        raw = {"key": "value", "nested": {"data": True}}
        result = OTXClient.normalize(raw, "test.com")

        # Ensure it's the same reference, not a copy
        assert result["raw"] is raw
        raw["new_key"] = "added"
        assert result["raw"]["new_key"] == "added"


class TestOTXClientFetchIPGeneral:
    """Test OTXClient.fetch_ip_general retry and error handling."""

    def test_fetch_ip_general_handles_rate_limit_then_success(self):
        """Test that fetch_ip_general retries on 429 (rate limit)."""
        client = OTXClient(api_key="test")

        rate_limited = Mock()
        rate_limited.status_code = 429

        success = Mock()
        success.status_code = 200
        success.json.return_value = {"indicator": "1.2.3.4", "pulse_info": {}}

        with patch("requests.get", side_effect=[rate_limited, success]) as mock_get:
            with patch("time.sleep"):
                result = client.fetch_ip_general("1.2.3.4")

        assert result == {"indicator": "1.2.3.4", "pulse_info": {}}
        assert mock_get.call_count == 2

    def test_fetch_ip_general_raises_on_http_error(self):
        """Test that fetch_ip_general raises on non-429 HTTP errors."""
        client = OTXClient(api_key="test")

        error_response = Mock()
        error_response.status_code = 401
        error_response.raise_for_status.side_effect = Exception("401 Unauthorized")

        with patch("requests.get", return_value=error_response):
            with pytest.raises(Exception):
                client.fetch_ip_general("1.2.3.4")

    def test_fetch_ip_general_returns_empty_on_exhausted_retries(self):
        """Test that after 3 failed rate-limit attempts, return empty dict."""
        client = OTXClient(api_key="test")

        rate_limited = Mock()
        rate_limited.status_code = 429

        with patch("requests.get", return_value=rate_limited):
            with patch("time.sleep"):
                result = client.fetch_ip_general("1.2.3.4")

        assert result == {}

    def test_fetch_ip_general_uses_correct_endpoint_url(self):
        """Verify that fetch_ip_general constructs the correct URL."""
        client = OTXClient(api_key="test_key")

        success = Mock()
        success.status_code = 200
        success.json.return_value = {"test": "data"}

        with patch("requests.get", return_value=success) as mock_get:
            client.fetch_ip_general("192.168.1.1")

            # Verify the URL was constructed correctly
            call_args = mock_get.call_args
            assert "192.168.1.1" in call_args[0][0]
            assert "IPv4" in call_args[0][0]
            assert "general" in call_args[0][0]

    def test_fetch_ip_general_passes_headers(self):
        """Verify that fetch_ip_general passes API key in headers."""
        client = OTXClient(api_key="my_api_key")

        success = Mock()
        success.status_code = 200
        success.json.return_value = {}

        with patch("requests.get", return_value=success) as mock_get:
            client.fetch_ip_general("1.1.1.1")

            call_kwargs = mock_get.call_args[1]
            assert "headers" in call_kwargs
            assert call_kwargs["headers"]["X-OTX-API-KEY"] == "my_api_key"


class TestOTXClientInit:
    """Test OTXClient initialization."""

    def test_init_with_api_key(self):
        """Test client initialization with explicit API key."""
        client = OTXClient(api_key="explicit_key")
        assert client.key == "explicit_key"
        assert client.headers == {"X-OTX-API-KEY": "explicit_key"}

    def test_init_without_api_key_defaults_to_empty(self):
        """Test client initialization without API key defaults to empty."""
        with patch.dict("os.environ", {}, clear=True):
            client = OTXClient(api_key=None)
            assert client.key == ""
            assert client.headers == {}

    def test_init_with_env_api_key(self):
        """Test client reads API key from environment if not provided."""
        with patch.dict("os.environ", {"OSINT_OTX_API_KEY": "env_key"}):
            client = OTXClient(api_key=None)
            assert client.key == "env_key"
            assert client.headers == {"X-OTX-API-KEY": "env_key"}

    def test_init_explicit_key_overrides_env(self):
        """Test that explicit API key takes precedence over environment."""
        with patch.dict("os.environ", {"OSINT_OTX_API_KEY": "env_key"}):
            client = OTXClient(api_key="explicit_key")
            assert client.key == "explicit_key"

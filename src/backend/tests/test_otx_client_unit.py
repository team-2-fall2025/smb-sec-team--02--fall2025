import pytest
from unittest.mock import Mock, patch

from ..services.osint.otx_client import OTXClient


def test_normalize_returns_expected_structure():
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


def test_fetch_ip_general_handles_rate_limit_then_success():
    client = OTXClient(api_key="test")

    # Mock responses: first a 429, then a 200
    rate_limited = Mock()
    rate_limited.status_code = 429

    success = Mock()
    success.status_code = 200
    success.json.return_value = {"indicator": "1.2.3.4", "pulse_info": {}}

    with patch("requests.get", side_effect=[rate_limited, success]) as mock_get:
        with patch("time.sleep") as mock_sleep:
            result = client.fetch_ip_general("1.2.3.4")

    assert result == {"indicator": "1.2.3.4", "pulse_info": {}}
    assert mock_get.call_count == 2

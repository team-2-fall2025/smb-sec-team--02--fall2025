import pytest
from unittest.mock import Mock, patch

from ..services.osint.otx_client import OTXClient, OTXConfig, OTXAPIError


class TestOTXConfig:
    """Test OTX configuration"""
    
    # def test_config_creation(self):
    #     """Test creating OTX configuration"""
    #     config = OTXConfig(
    #         api_key="test_key",
    #         base_url="https://test.com",
    #         rate_limit_delay=2.0,
    #         max_retries=5,
    #         timeout=60
    #     )
    #     # print(config)
    #     assert config.api_key == "test_key"
    #     assert config.base_url == "https://test.com"
    #     assert config.rate_limit_delay == 2.0
    #     assert config.max_retries == 5
    #     assert config.timeout == 60
    
    # def test_config_defaults(self):
    #     """Test default configuration values"""
    #     config = OTXConfig(api_key="test_key")
        
    #     # print(config)
    #     assert config.api_key == "test_key"
    #     assert config.base_url == "https://otx.alienvault.com/api/v1"
    #     assert config.rate_limit_delay == 1.0
    #     assert config.max_retries == 3
    #     assert config.timeout == 30


class TestOTXClient:
    """Test OTX client functionality"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing"""
        return OTXConfig(
            api_key="test_key",
            base_url="https://test.com",
            rate_limit_delay=0.1,  # Fast for testing
            max_retries=2,
            timeout=10
        )
    
#     @pytest.fixture
#     def otx_client(self, mock_config):
#         """Create OTX client with mock configuration"""
#         return OTXClient(mock_config)
    
#     def test_client_initialization(self, mock_config):
#         """Test client initialization"""
#         client = OTXClient(mock_config)
        
#         assert client.config == mock_config
#         assert client.session.headers['X-OTX-API-KEY'] == "test_key"
#         assert client.session.headers['Content-Type'] == "application/json"
#         assert client.last_request_time == 0.0
    
#     @patch.dict(os.environ, {'OTX_API_KEY': 'env_key'})
#     def test_load_config_from_env(self):
#         """Test loading configuration from environment variables"""
#         client = OTXClient()
        
#         assert client.config.api_key == "env_key"
#         assert client.config.base_url == "https://otx.alienvault.com/api/v1"
    
#     @patch.dict(os.environ, {}, clear=True)
#     def test_load_config_from_env_mock_mode(self):
#         """Test loading configuration when no API key is provided"""
#         client = OTXClient()
        
#         assert client.config.api_key == "mock_key"
    
#     def test_rate_limiting(self, otx_client):
#         """Test rate limiting functionality"""
#         start_time = time.time()
#         otx_client._rate_limit()
#         end_time = time.time()
        
#         # Should not sleep on first call
#         assert end_time - start_time < 0.1
        
#         # Second call should respect rate limit
#         start_time = time.time()
#         otx_client._rate_limit()
#         end_time = time.time()
        
#         # Should sleep for rate_limit_delay (0.1 seconds)
#         assert end_time - start_time >= 0.1
    
#     @patch('requests.Session.get')
#     def test_make_request_success(self, mock_get, otx_client):
#         """Test successful API request"""
#         mock_response = Mock()
#         mock_response.status_code = 200
#         mock_response.json.return_value = {"test": "data"}
#         mock_get.return_value = mock_response
        
#         result = otx_client._make_request("test/endpoint")
        
#         assert result == {"test": "data"}
#         mock_get.assert_called_once()
    
#     @patch('requests.Session.get')
#     def test_make_request_rate_limit(self, mock_get, otx_client):
#         """Test handling of rate limit response"""
#         # First response: rate limited
#         rate_limit_response = Mock()
#         rate_limit_response.status_code = 429
#         rate_limit_response.headers = {'Retry-After': '1'}
        
#         # Second response: success
#         success_response = Mock()
#         success_response.status_code = 200
#         success_response.json.return_value = {"test": "data"}
        
#         mock_get.side_effect = [rate_limit_response, success_response]
        
#         with patch('time.sleep'):  # Mock sleep to speed up test
#             result = otx_client._make_request("test/endpoint")
        
#         assert result == {"test": "data"}
#         assert mock_get.call_count == 2
    
#     @patch('requests.Session.get')
#     def test_make_request_api_error(self, mock_get, otx_client):
#         """Test handling of API errors"""
#         mock_response = Mock()
#         mock_response.status_code = 400
#         mock_response.text = "Bad Request"
#         mock_get.return_value = mock_response
        
#         with pytest.raises(OTXAPIError, match="API error 400"):
#             otx_client._make_request("test/endpoint")
    
#     @patch('requests.Session.get')
#     def test_make_request_retry_on_exception(self, mock_get, otx_client):
#         """Test retry logic on request exceptions"""
#         # First call raises exception, second succeeds
#         mock_get.side_effect = [
#             Exception("Network error"),
#             Mock(status_code=200, json=Mock(return_value={"test": "data"}))
#         ]
        
#         with patch('time.sleep'):  # Mock sleep to speed up test
#             result = otx_client._make_request("test/endpoint")
        
#         assert result == {"test": "data"}
#         assert mock_get.call_count == 2
    
#     def test_normalize_to_intel_event(self, otx_client):
#         """Test data normalization to IntelEvent"""
#         raw_data = {
#             "pulse_info": {
#                 "pulses": [
#                     {
#                         "id": "pulse1",
#                         "name": "Test Pulse",
#                         "tags": ["malware", "botnet"],
#                         "created": "2024-01-01T00:00:00Z"
#                     },
#                     {
#                         "id": "pulse2", 
#                         "name": "Another Pulse",
#                         "tags": ["phishing"],
#                         "created": "2024-01-01T00:00:00Z"
#                     }
#                 ]
#             },
#             "base_indicator": {
#                 "indicator": "1.2.3.4",
#                 "type": "IPv4"
#             }
#         }
        
#         intel_event = otx_client._normalize_to_intel_event(
#             raw_data, "1.2.3.4", "ipv4", {}
#         )
        
#         assert isinstance(intel_event, IntelEvent)
#         assert intel_event.source == "otx"
#         assert intel_event.event_type == "threat_intel"
#         assert intel_event.indicator == "1.2.3.4"
#         assert intel_event.indicator_type == "ipv4"
#         assert intel_event.confidence > 0.3  # Should be higher due to 2 pulses
#         assert intel_event.severity == "medium"  # 2 pulses = medium
#         assert "malware" in intel_event.tags
#         assert "botnet" in intel_event.tags
#         assert "phishing" in intel_event.tags
#         assert intel_event.raw_data == raw_data
    
#     def test_get_ip_reputation_mock_mode(self, otx_client):
#         """Test IP reputation in mock mode"""
#         otx_client.config.api_key = "mock_key"
        
#         intel_event = otx_client.get_ip_reputation("1.2.3.4")
        
#         assert isinstance(intel_event, IntelEvent)
#         assert intel_event.indicator == "1.2.3.4"
#         assert intel_event.indicator_type == "ipv4"
#         assert intel_event.source == "otx"
#         assert "malware" in intel_event.tags
    
#     def test_get_domain_reputation_mock_mode(self, otx_client):
#         """Test domain reputation in mock mode"""
#         otx_client.config.api_key = "mock_key"
        
#         intel_event = otx_client.get_domain_reputation("example.com")
        
#         assert isinstance(intel_event, IntelEvent)
#         assert intel_event.indicator == "example.com"
#         assert intel_event.indicator_type == "domain"
#         assert intel_event.source == "otx"
#         assert "phishing" in intel_event.tags
    
#     def test_get_file_hash_reputation_mock_mode(self, otx_client):
#         """Test file hash reputation in mock mode"""
#         otx_client.config.api_key = "mock_key"
        
#         # Test MD5 hash
#         md5_hash = "d41d8cd98f00b204e9800998ecf8427e"
#         intel_event = otx_client.get_file_hash_reputation(md5_hash)
        
#         assert isinstance(intel_event, IntelEvent)
#         assert intel_event.indicator == md5_hash
#         assert intel_event.indicator_type == "md5"
#         assert intel_event.source == "otx"
#         assert "malware" in intel_event.tags
        
#         # Test SHA256 hash
#         sha256_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
#         intel_event = otx_client.get_file_hash_reputation(sha256_hash)
        
#         assert intel_event.indicator_type == "sha256"
    
#     @patch('requests.Session.get')
#     def test_get_ip_reputation_real_api(self, mock_get, otx_client):
#         """Test IP reputation with real API call"""
#         mock_response = Mock()
#         mock_response.status_code = 200
#         mock_response.json.return_value = {
#             "pulse_info": {
#                 "pulses": [
#                     {
#                         "id": "real_pulse",
#                         "name": "Real Threat",
#                         "tags": ["malware"],
#                         "created": "2024-01-01T00:00:00Z"
#                     }
#                 ]
#             },
#             "base_indicator": {
#                 "indicator": "1.2.3.4",
#                 "type": "IPv4"
#             }
#         }
#         mock_get.return_value = mock_response
        
#         intel_event = otx_client.get_ip_reputation("1.2.3.4")
        
#         assert isinstance(intel_event, IntelEvent)
#         assert intel_event.indicator == "1.2.3.4"
#         assert intel_event.indicator_type == "ipv4"
#         assert "malware" in intel_event.tags
    
#     def test_health_check_mock_mode(self, otx_client):
#         """Test health check in mock mode"""
#         otx_client.config.api_key = "mock_key"
        
#         health = otx_client.health_check()
        
#         assert health['status'] == 'healthy'
#         assert health['mode'] == 'mock'
#         assert 'mock mode' in health['message']
    
#     @patch('requests.Session.get')
#     def test_health_check_real_api_healthy(self, mock_get, otx_client):
#         """Test health check with healthy real API"""
#         mock_response = Mock()
#         mock_response.status_code = 200
#         mock_response.json.return_value = {"pulses": []}
#         mock_get.return_value = mock_response
        
#         health = otx_client.health_check()
        
#         assert health['status'] == 'healthy'
#         assert health['mode'] == 'live'
#         assert 'accessible' in health['message']
    
#     @patch('requests.Session.get')
#     def test_health_check_real_api_unhealthy(self, mock_get, otx_client):
#         """Test health check with unhealthy real API"""
#         mock_get.side_effect = Exception("Connection failed")
        
#         health = otx_client.health_check()
        
#         assert health['status'] == 'unhealthy'
#         assert health['mode'] == 'live'
#         assert 'error' in health['message']


# class TestOTXClientIntegration:
#     """Integration tests for OTX client"""
    
#     def test_mock_data_consistency(self):
#         """Test that mock data is consistent across different indicator types"""
#         client = OTXClient(OTXConfig(api_key="mock_key"))
        
#         # Test all three indicator types
#         ip_event = client.get_ip_reputation("1.2.3.4")
#         domain_event = client.get_domain_reputation("example.com")
#         hash_event = client.get_file_hash_reputation("d41d8cd98f00b204e9800998ecf8427e")
        
#         # All should be IntelEvent instances
#         assert isinstance(ip_event, IntelEvent)
#         assert isinstance(domain_event, IntelEvent)
#         assert isinstance(hash_event, IntelEvent)
        
#         # All should have consistent structure
#         for event in [ip_event, domain_event, hash_event]:
#             assert event.source == "otx"
#             assert event.event_type == "threat_intel"
#             assert event.confidence > 0
#             assert event.severity in ["low", "medium", "high", "critical"]
#             assert isinstance(event.tags, list)
#             assert isinstance(event.raw_data, dict)
#             assert event.created_at is not None
#             assert event.updated_at is not None


if __name__ == "__main__":
    pytest.main([__file__])


import os
import time
import requests
from pydantic import HttpUrl
from dotenv import load_dotenv
load_dotenv() # Replace path with the path to the .env file

class OTXAPIError(Exception):
    """Custom exception for OTX API errors."""
    pass

class OTXConfig:
    api_key: str
    base_url: HttpUrl 
    rate_limit_delay: float
    max_retries: int
    timeout: int
    """Configuration class for OTXClient."""
    def __init__(self, api_key, base_url = None, 
                 rate_limit_delay = None, max_retries = None, timeout = None):
        self.api_key = api_key
        self.base_url=base_url or "https://otx.alienvault.com/api/v1",
        self.rate_limit_delay=rate_limit_delay or 2.0,
        self.max_retries=max_retries or 5,
        self.timeout=timeout or 60

class OTXClient:
    BASE = "https://otx.alienvault.com/api/v1"

    def __init__(self, api_key: str | None = None):
        self.key = api_key or os.getenv("OSINT_OTX_API_KEY", "")
        self.headers = {"X-OTX-API-KEY": self.key} if self.key else {}

    def fetch_ip_general(self, ip: str = "8.8.8.8") -> dict:
        url = f"{self.BASE}/indicators/IPv4/{ip}/general"
        for attempt in range(3):
            r = requests.get(url, headers=self.headers, timeout=10)
            if r.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            return r.json()
        return {}

    @staticmethod
    def normalize(raw: dict, ip: str) -> dict:
        return {
            "source": "otx",
            "ioc_type": "ipv4",
            "indicator": ip,
            "severity": 2,
            "raw": raw
        }

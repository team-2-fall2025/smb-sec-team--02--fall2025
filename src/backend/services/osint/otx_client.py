import os
import time
import requests

from dotenv import load_dotenv
load_dotenv() # Replace path with the path to the .env file

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

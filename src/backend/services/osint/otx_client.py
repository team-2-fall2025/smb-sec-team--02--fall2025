import os
import time
import requests
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()  # Replace path with the path to the .env file

class OTXAPIError(Exception):
	"""Custom exception for OTX API errors."""
	pass

@dataclass
class OTXConfig:
	"""Configuration class for OTXClient."""
	api_key: str = ""
	base_url: str = "https://otx.alienvault.com/api/v1"
	rate_limit_delay: float = 2.0
	max_retries: int = 5
	timeout: int = 60

class OTXClient:
	BASE = "https://otx.alienvault.com/api/v1"

	def __init__(self, api_key: str | None = None, config: OTXConfig | None = None):
		# Prefer explicit config, otherwise build one with the provided key
		self.config = config or OTXConfig(api_key=api_key or os.getenv("OSINT_OTX_API_KEY", ""))
		self.key = self.config.api_key
		self.headers = {"X-OTX-API-KEY": self.key} if self.key else {}
		self.base_url = self.config.base_url

	def fetch_ip_general(self, ip: str = "8.8.8.8") -> dict:
		url = f"{self.base_url}/indicators/IPv4/{ip}/general"
		for attempt in range(self.config.max_retries):
			r = requests.get(url, headers=self.headers, timeout=self.config.timeout)
			if r.status_code == 429:
				# Exponential backoff using configured base delay
				time.sleep(self.config.rate_limit_delay * (2 ** attempt))
				continue
			r.raise_for_status()
			return r.json()
		# If we exhausted retries, return empty dict as a safe fallback
		return {}

	@staticmethod
	def normalize(raw: dict, ip: str) -> dict:
		# Ensure severity is an integer and keep structure expected by tests
		severity = 0
		try:
			count = raw.get("pulse_info", {}).get("count")
			if isinstance(count, int) and count > 0:
				severity = 2
		except Exception:
			severity = 0

		return {
			"source": "otx",
			"ioc_type": "ipv4",
			"indicator": ip,
			"severity": int(severity),
			"raw": raw
		}

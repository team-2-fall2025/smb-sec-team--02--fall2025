from fastapi import FastAPI
from src.backend.db import intel_events
from src.backend.services.osint.otx_client import OTXClient

app = FastAPI()

@app.post("/api/osint/test")
def osint_test(ip: str = "8.8.8.8"):
    raw = OTXClient().fetch_ip_general(ip)
    doc = OTXClient.normalize(raw, ip)
    if doc:
        intel_events.insert_one(doc)
    return {"inserted": 1 if doc else 0, "indicator": ip}

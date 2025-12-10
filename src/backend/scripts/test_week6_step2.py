#!/usr/bin/env python3
"""
Seed detections so that one /api/respond/run call gives:

{
  "incidents_opened": 1,
  "incidents_attached": 1,
  "alerts_sent": 1,
  "suppressed_duplicates": 1
}

We:
- Find a real asset from the assets collection (e.g., AcmeRetail web-01)
- Insert 2 detections with the SAME (asset_id, indicator, source)
"""

import asyncio
from bson import ObjectId

from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client["smbsec"]



async def seed_for_test() -> None:
    assets = db["assets"]
    detections = db["detections"]

    # 1) Find a real asset to use (adjust filter if needed)
    asset = await assets.find_one({"org": "AcmeRetail", "name": "web-01"})
    if not asset:
        raise RuntimeError("Could not find asset {'org': 'AcmeRetail', 'name': 'web-01'}")

    asset_id: ObjectId = asset["_id"]
    print(f"Using asset_id={asset_id} for test detections")

    # Optional: clean old test docs first (only if you want a clean slate)
    # await detections.delete_many({"asset_id": asset_id, "indicator": "203.0.113.10", "source": "siem"})

    docs = [
        {
            "_id": ObjectId(),
            "title": "Suspicious login on web-01",
            "summary": "Multiple failed logins followed by a success.",
            "severity": "P2",
            "asset_id": asset_id,             # <-- real ObjectId
            "indicator": "203.0.113.10",      # match your screenshot IP if you like
            "source": "siem",
            "tags": ["login", "bruteforce"],
            "incident_handled": False,
        },
        {
            "_id": ObjectId(),
            "title": "Repeated login attempt on web-01",
            "summary": "Follow-up activity from same IP on web-01.",
            "severity": "P2",
            "asset_id": asset_id,             # SAME asset_id
            "indicator": "203.0.113.10",      # SAME indicator
            "source": "siem",                 # SAME source
            "tags": ["login", "repeat"],
            "incident_handled": False,
        },
    ]

    result = await detections.insert_many(docs)
    print(f"Inserted {len(result.inserted_ids)} test detections.")


if __name__ == "__main__":
    asyncio.run(seed_for_test())
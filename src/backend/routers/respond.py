from fastapi import APIRouter, HTTPException
from typing import Any, Dict
from pydantic import BaseModel
from bson import ObjectId
from pymongo import MongoClient
from agents.respond_agent import run_respond_agent, update_incident_status
from scripts.setup_db_week6 import (
    ensure_respond_collections,
    seed_respond_sample_data,
    MONGO_URI,
    DB_NAME,
)
router = APIRouter(prefix="/api/respond", tags=["respond"])

def _serialize_incident(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert ObjectId fields inside an incident doc to plain strings."""
    if not doc:
        return doc

    out = dict(doc)  # shallow copy

    # _id -> id
    if "_id" in out:
        out["id"] = str(out["_id"])
        del out["_id"]

    # primary_asset_id (single ObjectId)
    if "primary_asset_id" in out and isinstance(out["primary_asset_id"], ObjectId):
        out["primary_asset_id"] = str(out["primary_asset_id"])

    # detection_refs: list of ObjectId
    if "detection_refs" in out and isinstance(out["detection_refs"], list):
        out["detection_refs"] = [
            str(x) if isinstance(x, ObjectId) else x for x in out["detection_refs"]
        ]

    # risk_item_refs: list of ObjectId
    if "risk_item_refs" in out and isinstance(out["risk_item_refs"], list):
        out["risk_item_refs"] = [
            str(x) if isinstance(x, ObjectId) else x for x in out["risk_item_refs"]
        ]

    return out

@router.get("/ping")
def ping_respond():
    return {"area": "respond", "ok": True}


@router.get("/create")
async def create_respond_tables():
    """
    Initialize Respond / Incident collections + indexes and seed sample data.
    This will run when you open:
        http://127.0.0.1:8000/api/respond/create
    """
    # Create a sync client just for setup/seed
    client = MongoClient(MONGO_URI)
    db_sync = client[DB_NAME]

    # Run your existing sync helpers
    ensure_respond_collections(db_sync)
    seed_respond_sample_data(db_sync)

    # Optional: close client
    client.close()

    # Return only plain JSON
    return {
        "ok": True,
        "message": "Respond / Incident collections ensured and sample data seeded (if empty).",
    }

@router.post("/run")
async def respond_run():
    """
    Trigger the Respond / Playbook Agent (MVP).

    Returns:
        {
          "incidents_opened": int,
          "incidents_attached": int,
          "alerts_sent": int,
          "suppressed_duplicates": int
        }
    """
    summary = await run_respond_agent()
    return summary

# You can use POST here; it's fine for your project.
@router.post("/incidents/{incident_id}/status")
async def change_incident_status(incident_id: str):
    from motor.motor_asyncio import AsyncIOMotorClient
    import os

    MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client["smbsec"]

    """
    Change incident status with state-machine enforcement.

    Body JSON:
      {
        "status": "Containment",
        "actor": "alice"
      }
    """

    new_status = "Eradication"

    try:
        oid = ObjectId(incident_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid incident id")

    try:
        updated = await update_incident_status(oid, new_status)
    except ValueError as e:
        # e.g. invalid transition or incident not found
        raise HTTPException(status_code=400, detail=str(e))

    return _serialize_incident(updated)
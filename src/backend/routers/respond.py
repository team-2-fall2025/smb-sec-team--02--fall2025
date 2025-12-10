from fastapi import APIRouter, HTTPException, Body
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

# -----------------------------------------------------
# ❗ ONLY ONE router — DO NOT redefine it later!
# -----------------------------------------------------
router = APIRouter(prefix="/api/respond", tags=["respond"])


def _serialize_incident(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc

    out = dict(doc)

    if "_id" in out:
        out["id"] = str(out["_id"])
        del out["_id"]

    if "primary_asset_id" in out and isinstance(out["primary_asset_id"], ObjectId):
        out["primary_asset_id"] = str(out["primary_asset_id"])

    if "detection_refs" in out:
        out["detection_refs"] = [
            str(x) if isinstance(x, ObjectId) else x for x in out["detection_refs"]
        ]

    if "risk_item_refs" in out:
        out["risk_item_refs"] = [
            str(x) if isinstance(x, ObjectId) else x for x in out["risk_item_refs"]
        ]

    return out


# -----------------------------------------------------
# /ping
# -----------------------------------------------------
@router.get("/ping")
def ping_respond():
    return {"area": "respond", "ok": True}


# -----------------------------------------------------
# /create
# -----------------------------------------------------
@router.get("/create")
async def create_respond_tables():
    client = MongoClient(MONGO_URI)
    db_sync = client[DB_NAME]

    ensure_respond_collections(db_sync)
    seed_respond_sample_data(db_sync)

    client.close()

    return {
        "ok": True,
        "message": "Respond / Incident collections ensured and sample data seeded.",
    }


# -----------------------------------------------------
# /run  (GET + POST allowed)
# -----------------------------------------------------
@router.post("/run")
@router.get("/run")
async def respond_run():
    summary = await run_respond_agent()
    return summary


# -----------------------------------------------------
# Status update endpoint
# -----------------------------------------------------
class StatusUpdate(BaseModel):
    status: str
    actor: str | None = None


@router.post("/incidents/{incident_id}/status")
async def change_incident_status(
    incident_id: str,
    body: StatusUpdate = Body(...),
):
    try:
        oid = ObjectId(incident_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid incident id")

    try:
        updated = await update_incident_status(oid, body.status, body.actor)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "ok": True,
        "updated_status": body.status,
        "incident": _serialize_incident(updated),
    }

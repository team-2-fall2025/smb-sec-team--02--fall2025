from datetime import datetime
from fastapi import APIRouter, HTTPException, Body
from typing import Any, Dict, Optional
from fastapi.temp_pydantic_v1_params import Query
from pydantic import BaseModel
from bson import ObjectId
from pymongo import MongoClient
from db.mongo import db

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
        await update_incident_status(oid, body.status, body.actor)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "ok": True,
        "updated_status": body.status,
        "incident": "_serialize_incident(updated)",
    }

@router.get("/getIncidents", response_model=dict)
async def get_incidents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    severity: Optional[int] = None,
    sla_status: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Retrieve all incidents with optional filtering
    """

    query = {}
    
    if status:
        query["status"] = status
    
    if severity:
        query["severity"] = severity
    
    if sla_status:
        query["sla_status"] = sla_status
    
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"summary": {"$regex": search, "$options": "i"}},
            {"owner": {"$regex": search, "$options": "i"}}
        ]
    
    # Get total count
    total = await db.incidents.count_documents(query)
    
    # Fetch incidents with pagination
    cursor = await db.incidents.find(query).skip(skip).limit(limit).sort("opened_at", -1).to_list(length=total)
    
    # Convert MongoDB documents to Incident objects
    incidents = []
    for doc in cursor:
        # Convert ObjectId to string
        doc["_id"] = str(doc["_id"])
        doc["primary_asset_id"] = str(doc["primary_asset_id"])
        doc["asset_refs"] = None
        doc["detection_refs"] = None
        doc["risk_item_refs"] = None
        incidents.append(doc)
    
    return {
        "data": incidents,
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "limit": limit
    }
        

@router.get("/getIncident/{incident_id}", response_model=dict)
async def get_incident(incident_id: str):
    """
    Retrieve a single incident by ID
    """        
    # Fetch incident
    incident = await db.incidents.find_one({"_id": ObjectId(incident_id)})
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Convert ObjectId to string
    incident["_id"] = str(incident["_id"])
    incident["primary_asset_id"] = str(incident["primary_asset_id"])
    if not incident.get("asset_refs"):
        incident["asset_refs"] = []
        incident["asset_refs"].append(incident["primary_asset_id"])

    # Get related data
    incident["asset_refs"] = await db.assets.find({"_id": {"$in": incident["asset_refs"]}}).to_list(length=None)
    incident["detection_refs"] = await db.detections.find({"_id": {"$in": incident["detection_refs"]}}).to_list(length=None)
    incident["risk_item_refs"] = await db.risk_items.find({"_id": {"$in": incident["risk_item_refs"]}}).to_list(length=None)
    incident["tasks"] = await db.incident_tasks.find({"incident_id": ObjectId(incident_id)}).to_list(length=None)
    incident["evidence"] = await db.incident_evidence.find({"incident_id": ObjectId(incident_id)}).to_list(length=None)
    incident["timelines"] = await db.incident_timeline.find({"incident_id": ObjectId(incident_id)}).to_list(length=None)
    
    print(incident["evidence"])
    # Clean related data ObjectIds
    for asset in incident["asset_refs"]:
        asset["_id"] = str(asset["_id"])
    for detection in incident["detection_refs"]:
        detection["_id"] = str(detection["_id"])
        detection["asset_id"] = str(detection["asset_id"])
    for risk in incident["risk_item_refs"]:
        risk["_id"] = str(risk["_id"])
        risk["asset_id"] = str(risk["asset_id"])
    for task in incident["tasks"]:
        task["_id"] = str(task["_id"])
        task["incident_id"] = str(task["incident_id"])
    for ev in incident["evidence"]:
        ev["_id"] = str(ev["_id"])
        ev["incident_id"] = str(ev["incident_id"])
    for tl in incident["timelines"]:
        tl["_id"] = str(tl["_id"])
        tl["incident_id"] = str(tl["incident_id"])
    
    return incident

@router.post("/incidents/{incident_id}/tasks")
async def add_task(incident_id: str, task: dict):
    """Add task to incident"""
    from bson import ObjectId
    
    # Basic validation
    if not task.get("title"):
        raise HTTPException(status_code=400, detail="Task title required")
    
    # Create task document
    task_doc = {
        "incident_id": ObjectId(incident_id),
        "phase": task.get("phase", "Triage"),
        "title": task["title"],
        "assignee": task.get("assignee", ""),
        "status": "Open",
        "notes": task.get("notes", ""),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    # Insert
    await db.incident_tasks.insert_one(task_doc)
    
    # Log to timeline
    await db.incident_timeline.insert_one({
        "incident_id": ObjectId(incident_id),
        "ts": datetime.utcnow(),
        "actor": "system",
        "event_type": "task_added",
        "detail": f"Task '{task['title']}' added"
    })
    print("Task added to timeline", task_doc)
    # Convert ObjectId to string
    task_doc["_id"] = str(task_doc["_id"])
    task_doc["incident_id"] = incident_id
    
    return "task_doc"

@router.patch("/incidents/{incident_id}/tasks/{task_id}")
async def toggle_task(incident_id: str, task_id: str):
    """Toggle task status between Open/Done"""

    # Find and update task
    task = await db.incident_tasks.find_one({
        "_id": ObjectId(task_id),
        "incident_id": ObjectId(incident_id)
    })
    
    if not task:
        raise HTTPException(404, "Task not found")
    
    # Toggle status
    new_status = "Done" if task["status"] == "Open" else "Open"
    
    await db.incident_tasks.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
    )
    
    # Log to timeline
    await db.incident_timeline.insert_one({
        "incident_id": ObjectId(incident_id),
        "ts": datetime.utcnow(),
        "actor": "system",
        "event_type": "task_updated",
        "detail": f"Task '{task['title']}' marked as {new_status}"
    })
    
    return {"task_id": task_id, "status": new_status}

@router.post("/incidents/{incident_id}/evidence")
async def add_evidence(incident_id: str, evidence: dict):
    """Add evidence metadata to incident"""
    from bson import ObjectId
    
    # Required fields check
    if not evidence.get("location"):
        raise HTTPException(400, "Evidence location required")
    
    # Create evidence record
    evidence_id = ObjectId()
    evidence_doc = {
        "_id": evidence_id,
        "incident_id": ObjectId(incident_id),
        "type": evidence.get("type", "other"),
        "location": evidence["location"],
        "submitted_by": evidence.get("submitted_by", "system"),
        "submitted_at": datetime.utcnow()
    }
    
    # Optional fields
    if evidence.get("hash"):
        evidence_doc["hash"] = evidence["hash"]
    
    # Insert
    await db.incident_evidence.insert_one(evidence_doc)
    
    # Return
    evidence_doc["_id"] = str(evidence_id)
    evidence_doc["incident_id"] = incident_id
    
    return "evidence_doc"
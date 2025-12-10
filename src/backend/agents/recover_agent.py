# agents/recover_agent.py

from datetime import datetime
from typing import List, Literal, Optional, Union
from bson import ObjectId
from pydantic import BaseModel, Field, validator
from pymongo.database import Database

def _normalize_asset_id_for_query(raw: Union[str, int, ObjectId]):
    """
    Try to convert a string like '6938e2a58d025474c790e7e7' into ObjectId.
    If that fails, fall back to int or raw string.
    """
    # Already an ObjectId → just return
    if isinstance(raw, ObjectId):
        return raw

    # If it's a string, try ObjectId
    if isinstance(raw, str):
        try:
            return ObjectId(raw)
        except InvalidId:
            # Maybe they used numeric asset IDs
            if raw.isdigit():
                return int(raw)
            return raw

    # If it's an int, just return as-is
    return raw

def _json_safe_asset_id(raw):
    if isinstance(raw, ObjectId):
        return str(raw)
    return raw

class BackupReportIn(BaseModel):
    asset_id: Union[int, str]
    backup_type: Literal["full", "inc", "snapshot", "dbdump"]
    storage_location: str

    encrypted: bool = True
    frequency_minutes: Optional[int] = None
    rpo_target_minutes: Optional[int] = None

    status: Literal["success", "failure"]
    finished_at: datetime

    size_bytes: int = Field(..., alias="size_bytes")
    checksum: Optional[str] = None

    reported_by: Optional[str] = None  # optional explicit reporter

    @validator("size_bytes")
    def size_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("size_bytes must be > 0")
        return v

    @validator("checksum", always=True)
    def checksum_required_on_success(cls, v: Optional[str], values):
        status_val = values.get("status")
        if status_val == "success" and (v is None or not v.strip()):
            raise ValueError("checksum is required when status='success'")
        return v


def report_backup_intake(
    db: Database,
    payload: BackupReportIn,
    header_reported_by: Optional[str] = None,
) -> dict:
    """
    Core logic for '2) Backup intake (reporting endpoint)'.

    - Upserts into backup_sets.
    - Updates last_success_at / last_failure_at.
    - Returns a JSON object shaped like the example in the Week 7 doc:

    {
      "asset_id": 12,
      "backup_type": "snapshot",
      "storage_location": "...",
      "encrypted": true,
      "frequency_minutes": 1440,
      "rpo_target_minutes": 1440,
      "status": "success",
      "finished_at": "2025-11-08T02:14:00Z",
      "size_bytes": 4289114112,
      "checksum": "sha256:abcd..."
    }
    """
    col = db.get_collection("backup_sets")

    reporter = payload.reported_by or header_reported_by or "recover-agent"
    now = datetime.utcnow()

    # Upsert key for this backup set
    filter_doc = {
        "asset_id": payload.asset_id,
        "backup_type": payload.backup_type,
        "storage_location": payload.storage_location,
    }

    update_doc = {
        "$set": {
            "asset_id": payload.asset_id,
            "backup_type": payload.backup_type,
            "storage_location": payload.storage_location,
            "encrypted": payload.encrypted,
            "frequency_minutes": payload.frequency_minutes,
            "rpo_target_minutes": payload.rpo_target_minutes,
            "last_size_bytes": payload.size_bytes,
            "last_checksum": payload.checksum,
            "reported_by": reporter,
            "reported_at": now,
        },
        "$setOnInsert": {
            "created_at": now,
        },
    }

    if payload.status == "success":
        update_doc["$set"]["last_success_at"] = payload.finished_at
    else:
        update_doc["$set"]["last_failure_at"] = payload.finished_at

    col.update_one(filter_doc, update_doc, upsert=True)

    # ✅ Response strictly follows the assignment's example format
    return {
        "asset_id": payload.asset_id,
        "backup_type": payload.backup_type,
        "storage_location": payload.storage_location,
        "encrypted": payload.encrypted,
        "frequency_minutes": payload.frequency_minutes,
        "rpo_target_minutes": payload.rpo_target_minutes,
        "status": payload.status,
        "finished_at": payload.finished_at,
        "size_bytes": payload.size_bytes,
        "checksum": payload.checksum,
    }

def get_backup_reports_by_asset_id(db, asset_id: Union[int, str]) -> List[dict]:
    col = db.get_collection("backup_sets")

    # Normalize incoming asset_id (string -> ObjectId/int/etc.)
    normalized_id = _normalize_asset_id_for_query(asset_id)

    docs = list(col.find({"asset_id": normalized_id}))

    results = []

    for doc in docs:
        # Decide status/finished_at based on last_success_at/last_failure_at
        if doc.get("last_success_at"):
            status = "success"
            finished_at = doc.get("last_success_at")
        elif doc.get("last_failure_at"):
            status = "failure"
            finished_at = doc.get("last_failure_at")
        else:
            status = "unknown"
            finished_at = None

        results.append({
            # ✅ convert ObjectId → string
            "asset_id": _json_safe_asset_id(doc.get("asset_id")),
            "backup_type": doc.get("backup_type"),
            "storage_location": doc.get("storage_location"),
            "encrypted": doc.get("encrypted"),
            "frequency_minutes": doc.get("frequency_minutes"),
            "rpo_target_minutes": doc.get("rpo_target_minutes"),
            "status": status,
            "finished_at": finished_at,
            "size_bytes": doc.get("last_size_bytes"),
            "checksum": doc.get("last_checksum"),
        })

    return results
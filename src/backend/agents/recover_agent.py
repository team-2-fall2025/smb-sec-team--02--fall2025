# agents/recover_agent.py

from datetime import datetime
from typing import List, Literal, Optional, Union
from bson import ObjectId
from bson.errors import InvalidId
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
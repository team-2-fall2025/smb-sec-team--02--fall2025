# agents/recover_agent.py

from datetime import datetime
from typing import Any, List, Literal, Optional, Union
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

# class RestoreTestIn(BaseModel):
#     asset_id: Union[int, str]
#     backup_set_id: Union[int, str]

#     test_started_at: datetime
#     test_completed_at: datetime

#     result: str
#     logs_location: Optional[str] = None
#     verifier_hash: Optional[str] = None

#     rto_target_minutes: Optional[int] = None
#     notes: Optional[str] = None

#     reported_by: Optional[str] = None

# def _open_or_update_resilience_finding_for_restore(
#     db: Database,
#     asset_id: Any,
#     finding_type: Literal["rto_breach", "restore_failed", "rpo_breach"],
#     detail: str,
#     severity: int,
# ) -> dict:
#     """
#     Create or update a row in resilience_findings that matches the existing
#     table format:

#       {
#         _id: ...,
#         asset_id: "6938e2a58d025474c790e7e7",
#         type: "restore_failed" | "rpo_breach" | "rto_breach",
#         severity: 3/4,
#         status: "Open" | "Closed",
#         opened_at: <datetime>,
#         updated_at: <datetime>,
#         detail: "...",
#         linked_risk_item_id: null,
#         closed_at: <datetime> | null
#       }
#     """

#     findings = db.get_collection("resilience_findings")
#     now = datetime.utcnow()

#     # 🔑 Store asset_id as a string to match your screenshot/table
#     asset_key = str(asset_id)

#     existing = findings.find_one(
#         {
#             "asset_id": asset_key,
#             "type": finding_type,
#             "status": {"$ne": "Closed"},
#         }
#     )

#     if existing:
#         findings.update_one(
#             {"_id": existing["_id"]},
#             {
#                 "$set": {
#                     "detail": detail,
#                     "severity": severity,
#                     "updated_at": now,
#                 }
#             },
#         )
#         existing["detail"] = detail
#         existing["severity"] = severity
#         existing["updated_at"] = now
#         # Make _id JSON-friendly if you return it
#         existing["_id"] = str(existing["_id"])
#         return existing

#     doc = {
#         "asset_id": asset_key,
#         "type": finding_type,
#         "severity": severity,
#         "status": "Open",
#         "opened_at": now,
#         "updated_at": now,
#         "detail": detail,
#         "linked_risk_item_id": None,
#         "closed_at": None,
#     }
#     inserted_id = findings.insert_one(doc).inserted_id
#     doc["_id"] = str(inserted_id)
#     return doc

def _normalize_id_for_query(raw: Union[str, int, ObjectId]):
    # Shared helper: convert 24-hex string → ObjectId; numbers stay numbers; others stay strings
    if isinstance(raw, ObjectId):
        return raw

    if isinstance(raw, str):
        try:
            return ObjectId(raw)
        except InvalidId:
            if raw.isdigit():
                return int(raw)
            return raw

    return raw

def _json_safe_id(raw):
    if isinstance(raw, ObjectId):
        return str(raw)
    return raw

# def record_restore_test(
#     db: Database,
#     payload: RestoreTestIn,
#     header_reported_by: Optional[str] = None,
# ) -> dict:
#     """
#     3) Restore test workflow.

#     - Inserts a restore_tests row.
#     - Calculates duration_minutes.
#     - If result='fail' → open/update 'restore_failed' finding.
#     - If duration > rto_target_minutes → open/update 'rto_breach' finding.
#     - Findings match your table format.
#     """
#     col = db.get_collection("restore_tests")

#     reporter = payload.reported_by or header_reported_by or "recover-agent"
#     now = datetime.utcnow()

#     # For restore_tests we still normalize IDs for consistency with backup_sets
#     normalized_asset_id = _normalize_id_for_query(payload.asset_id)
#     normalized_backup_set_id = _normalize_id_for_query(payload.backup_set_id)

#     print( col.distinct("asset_id"))

#     # Duration in minutes
#     delta = payload.test_completed_at - payload.test_started_at
#     duration_minutes = int(round(delta.total_seconds() / 60.0))

#     restore_doc = {
#         "asset_id": normalized_asset_id,
#         "backup_set_id": normalized_backup_set_id,
#         "test_started_at": payload.test_started_at,
#         "test_completed_at": payload.test_completed_at,
#         "duration_minutes": duration_minutes,
#         "result": payload.result,
#         "logs_location": payload.logs_location,
#         "verifier_hash": payload.verifier_hash,
#         "rto_target_minutes": payload.rto_target_minutes,
#         "notes": payload.notes,
#         "reported_by": reporter,
#         "reported_at": now,
#     }

#     inserted_id = col.insert_one(restore_doc).inserted_id
#     restore_doc["_id"] = inserted_id  # internal only

#     # ---- Create/update findings, following your table format ----
#     finding = None

#     # 1) Restore failed
#     if payload.result == "fail":
#         detail = (
#             f"Latest restore test failed; backup_set={normalized_backup_set_id}"
#         )
#         finding = _open_or_update_resilience_finding_for_restore(
#             db=db,
#             asset_id=normalized_asset_id,
#             finding_type="restore_failed",
#             detail=detail,
#             severity=4,
#         )

#     # 2) RTO breach
#     elif (
#         payload.rto_target_minutes is not None
#         and duration_minutes > payload.rto_target_minutes
#     ):
#         detail = (
#             f"RTO breach: duration {duration_minutes}m "
#             f"> target {payload.rto_target_minutes}m."
#         )
#         finding = _open_or_update_resilience_finding_for_restore(
#             db=db,
#             asset_id=normalized_asset_id,
#             finding_type="rto_breach",
#             detail=detail,
#             severity=3,
#         )

#     # ---- Response: echo the test + duration (no weird fields) ----
#     response = {
#         "asset_id": _json_safe_id(normalized_asset_id),
#         "backup_set_id": _json_safe_id(normalized_backup_set_id),
#         "test_started_at": payload.test_started_at,
#         "test_completed_at": payload.test_completed_at,
#         "duration_minutes": duration_minutes,
#         "result": payload.result,
#         "logs_location": payload.logs_location,
#         "verifier_hash": payload.verifier_hash,
#         "rto_target_minutes": payload.rto_target_minutes,
#         "notes": payload.notes,
#     }

#     # Optional: include finding info in response for debugging/UI
#     if finding is not None:
#         response["finding"] = finding

#     return response

def get_restore_tests_by_asset_id(
    db: Database,
    asset_id: Union[str, int],
) -> List[dict]:
    """
    Fetch all restore_tests rows for a given asset_id.

    Returns a list of tests with fields shaped similarly to the restore
    test payload + duration_minutes.
    """
    col = db.get_collection("restore_tests")

    normalized_id = _normalize_id_for_query(asset_id)

    # Get tests for this asset, newest first (or change sort if you prefer)
    docs = list(
        col.find({"asset_id": normalized_id}).sort("test_started_at", -1)
    )

    results: List[dict] = []

    for doc in docs:
        results.append(
            {
                "asset_id": _json_safe_id(doc.get("asset_id")),
                "backup_set_id": _json_safe_id(doc.get("backup_set_id")),
                "test_started_at": doc.get("test_started_at"),
                "test_completed_at": doc.get("test_completed_at"),
                "duration_minutes": doc.get("duration_minutes"),
                "result": doc.get("result"),
                "logs_location": doc.get("logs_location"),
                "verifier_hash": doc.get("verifier_hash"),
                "rto_target_minutes": doc.get("rto_target_minutes"),
                "notes": doc.get("notes"),
            }
        )

    return results
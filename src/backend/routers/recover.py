import os
from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from scripts.setup_db_week7 import ensure_recover_indexes, seed_recover_data, get_db
from pymongo import MongoClient
from agents.recover_agent import get_backup_reports_by_asset_id
# from agents.recover_agent import RestoreTestIn, record_restore_test
from agents.recover_agent import get_restore_tests_by_asset_id
from bson import ObjectId
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta


router = APIRouter(prefix="/api/recover", tags=["recover"])

@router.get("/ping")
def ping_recover():
    return {"area": "recover", "ok": True}

@router.get("/create")
def create_recover_tables():
    """
    Initializes Week 7 Recover / Resilience collections,
    creates indexes, and seeds sample data.
    """
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(MONGO_URI)
    db = get_db()

    ensure_recover_indexes(db)
    seed_recover_data(db)

    client.close()

    return {
        "status": "success",
        "message": "Week 7 Recover / Resilience collections created and seeded"
    }

class RestoreTestIn(BaseModel):
    asset_id: str
    backup_set_id: Optional[str] = None
    test_started_at: datetime
    test_completed_at: datetime
    result: str  # "pass" or "fail"
    logs_location: Optional[str] = None
    rto_target_minutes: int
    notes: Optional[str] = None

def convert_objectid(doc):
    """Recursively convert ObjectId to str so FastAPI can serialize."""
    if isinstance(doc, list):
        return [convert_objectid(i) for i in doc]

    if isinstance(doc, dict):
        new_doc = {}
        for k, v in doc.items():
            if isinstance(v, ObjectId):
                new_doc[k] = str(v)
            elif isinstance(v, dict) or isinstance(v, list):
                new_doc[k] = convert_objectid(v)
            else:
                new_doc[k] = v
        return new_doc

    return doc
class BackupReportIn(BaseModel):
    asset_id: str
    backup_type: str
    storage_location: str
    encrypted: bool
    frequency_minutes: int
    rpo_target_minutes: int
    status: str  # "success" or "failure"
    finished_at: datetime
    size_bytes: int
    checksum: Optional[str] = None


@router.post("/backup/report")
def report_backup(payload: BackupReportIn):
    """
    Step 3 - Backup intake & validation

    a) Endpoint for reporting backup metadata.
    b) Validates size > 0 and checksum exists if backup succeeded.
    c) Writes/updates backup_sets collection.
    """

    db = get_db()

    # -----------------------------
    # Basic validation rules
    # -----------------------------
    if payload.status not in ("success", "failure"):
        raise HTTPException(status_code=400, detail="Status must be success or failure")

    if payload.status == "success":
        if payload.size_bytes <= 0:
            raise HTTPException(status_code=400, detail="Backup size must be > 0 for successful backup")

        if not payload.checksum:
            raise HTTPException(status_code=400, detail="Checksum required for successful backup")

    # Fields always updated
    common_fields = {
        "backup_type": payload.backup_type,
        "storage_location": payload.storage_location,
        "encrypted": payload.encrypted,
        "frequency_minutes": payload.frequency_minutes,
        "rpo_target_minutes": payload.rpo_target_minutes,
        "updated_at": datetime.now(timezone.utc)
    }

    # Successful backup
    if payload.status == "success":
        update = {
            **common_fields,
            "last_success_at": payload.finished_at,
            "last_size_bytes": payload.size_bytes,
            "last_checksum": payload.checksum
        }

    # Failed backup
    else:
        update = {
            **common_fields,
            "last_failure_at": payload.finished_at
        }

    # -----------------------------
    # Upsert backup metadata
    # -----------------------------
    db.backup_sets.update_one(
        {"asset_id": payload.asset_id},
        {"$set": update},
        upsert=True
    )

    return {
        "ok": True,
        "message": "Backup report stored",
        "asset_id": payload.asset_id,
        "status": payload.status
    }


def record_restore_test(db, payload: RestoreTestIn, reported_by=None):     #Step 4-------- restore_tests  resilience_findings
    """
    Records a restore test, computes duration, evaluates RTO compliance,
    stores next-due test date, and opens findings if needed.

    When a restore test payload is received, the system calculates the duration_minutes.
    If the result is fail, it creates a restore_failed finding.
    If the result is pass but the duration exceeds the RTO target, it creates an rto_breach finding.
    If the result is pass and the duration is within the RTO target, no finding is created.


    """

    # 1) compute duration
    duration = (payload.test_completed_at - payload.test_started_at).total_seconds() / 60

    restore_doc = {
        "asset_id": payload.asset_id,
        "backup_set_id": payload.backup_set_id,  # 不转换为 ObjectId
        "test_started_at": payload.test_started_at,
        "test_completed_at": payload.test_completed_at,
        "duration_minutes": duration,
        "result": payload.result,
        "logs_location": payload.logs_location,
        "rto_target_minutes": payload.rto_target_minutes,
        "notes": payload.notes,
        "reported_by": reported_by,
        "reported_at": datetime.now(timezone.utc),
    }

    # Insert restore test document
    res = db.restore_tests.insert_one(restore_doc)
    restore_id = res.inserted_id

    # 2) Determine RTO compliance
    rto_ok = payload.result == "pass" and duration <= payload.rto_target_minutes

    # 3) Compute next_due_test_date (default: 30 days)
    next_due = payload.test_completed_at + timedelta(days=30)
    db.restore_tests.update_one(
        {"_id": restore_id},
        {"$set": {"next_due_test_at": next_due}},
    )

    # 4) Open finding if needed
    if not rto_ok:
        finding_type = "restore_failed" if payload.result == "fail" else "rto_breach"
        _open_or_update_restore_finding(db, payload.asset_id, finding_type, duration, payload.rto_target_minutes)

    # Return stored record to client
    restore_doc["_id"] = restore_id
    restore_doc["next_due_test_at"] = next_due
    restore_doc["rto_ok"] = rto_ok
    return convert_objectid(restore_doc)


def _open_or_update_restore_finding(db, asset_id, finding_type, duration, target):
    now = datetime.now(timezone.utc)

    detail_text = f"RTO target={target} min, actual duration={duration} min"

    db.resilience_findings.update_one(
        {
            "asset_id": asset_id,
            "type": finding_type,
            "status": "Open"
        },
        {
            "$set": {
                "updated_at": now,
                "detail": detail_text,
            },
            "$setOnInsert": {
                "severity": 3,
                "opened_at": now,
                "status": "Open",
            }
        },
        upsert=True
    )




@router.get("/report/{asset_id}")
def get_backup_reports(asset_id: str):
    """
    Get all backup reports for a specific asset_id.

    Example:
    GET /api/backups/report/12
    """
    db = get_db()
    results = get_backup_reports_by_asset_id(db, asset_id)

    return results

# @router.post("/test")
# def post_restore_test(
#     payload: RestoreTestIn,
#     x_reported_by: Optional[str] = Header(default=None, alias="X-Reported-By"),
# ):
#     db = get_db()
#     test = record_restore_test(db, payload, header_reported_by=x_reported_by)
#     return test

@router.get("/test/{asset_id}")
def get_restore_tests(asset_id: str):
    db = get_db()
    tests = get_restore_tests_by_asset_id(db, asset_id)
    return {
        "asset_id": asset_id,
        "count": len(tests),
        "tests": tests,
    }


@router.post("/test")
def post_restore_test(
    payload: RestoreTestIn,
    x_reported_by: Optional[str] = Header(default=None, alias="X-Reported-By"),
):
    db = get_db()
    test_doc = record_restore_test(db, payload, reported_by=x_reported_by)
    return test_doc

@router.get("/run")
def run_recover_agent_get():
    return run_recover_agent()

def ensure_aware(dt):
    """Ensure DB-loaded datetime is timezone aware."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@router.post("/run")
def run_recover_agent():
    """
    Week 7 - Resilience Agent:
    - Evaluate RPO/RTO
    - Compute resilience score
    - Update residual risk
    - Open/update findings

    Step 5 scans the backup_sets table (for RPO fields) and the restore_tests table (for RTO fields),
    and based on the evaluation results, it updates the assets table by adjusting residual_risk and
    updates the resilience_findings table by creating or modifying findings.

    """
    db = get_db()
    now = datetime.now(timezone.utc)

    assets = list(db.backup_sets.find())  # assets with backup info

    summary = {
        "assets_evaluated": 0,
        "rpo_compliant": 0,
        "rto_compliant": 0,
        "findings_opened": 0,
        "findings_updated": 0,
    }

    for asset in assets:
        asset_id = asset["asset_id"]
        summary["assets_evaluated"] += 1

        # ------------------------------------------------
        # 1) RPO Evaluation
        # ------------------------------------------------
        last_success = ensure_aware(asset.get("last_success_at"))
        rpo_target = asset.get("rpo_target_minutes", 1440)

        if last_success:
            minutes_since_backup = (now - last_success).total_seconds() / 60
            rpo_ok = minutes_since_backup <= rpo_target
        else:
            minutes_since_backup = None
            rpo_ok = False

        if rpo_ok:
            summary["rpo_compliant"] += 1
        else:
            detail = (
                f"RPO target={rpo_target}m, "
                f"last success {minutes_since_backup}m ago" if minutes_since_backup else
                "No successful backup found"
            )
            _store_or_update_finding(db, asset_id, "rpo_breach", detail, summary)

        # ------------------------------------------------
        # 2) RTO Evaluation
        # ------------------------------------------------
        last_test = db.restore_tests.find_one(
            {"asset_id": asset_id},
            sort=[("test_completed_at", -1)]
        )

        if last_test:
            test_duration = last_test.get("duration_minutes", 999999)
            rto_target = last_test.get("rto_target_minutes", 30)
            result = last_test.get("result")

            rto_ok = (result == "pass" and test_duration <= rto_target)
        else:
            result = None
            rto_ok = False

        if rto_ok:
            summary["rto_compliant"] += 1
        else:
            if result == "fail":
                type_ = "restore_failed"
                detail = "Restore test failed"
            else:
                type_ = "rto_breach"
                detail = f"RTO target={rto_target}m, duration={test_duration}"

            _store_or_update_finding(db, asset_id, type_, detail, summary)

        # ------------------------------------------------
        # 3) Resilience Score Calculation
        # ------------------------------------------------
        score = 100

        # Penalty: No backup in > 2×RPO window
        if last_success:
            if minutes_since_backup > (rpo_target * 2):
                score -= 40
        else:
            score -= 40

        if not rpo_ok:
            score -= 25

        if not rto_ok:
            score -= 25

        if result == "fail":
            score -= 20

        score = max(0, min(100, score))  # clamp score

        # ------------------------------------------------
        # 4) Residual Risk Update
        # ------------------------------------------------
        asset_record = db.assets.find_one({"asset_id": asset_id}) or {}
        prior_risk = asset_record.get("residual_risk", 50)

        new_risk = round(prior_risk * (1 - score / 300))

        db.assets.update_one(
            {"asset_id": asset_id},
            {"$set": {"residual_risk": new_risk}},
            upsert=True
        )

    return summary


def _store_or_update_finding(db, asset_id, type_, detail, summary):
    """Upsert resilience findings."""
    now = datetime.now(timezone.utc)

    result = db.resilience_findings.update_one(
        {
            "asset_id": asset_id,
            "type": type_,
            "status": "Open"
        },
        {
            "$set": {
                "detail": detail,
                "updated_at": now,
            },
            "$setOnInsert": {
                "opened_at": now,
                "status": "Open",
                "severity": 3
            }
        },
        upsert=True
    )

    if result.upserted_id:
        summary["findings_opened"] += 1
    else:
        summary["findings_updated"] += 1
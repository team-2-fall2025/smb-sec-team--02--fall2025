import os
from typing import Optional
from fastapi import APIRouter, Header
from scripts.setup_db_week7 import ensure_recover_indexes, seed_recover_data, get_db
from pymongo import MongoClient
from agents.recover_agent import get_backup_reports_by_asset_id
# from agents.recover_agent import RestoreTestIn, record_restore_test
from agents.recover_agent import get_restore_tests_by_asset_id

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
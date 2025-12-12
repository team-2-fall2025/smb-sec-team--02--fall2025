#!/usr/bin/env python3
"""
Week 7 – Recover / Resilience Agent

This script does everything for Week 7:
  1) Defines MongoDB/Pydantic models for:
       - dr_plans
       - backup_sets
       - restore_tests
       - resilience_findings
  2) Ensures collections + indexes exist.
  3) Seeds some realistic sample data (only if collections are empty).

Env (defaults):
  MONGO_URI=mongodb://localhost:27017
  DB_NAME=smbsec

Usage:
  python scripts/setup_db_week7.py
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import List, Optional, Literal

from bson import ObjectId
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Mongo connection helpers
# ---------------------------------------------------------------------------

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "smbsec")


def get_db() -> Database:
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]


# ---------------------------------------------------------------------------
# Shared Pydantic / ObjectId helpers
# ---------------------------------------------------------------------------

class PyObjectId(ObjectId):
    """Pydantic-friendly ObjectId wrapper."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            try:
                return ObjectId(v)
            except Exception as exc:  # noqa: BLE001
                raise ValueError("Invalid ObjectId string") from exc
        raise TypeError("ObjectId or valid ObjectId string required")


class MongoModel(BaseModel):
    """Base model with _id support."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True
        orm_mode = True


# ---------------------------------------------------------------------------
# 1) Data models (suggested tables/collections)
# ---------------------------------------------------------------------------

# ---------- dr_plans ----------

class DRPlan(MongoModel):
    """
    dr_plans

    Fields:
      - service_or_group: e.g., "Customer Web Portal", "Payroll Database"
      - rpo_target_minutes: RPO target in minutes
      - rto_target_minutes: RTO target in minutes
      - runbook_md: Markdown DR runbook text
      - owner: owner email/name
      - last_reviewed_at: last time the DR plan was reviewed
      - tags: list of strings (e.g., ["web", "production", "critical"])
    """

    service_or_group: str
    rpo_target_minutes: int
    rto_target_minutes: int

    runbook_md: str = ""
    owner: Optional[str] = None
    last_reviewed_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)


# ---------- backup_sets ----------

BackupTypeLiteral = Literal["full", "inc", "snapshot", "dbdump"]


class BackupSet(MongoModel):
    """
    backup_sets (one per protected asset or dataset)

    Fields:
      - asset_id: FK to an asset (ObjectId)
      - backup_type: "full" | "inc" | "snapshot" | "dbdump"
      - storage_location: path or URL, e.g., "s3://bucket/..."
      - encrypted: bool
      - last_success_at: datetime of last successful backup
      - last_failure_at: datetime of last failed backup
      - frequency_minutes: how often backups run
      - rpo_target_minutes: RPO target for this backup set
      - last_size_bytes: size of last backup
      - last_checksum: optional checksum/hash
      - notes: free text
      - reported_by / reported_at: simple audit trail (optional)
    """

    asset_id: PyObjectId
    backup_type: BackupTypeLiteral
    storage_location: str

    encrypted: bool = True
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None

    frequency_minutes: Optional[int] = None
    rpo_target_minutes: Optional[int] = None

    last_size_bytes: Optional[int] = None
    last_checksum: Optional[str] = None

    notes: Optional[str] = None
    reported_by: Optional[str] = None
    reported_at: Optional[datetime] = None


# ---------- restore_tests ----------

RestoreResultLiteral = Literal["pass", "fail"]


class RestoreTest(MongoModel):
    """
    restore_tests

    Fields:
      - asset_id: FK to asset
      - backup_set_id: FK to backup_sets
      - test_started_at / test_completed_at: timestamps
      - duration_minutes: duration of restore test
      - result: "pass" | "fail"
      - logs_location: URL/path to logs
      - verifier_hash: optional hash/signature for verification
      - rto_target_minutes: RTO target for this restore path
      - notes: free text
      - reported_by / reported_at: simple audit trail (optional)
    """

    asset_id: PyObjectId
    backup_set_id: PyObjectId

    test_started_at: datetime
    test_completed_at: datetime
    duration_minutes: Optional[int] = None

    result: RestoreResultLiteral
    logs_location: Optional[str] = None
    verifier_hash: Optional[str] = None

    rto_target_minutes: Optional[int] = None
    notes: Optional[str] = None

    reported_by: Optional[str] = None
    reported_at: Optional[datetime] = None


# ---------- resilience_findings ----------

FindingTypeLiteral = Literal[
    "rpo_breach",
    "rto_breach",
    "restore_failed",
    "no_backups",
]

FindingStatusLiteral = Literal["Open", "In-Progress", "Closed"]


class ResilienceFinding(MongoModel):
    """
    resilience_findings

    Fields:
      - asset_id: FK to asset
      - type: "rpo_breach" | "rto_breach" | "restore_failed" | "no_backups"
      - severity: 1..5
      - status: "Open" | "In-Progress" | "Closed"
      - opened_at / updated_at / closed_at
      - detail: short description
      - linked_risk_item_id: optional FK into risk register (if you have one)
    """

    asset_id: PyObjectId
    type: FindingTypeLiteral

    severity: int = Field(ge=1, le=5)
    status: FindingStatusLiteral = "Open"

    opened_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None

    detail: str
    linked_risk_item_id: Optional[PyObjectId] = None


# ---------------------------------------------------------------------------
# 2) Index creation
# ---------------------------------------------------------------------------

def ensure_recover_indexes(db: Database) -> None:
    """
    Create collections & indexes for Week 7 Recover / Resilience.

    Indexes:
      - dr_plans:            service_or_group, tags
      - backup_sets:         (asset_id, last_success_at)
      - restore_tests:       (asset_id, test_completed_at)
      - resilience_findings: (status, severity), type
    """
    # dr_plans
    dr_plans = db.get_collection("dr_plans")
    dr_plans.create_index([("service_or_group", ASCENDING)], name="service")
    dr_plans.create_index([("tags", ASCENDING)], name="tags")

    # backup_sets
    backup_sets = db.get_collection("backup_sets")
    backup_sets.create_index(
        [("asset_id", ASCENDING), ("last_success_at", DESCENDING)],
        name="asset_last_success",
    )

    # restore_tests
    restore_tests = db.get_collection("restore_tests")
    restore_tests.create_index(
        [("asset_id", ASCENDING), ("test_completed_at", DESCENDING)],
        name="asset_last_test",
    )

    # resilience_findings
    findings = db.get_collection("resilience_findings")
    findings.create_index(
        [("status", ASCENDING), ("severity", DESCENDING)],
        name="status_severity",
    )
    findings.create_index(
        [("type", ASCENDING)],
        name="type",
    )


# ---------------------------------------------------------------------------
# 3) Seed sample data
# ---------------------------------------------------------------------------

def seed_recover_data(db: Database) -> None:
    """
    Seed realistic sample data for Week 7.

    To avoid duplicates, this only inserts if the main collections are empty.
    """
    if db.dr_plans.count_documents({}) > 0:
        print("dr_plans already has data; skipping seed.")
        return

    print("Seeding Week 7 Recover / Resilience data...")

    # Example asset IDs (you could link these to an actual assets collection)
    asset_web_id = ObjectId()
    asset_db_id = ObjectId()

    # ---- dr_plans ----
    dr_plans_docs = [
        {
            "service_or_group": "Customer Web Portal",
            "rpo_target_minutes": 15,
            "rto_target_minutes": 60,
            "runbook_md": (
                "1. Failover to AWS standby\n"
                "2. Restore latest DB snapshot\n"
                "3. Validate login and checkout workflows\n"
            ),
            "owner": "ops@acme.com",
            "last_reviewed_at": datetime.utcnow() - timedelta(days=30),
            "tags": ["web", "production", "critical"],
        },
        {
            "service_or_group": "Payroll Database",
            "rpo_target_minutes": 60,
            "rto_target_minutes": 240,
            "runbook_md": (
                "1. Restore encrypted DB dump to standby instance\n"
                "2. Run consistency checks\n"
                "3. Validate last payroll batch\n"
            ),
            "owner": "it@acme.com",
            "last_reviewed_at": datetime.utcnow() - timedelta(days=90),
            "tags": ["finance", "restricted"],
        },
    ]
    db.dr_plans.insert_many(dr_plans_docs)

    # ---- backup_sets ----
    backup_sets_docs = [
        {
            "asset_id": asset_web_id,
            "backup_type": "snapshot",
            "storage_location": "s3://acme-backups/web-portal/",
            "encrypted": True,
            "last_success_at": datetime.utcnow() - timedelta(hours=4),
            "frequency_minutes": 60,
            "rpo_target_minutes": 15,
            "last_size_bytes": 3_200_000_000,
            "notes": "Hourly EC2 snapshot of web tier",
            "reported_by": "backup-bot",
            "reported_at": datetime.utcnow() - timedelta(hours=4),
        },
        {
            "asset_id": asset_db_id,
            "backup_type": "dbdump",
            "storage_location": "s3://acme-backups/payroll-db/",
            "encrypted": True,
            "last_success_at": datetime.utcnow() - timedelta(days=1),
            "frequency_minutes": 1440,
            "rpo_target_minutes": 60,
            "last_size_bytes": 18_700_000_000,
            "notes": "Nightly encrypted SQL dump",
            "reported_by": "backup-bot",
            "reported_at": datetime.utcnow() - timedelta(days=1),
        },
    ]
    backup_ids = db.backup_sets.insert_many(backup_sets_docs).inserted_ids

    # ---- restore_tests ----
    restore_tests_docs = [
        {
            "asset_id": asset_web_id,
            "backup_set_id": backup_ids[0],
            "test_started_at": datetime.utcnow() - timedelta(hours=2),
            "test_completed_at": datetime.utcnow() - timedelta(hours=1, minutes=20),
            "duration_minutes": 40,
            "result": "pass",
            "logs_location": "s3://acme-logs/restore-tests/web-portal.log",
            "rto_target_minutes": 60,
            "notes": "Full snapshot restore validated on staging",
            "reported_by": "alice",
            "reported_at": datetime.utcnow() - timedelta(hours=1, minutes=20),
        },
        {
            "asset_id": asset_db_id,
            "backup_set_id": backup_ids[1],
            "test_started_at": datetime.utcnow() - timedelta(days=2, hours=3),
            "test_completed_at": datetime.utcnow() - timedelta(days=2),
            "duration_minutes": 180,
            "result": "fail",
            "logs_location": "s3://acme-logs/restore-tests/payroll-db.log",
            "rto_target_minutes": 240,
            "notes": "Checksum mismatch during restore",
            "reported_by": "bob",
            "reported_at": datetime.utcnow() - timedelta(days=2),
        },
    ]
    db.restore_tests.insert_many(restore_tests_docs)

    # ---- resilience_findings ----
    findings_docs = [
        {
            "asset_id": asset_db_id,
            "type": "restore_failed",
            "severity": 4,
            "status": "Open",
            "opened_at": datetime.utcnow() - timedelta(days=1),
            "updated_at": datetime.utcnow() - timedelta(days=1),
            "detail": "Latest payroll restore test failed due to corrupted backup",
            "linked_risk_item_id": None,
        },
        {
            "asset_id": asset_web_id,
            "type": "rpo_breach",
            "severity": 3,
            "status": "Closed",
            "opened_at": datetime.utcnow() - timedelta(days=10),
            "updated_at": datetime.utcnow() - timedelta(days=7),
            "closed_at": datetime.utcnow() - timedelta(days=7),
            "detail": "Backup delay exceeded 15-minute RPO during outage window",
            "linked_risk_item_id": None,
        },
    ]
    db.resilience_findings.insert_many(findings_docs)

    print("✅ Week 7 Recover / Resilience seed data inserted.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    db = get_db()
    print(f"Using DB: {DB_NAME} at {MONGO_URI}")
    ensure_recover_indexes(db)
    seed_recover_data(db)
    print("✅ Week 7 Recover / Resilience setup complete.")
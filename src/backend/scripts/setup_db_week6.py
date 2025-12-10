#!/usr/bin/env python3
"""
MongoDB setup + seed script for Week 6 Respond / Incident feature.

- Connects to MongoDB using:
    MONGO_URI (default: mongodb://localhost:27017)
    DB_NAME   (default: smbsec)
- Ensures collections:
    incidents
    incident_tasks
    incident_timeline
    incident_evidence
- Seeds some sample data if incidents collection is empty.
"""

import os
from datetime import datetime, timedelta

from pymongo import MongoClient, ASCENDING
from bson import ObjectId

# -------- Env & Basic Config --------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "smbsec")


def ensure_respond_collections(db):
    """
    Create collections + indexes for Week 6 Respond / Incident feature.
    """

    incidents = db["incidents"]
    incident_tasks = db["incident_tasks"]
    incident_timeline = db["incident_timeline"]
    incident_evidence = db["incident_evidence"]

    # ---- incidents ----
    incidents.create_index([("severity", ASCENDING), ("status", ASCENDING)])
    incidents.create_index([("sla_due_at", ASCENDING)])
    incidents.create_index([
        ("dedup_key.asset_id", ASCENDING),
        ("dedup_key.indicator", ASCENDING),
        ("dedup_key.source", ASCENDING),
    ])

    # ---- incident_tasks ----
    incident_tasks.create_index([
        ("incident_id", ASCENDING),
        ("order", ASCENDING),
    ])
    incident_tasks.create_index([
        ("incident_id", ASCENDING),
        ("phase", ASCENDING),
    ])

    # ---- incident_timeline ----
    incident_timeline.create_index([
        ("incident_id", ASCENDING),
        ("ts", ASCENDING),
    ])

    # ---- incident_evidence ----
    incident_evidence.create_index([
        ("incident_id", ASCENDING),
    ])

    print("[OK] Respond / Incident collections and indexes ensured.")


def seed_respond_sample_data(db):
    """
    Seed a few sample incidents + related docs.
    Only runs if incidents collection is empty.
    """
    incidents = db["incidents"]
    incident_tasks = db["incident_tasks"]
    incident_timeline = db["incident_timeline"]
    incident_evidence = db["incident_evidence"]

    if incidents.count_documents({}) > 0:
        print("[SKIP] incidents collection already has data; not seeding.")
        return

    now = datetime.utcnow()

    # -------- Sample Incident 1: P1 Ransomware on web-01 --------
    inc1_id = ObjectId()
    inc1_opened = now - timedelta(hours=1)
    inc1_sla_due = inc1_opened + timedelta(hours=4)

    inc1 = {
        "_id": inc1_id,
        "title": "Ransomware activity detected on web-01",
        "severity": "P1",
        "status": "Containment",
        "opened_at": inc1_opened,
        "updated_at": now,
        "closed_at": None,
        "owner": "alice",
        "sla_due_at": inc1_sla_due,
        "sla_status": "ok",
        "primary_asset_id": "68e2ff2bebc14d7e0eba50ec",
        "detection_refs": [ObjectId()],
        "risk_item_refs": [],
        "summary": "Possible ransomware encryption observed on web-01. User files rapidly modified.",
        "root_cause": "",
        "lessons_learned": "",
        "tags": ["ransomware", "endpoint"],
        "dedup_key": {
            "asset_id": "68e2ff2bebc14d7e0eba50ec",
            "indicator": "10.0.0.5",
            "source": "siem",
            "window_start": inc1_opened,
        },
    }

    # Tasks for incident 1
    inc1_tasks = [
        {
            "_id": ObjectId(),
            "incident_id": inc1_id,
            "phase": "Triage",
            "title": "Confirm scope of ransomware on web-01",
            "assignee": "alice",
            "due_at": inc1_opened + timedelta(hours=1),
            "status": "Done",
            "notes": "Auto-generated task",
            "order": 1,
            "created_at": inc1_opened,
            "updated_at": now,
        },
        {
            "_id": ObjectId(),
            "incident_id": inc1_id,
            "phase": "Containment",
            "title": "Isolate web-01 from network",
            "assignee": "bob",
            "due_at": inc1_opened + timedelta(hours=2),
            "status": "Open",
            "notes": "Auto-generated task",
            "order": 2,
            "created_at": inc1_opened,
            "updated_at": now,
        },
        {
            "_id": ObjectId(),
            "incident_id": inc1_id,
            "phase": "Eradication",
            "title": "Remove malicious binaries and scheduled tasks",
            "assignee": None,
            "due_at": inc1_opened + timedelta(hours=3),
            "status": "Open",
            "notes": "Auto-generated task",
            "order": 3,
            "created_at": inc1_opened,
            "updated_at": now,
        },
    ]

    # Timeline for incident 1
    inc1_timeline = [
        {
            "_id": ObjectId(),
            "incident_id": inc1_id,
            "ts": inc1_opened,
            "actor": "system",
            "event_type": "opened",
            "detail": {
                "note": "Incident auto-opened from ransomware detection",
            },
        },
        {
            "_id": ObjectId(),
            "incident_id": inc1_id,
            "ts": inc1_opened + timedelta(minutes=15),
            "actor": "user:alice",
            "event_type": "status_change",
            "detail": {
                "from": "Open",
                "to": "Triage",
            },
        },
        {
            "_id": ObjectId(),
            "incident_id": inc1_id,
            "ts": inc1_opened + timedelta(minutes=45),
            "actor": "user:alice",
            "event_type": "status_change",
            "detail": {
                "from": "Triage",
                "to": "Containment",
            },
        },
        {
            "_id": ObjectId(),
            "incident_id": inc1_id,
            "ts": inc1_opened + timedelta(minutes=50),
            "actor": "user:alice",
            "event_type": "note",
            "detail": {
                "message": "Confirmed encryption activity and suspicious process tree on web-01.",
            },
        },
    ]

    # Evidence for incident 1
    inc1_evidence = [
        {
            "_id": ObjectId(),
            "incident_id": inc1_id,
            "asset_id": "68e2ff2bebc14d7e0eba50ec",
            "detection_id": inc1["detection_refs"][0],
            "type": "log",
            "location": "s3://ir-bucket/inc-001/web-01/sysmon-logs.json",
            "hash": "deadbeef1234",
            "submitted_by": "alice",
            "submitted_at": inc1_opened + timedelta(minutes=20),
            "chain_of_custody": [
                {
                    "who": "alice",
                    "when": (inc1_opened + timedelta(minutes=20)).isoformat(),
                    "action": "uploaded",
                }
            ],
        }
    ]

    # -------- Sample Incident 2: P3 Suspicious login --------
    inc2_id = ObjectId()
    inc2_opened = now - timedelta(days=1)
    inc2_sla_due = inc2_opened + timedelta(hours=24)

    inc2 = {
        "_id": inc2_id,
        "title": "Suspicious login from unusual country for CFO account",
        "severity": "P3",
        "status": "Recovery",
        "opened_at": inc2_opened,
        "updated_at": now,
        "closed_at": None,
        "owner": "carol",
        "sla_due_at": inc2_sla_due,
        "sla_status": "ok",
        "primary_asset_id": "68e2ff2bebc14d7e0eba50ef",
        "detection_refs": [ObjectId()],
        "risk_item_refs": [],
        "summary": "Multiple login attempts to CFO account from foreign IP range.",
        "root_cause": "",
        "lessons_learned": "",
        "tags": ["account-compromise", "identity"],
        "dedup_key": {
            "asset_id": "68e2ff2bebc14d7e0eba50ef",
            "indicator": "203.0.113.10",
            "source": "idp",
            "window_start": inc2_opened,
        },
    }

    inc2_tasks = [
        {
            "_id": ObjectId(),
            "incident_id": inc2_id,
            "phase": "Triage",
            "title": "Confirm whether CFO login attempts are legitimate",
            "assignee": "carol",
            "due_at": inc2_opened + timedelta(hours=2),
            "status": "Done",
            "notes": "CFO confirmed no travel.",
            "order": 1,
            "created_at": inc2_opened,
            "updated_at": inc2_opened + timedelta(hours=2),
        },
        {
            "_id": ObjectId(),
            "incident_id": inc2_id,
            "phase": "Containment",
            "title": "Force password reset and revoke active sessions",
            "assignee": "carol",
            "due_at": inc2_opened + timedelta(hours=4),
            "status": "Done",
            "notes": "",
            "order": 2,
            "created_at": inc2_opened,
            "updated_at": inc2_opened + timedelta(hours=4),
        },
        {
            "_id": ObjectId(),
            "incident_id": inc2_id,
            "phase": "Recovery",
            "title": "Monitor for repeated login attempts and update geo rules",
            "assignee": "secops-bot",
            "due_at": inc2_opened + timedelta(hours=12),
            "status": "Open",
            "notes": "",
            "order": 3,
            "created_at": inc2_opened,
            "updated_at": now,
        },
    ]

    inc2_timeline = [
        {
            "_id": ObjectId(),
            "incident_id": inc2_id,
            "ts": inc2_opened,
            "actor": "system",
            "event_type": "opened",
            "detail": {
                "note": "Incident auto-opened from IdP anomalous login detection",
            },
        },
        {
            "_id": ObjectId(),
            "incident_id": inc2_id,
            "ts": inc2_opened + timedelta(hours=1),
            "actor": "user:carol",
            "event_type": "comms",
            "detail": {
                "channel": "email",
                "recipient": "cfo@example.com",
                "subject": "Suspicious login to your account",
            },
        },
    ]

    inc2_evidence = [
        {
            "_id": ObjectId(),
            "incident_id": inc2_id,
            "asset_id": "68e2ff2bebc14d7e0eba50ef",
            "detection_id": inc2["detection_refs"][0],
            "type": "screenshot",
            "location": "s3://ir-bucket/inc-002/idp-screenshot.png",
            "hash": None,
            "submitted_by": "carol",
            "submitted_at": inc2_opened + timedelta(hours=1, minutes=30),
            "chain_of_custody": [
                {
                    "who": "carol",
                    "when": (inc2_opened + timedelta(hours=1, minutes=30)).isoformat(),
                    "action": "uploaded",
                }
            ],
        }
    ]

    # ---- Insert all docs ----
    incidents.insert_many([inc1, inc2])
    incident_tasks.insert_many(inc1_tasks + inc2_tasks)
    incident_timeline.insert_many(inc1_timeline + inc2_timeline)
    incident_evidence.insert_many(inc1_evidence + inc2_evidence)

    print("[OK] Seeded sample incidents, tasks, timeline, and evidence.")


def main():
    print(f"Connecting to MongoDB at {MONGO_URI}, DB={DB_NAME} ...")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    ensure_respond_collections(db)
    seed_respond_sample_data(db)

    print("[DONE] Database setup + seed complete.")


if __name__ == "__main__":
    main()
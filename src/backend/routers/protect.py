# from fastapi import APIRouter
# router = APIRouter(prefix="/api/protect", tags=["protect"])

# @router.get("/ping")
# def ping_protect():
#     return {"area": "protect", "ok": True}

import os
import pathlib
from pymongo import MongoClient
from fastapi import APIRouter, Request
from services.protect.policy_builder import run_policy_builder
from db.mongo import db
from scripts.week5_1 import (
    _read_json,
    discover_indexes,
    create_collection_if_missing,
    ensure_indexes,
    seed_controls,
    seed_control_mappings,
    seed_policies,
    seed_policy_assignments,
    seed_control_evidence,
)

router = APIRouter(prefix="/api/protect", tags=["protect"])

@router.post("/run")
async def protect_run():
    summary = await run_policy_builder(db)
    return summary

@router.post("/create")
async def create_table():
    """
    Initialize MongoDB collections and seed data (NO validators).
    This mirrors scripts/week5_1.py:main(), but is exposed as an API route.
    """
    # Env + paths (keep in sync with week5_1.py)
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DB_NAME", "smbsec")
    SCHEMA_DIR = pathlib.Path(os.getenv("SCHEMA_DIR", "scripts/schemas")).resolve()
    SEED_DIR = pathlib.Path(os.getenv("SEED_DIR", "seed")).resolve()

    # Connect to Mongo
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    print(f"Connecting to: {MONGO_URI}  DB: {DB_NAME}")
    print(f"Schemas dir:  {SCHEMA_DIR}")
    print(f"Seeds dir:    {SEED_DIR}")

    # 1) Discover & ensure indexes (also tells us which collections to create)
    idx_map = discover_indexes(SCHEMA_DIR)

    # union of collections from indexes plus known seed targets
    known_seed_colls = {
        "controls",
        "control_mappings",
        "policies",
        "policy_assignments",
        "control_evidence",
    }
    all_colls = sorted(set(idx_map.keys()) | known_seed_colls)

    # 2) Create collections (NO validators)
    for coll in all_colls:
        create_collection_if_missing(db, coll)

    # 3) Apply indexes
    for coll, specs in idx_map.items():
        ensure_indexes(db, coll, specs)

    # 4) Seeds (optional if files exist)
    controls_seed = _read_json(SEED_DIR / "controls.seed.json")
    if controls_seed:
        seed_controls(db, controls_seed)
    else:
        print("[INFO] No seed/controls.seed.json found; skipping.")

    mappings_seed = _read_json(SEED_DIR / "control_mappings.seed.json")
    if mappings_seed:
        seed_control_mappings(db, mappings_seed)
    else:
        print("[INFO] No seed/control_mappings.seed.json found; skipping.")

    policies_seed = _read_json(SEED_DIR / "policies.seed.json")
    if policies_seed:
        seed_policies(db, policies_seed)
    else:
        print("[INFO] No seed/policies.seed.json found; skipping.")

    assignments_seed = _read_json(SEED_DIR / "policy_assignments.seed.json")
    if assignments_seed:
        seed_policy_assignments(db, assignments_seed)
    else:
        print("[INFO] No seed/policy_assignments.seed.json found; skipping.")

    evidence_seed = _read_json(SEED_DIR / "control_evidence.seed.json")
    if evidence_seed:
        seed_control_evidence(db, evidence_seed)
    else:
        print("[INFO] No seed/control_evidence.seed.json found; skipping.")

    print("[DONE] Database setup complete (no validators).")

    return {
        "status": "ok",
        "message": "Database setup complete (no validators).",
        "db": DB_NAME,
        "collections_created": all_colls,
    }

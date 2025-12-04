#!/usr/bin/env python3
"""
MongoDB setup helpers (NO validators).

Provides reusable functions for:
- Creating collections if missing (no JSON Schema validators)
- Dropping & recreating collections if they already exist
- Ensuring indexes from scripts/schemas/indexes.json and any *.indexes.json
- Seeding documents from seed/*.json (Extended JSON supported)

Env (defaults):
  MONGO_URI=mongodb://localhost:27017
  DB_NAME=smbsec
  SCHEMA_DIR=scripts/schemas
  SEED_DIR=seed
"""

import os
import pathlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import CollectionInvalid, DuplicateKeyError
from bson import json_util
from bson.objectid import ObjectId


BASE_DIR = pathlib.Path(__file__).resolve().parent.parent  # backend/

SCHEMA_DIR = pathlib.Path(os.getenv(
    "SCHEMA_DIR",
    BASE_DIR / "scripts" / "schemas"
)).resolve()

SEED_DIR = pathlib.Path(os.getenv(
    "SEED_DIR",
    BASE_DIR / "seed"
)).resolve()

# -------- Env & Paths --------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "smbsec")


def get_db():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]


# -------- Utils --------
def _read_json(path: pathlib.Path):
    if not path.exists():
        return None
    return json_util.loads(path.read_text(encoding="utf-8"))


def _index_spec_to_tuple(keys_obj: Dict[str, int]):
    out = []
    for k, v in keys_obj.items():
        out.append((k, ASCENDING if int(v) >= 0 else DESCENDING))
    return out


def _ensure_datetime_fields(doc: Dict[str, Any], *fields: str, default_dt: Optional[datetime] = None):
    dt = default_dt or datetime.utcnow()
    for f in fields:
        doc.setdefault(f, dt)


# -------- Collections & Indexes (no validators) --------
def create_collection_if_missing(db, name: str) -> None:
    """Create a collection if it does not exist."""
    if name in db.list_collection_names():
        print(f"[OK] Collection exists: {name}")
        return
    try:
        db.create_collection(name)
        print(f"[OK] Created collection: {name}")
    except CollectionInvalid as e:
        print(f"[WARN] {name}: {e}")


def discover_indexes(schema_dir: pathlib.Path) -> Dict[str, List[Dict[str, Any]]]:
    idx_map: Dict[str, List[Dict[str, Any]]] = {}

    # global indexes.json
    global_idx = _read_json(schema_dir / "indexes.json") or {}
    for coll, lst in global_idx.items():
        if isinstance(lst, list):
            idx_map[coll] = list(lst)

    # per-collection *.indexes.json
    for p in schema_dir.glob("*.indexes.json"):
        coll = p.name.replace(".indexes.json", "")
        data = _read_json(p) or []
        if isinstance(data, list):
            idx_map.setdefault(coll, []).extend(data)

    return idx_map


def ensure_indexes(db, coll_name: str, specs: List[Dict[str, Any]]) -> None:
    if not specs:
        return

    for item in specs:
        keys = item.get("keys", {})
        options = item.get("options", {})
        if not keys:
            continue
        db[coll_name].create_index(_index_spec_to_tuple(keys), **options)

    print(f"[OK] Indexes ensured for: {coll_name}")


# -------- Seeding Functions --------
def seed_controls(db, payload: List[Dict[str, Any]]) -> None:
    now = datetime.utcnow()
    upserted = 0
    for c in payload:
        _ensure_datetime_fields(c, "created_at", "updated_at", default_dt=now)
        c.setdefault("implementation_status", "Proposed")

        res = db.controls.update_one(
            {"control_id": c["control_id"]},
            {"$setOnInsert": c},
            upsert=True,
        )
        if res.upserted_id is not None:
            upserted += 1

    print(f"[OK] Seed controls: upserted={upserted}, total_payload={len(payload)}")


def seed_control_mappings(db, payload: List[Dict[str, Any]]) -> None:
    now = datetime.utcnow()
    upserted = 0
    for m in payload:
        _ensure_datetime_fields(m, "created_at", "updated_at", default_dt=now)
        res = db.control_mappings.update_one(
            {"control_id": m.get("control_id"), "csf_ref": m.get("csf_ref")},
            {"$setOnInsert": m},
            upsert=True,
        )
        if res.upserted_id is not None:
            upserted += 1
    print(f"[OK] Seed control_mappings: upserted={upserted}, total_payload={len(payload)}")


def seed_policies(db, payload: List[Dict[str, Any]]) -> None:
    now = datetime.utcnow()
    upserted = 0
    for p in payload:
        _ensure_datetime_fields(p, "created_at", "updated_at", default_dt=now)
        res = db.policies.update_one(
            {"name": p.get("name"), "version": p.get("version")},
            {"$setOnInsert": p},
            upsert=True,
        )
        if res.upserted_id is not None:
            upserted += 1
    print(f"[OK] Seed policies: upserted={upserted}, total_payload={len(payload)}")


def seed_policy_assignments(db, payload: List[Dict[str, Any]]) -> None:
    now = datetime.utcnow()
    upserted = 0
    for pa in payload:
        _ensure_datetime_fields(pa, "created_at", "updated_at", default_dt=now)

        if "asset_id" in pa and isinstance(pa["asset_id"], str):
            try:
                pa["asset_id"] = ObjectId(pa["asset_id"])
            except Exception:
                pass

        res = db.policy_assignments.update_one(
            {"asset_id": pa.get("asset_id"), "control_id": pa.get("control_id")},
            {"$setOnInsert": pa},
            upsert=True,
        )
        if res.upserted_id is not None:
            upserted += 1

    print(f"[OK] Seed policy_assignments: upserted={upserted}, total_payload={len(payload)}")


def seed_control_evidence(db, payload: List[Dict[str, Any]]) -> None:
    now = datetime.utcnow()
    inserted_or_upserted = 0
    for ev in payload:
        _ensure_datetime_fields(ev, "created_at", default_dt=now)

        if "asset_id" in ev and isinstance(ev["asset_id"], str):
            try:
                ev["asset_id"] = ObjectId(ev["asset_id"])
            except Exception:
                pass

        key = {
            "control_id": ev.get("control_id"),
            "asset_id": ev.get("asset_id"),
            "evidence_type": ev.get("evidence_type"),
            "location": ev.get("location"),
            "submitted_at": ev.get("submitted_at"),
        }
        try:
            db.control_evidence.update_one(key, {"$setOnInsert": ev}, upsert=True)
            inserted_or_upserted += 1
        except DuplicateKeyError:
            pass

    print(
        f"[OK] Seed control_evidence: upserted_or_matched≈{inserted_or_upserted}, total_payload={len(payload)}"
    )


# -------- Main (Drop & Recreate Collections) --------
def main() -> None:
    db = get_db()

    print(f"Connecting to: {MONGO_URI}  DB: {DB_NAME}")
    print(f"Schemas dir:  {SCHEMA_DIR}")
    print(f"Seeds dir:    {SEED_DIR}")

    # Discover index specs
    idx_map = discover_indexes(SCHEMA_DIR)

    known_seed_colls = {
        "controls",
        "control_mappings",
        "policies",
        "policy_assignments",
        "control_evidence",
    }

    all_colls = sorted(set(idx_map.keys()) | known_seed_colls)

    # -------- ⭐ DROP & RECREATE COLLECTIONS --------
    for coll in all_colls:
        if coll in db.list_collection_names():
            print(f"[WARN] Dropping existing collection: {coll}")
            db.drop_collection(coll)

        create_collection_if_missing(db, coll)

    # -------- Apply Indexes --------
    for coll, specs in idx_map.items():
        ensure_indexes(db, coll, specs)

    # -------- Seed Data --------
    controls_seed = _read_json(SEED_DIR / "controls.seed.json")
    if controls_seed:
        seed_controls(db, controls_seed)

    mappings_seed = _read_json(SEED_DIR / "control_mappings.seed.json")
    if mappings_seed:
        seed_control_mappings(db, mappings_seed)

    policies_seed = _read_json(SEED_DIR / "policies.seed.json")
    if policies_seed:
        seed_policies(db, policies_seed)

    assignments_seed = _read_json(SEED_DIR / "policy_assignments.seed.json")
    if assignments_seed:
        seed_policy_assignments(db, assignments_seed)

    evidence_seed = _read_json(SEED_DIR / "control_evidence.seed.json")
    if evidence_seed:
        seed_control_evidence(db, evidence_seed)

    print("[DONE] Database setup complete (collections dropped & recreated).")


if __name__ == "__main__":
    main()

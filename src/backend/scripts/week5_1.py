#!/usr/bin/env python3
"""
MongoDB setup helpers (NO validators).

Provides reusable functions for:
- Creating collections if missing (no JSON Schema validators)
- Ensuring indexes from scripts/schemas/indexes.json and any *.indexes.json
- Seeding documents from seed/*.json (Extended JSON supported)

Env (defaults):
  MONGO_URI=mongodb://localhost:27017
  DB_NAME=smbsec
  SCHEMA_DIR=scripts/schemas
  SEED_DIR=seed

Can be used in two ways:
  1) As a library from FastAPI (week 5.1 assignment)
  2) As a standalone script:
       python scripts/week5_1.py
"""

import os
import pathlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import CollectionInvalid, DuplicateKeyError
from bson import json_util
from bson.objectid import ObjectId

# -------- Env & Paths --------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "smbsec")
SCHEMA_DIR = pathlib.Path(os.getenv("SCHEMA_DIR", "scripts/schemas")).resolve()
SEED_DIR = pathlib.Path(os.getenv("SEED_DIR", "seed")).resolve()


def get_db():
    """Return a new DB handle using env-configured URI and DB name."""
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]


# -------- Utils --------
def _read_json(path: pathlib.Path):
    """Read JSON using bson.json_util to support Extended JSON ($oid/$date)."""
    if not path.exists():
        return None
    return json_util.loads(path.read_text(encoding="utf-8"))


def _index_spec_to_tuple(keys_obj: Dict[str, int]):
    # {"a":1,"b":-1} -> [("a", ASCENDING), ("b", DESCENDING)]
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
    """
    Create a collection if it does not exist.
    NO VALIDATORS are applied here, just an empty collection.
    """
    if name in db.list_collection_names():
        print(f"[OK] Collection exists: {name}")
        return
    try:
        db.create_collection(name)
        print(f"[OK] Created collection: {name}")
    except CollectionInvalid as e:
        print(f"[WARN] {name}: {e}")


def discover_indexes(schema_dir: pathlib.Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load indexes from:
      - indexes.json (global)
      - *.indexes.json (per-collection)
    Format:
      {
        "collection_name": [
          {
            "keys": {"field": 1, "field2": -1},
            "options": {"unique": true, "name": "idx_name"}
          },
          ...
        ],
        ...
      }
    """
    idx_map: Dict[str, List[Dict[str, Any]]] = {}

    # Global indexes.json (optional)
    global_idx = _read_json(schema_dir / "indexes.json") or {}
    for coll, lst in global_idx.items():
        if isinstance(lst, list):
            idx_map[coll] = list(lst)

    # Per-collection *.indexes.json
    for p in schema_dir.glob("*.indexes.json"):
        coll = p.name.replace(".indexes.json", "")
        data = _read_json(p) or []
        if isinstance(data, list):
            idx_map.setdefault(coll, []).extend(data)

    return idx_map


def ensure_indexes(db, coll_name: str, specs: List[Dict[str, Any]]) -> None:
    """
    Ensure the given index specs exist on the collection.
    Specs come from discover_indexes().
    """
    if not specs:
        return

    for item in specs:
        keys = item.get("keys", {})
        options = item.get("options", {})
        if not keys:
            continue
        db[coll_name].create_index(_index_spec_to_tuple(keys), **options)

    print(f"[OK] Indexes ensured for: {coll_name}")


# -------- Seeding (idempotent upserts) --------
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

        # coerce asset_id to ObjectId if string
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
            # If there's a unique index and we hit an existing doc, just ignore.
            pass

    print(
        f"[OK] Seed control_evidence: upserted_or_matched≈{inserted_or_upserted}, "
        f"total_payload={len(payload)}"
    )


# -------- Main (standalone script) --------
def main() -> None:
    db = get_db()

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

    # 2) Create collections (no validators)
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


if __name__ == "__main__":
    main()

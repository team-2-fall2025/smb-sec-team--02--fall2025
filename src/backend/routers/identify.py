# routers/identify.py
from datetime import datetime, timedelta
import re
from fastapi import APIRouter
from bson import ObjectId
from db.mongo import db

router = APIRouter(prefix="/api/identify", tags=["identify"])

@router.get("/ping")
async def ping(): return {"ok": True, "area": "identify"}

# ------- Heuristics -------
_DB_PAT = re.compile(r"\b(db|mysql|postgres|mongo|mariadb|oracle)\b", re.I)
_WEB_PAT = re.compile(r"\b(web|svc|api|gw|gateway|nginx|apache)\b", re.I)
def _infer_type(name: str | None) -> str:
    n = (name or "").lower()
    if _DB_PAT.search(n): return "HW"
    if _WEB_PAT.search(n): return "Service"
    return "SW"
def _crit_from_sens(s: str | None) -> int:
    s = (s or "Low").lower()
    return 5 if s == "high" else 3 if s.startswith("mod") else 2
def _norm(h: str | None) -> str:
    return (h or "").strip().lower().rstrip(".")

async def _classify_and_link():
    assets = db["assets"]; intel = db["intel_events"]; links = db["asset_intel_links"]; audits = db["audit_logs"]
    now = datetime.utcnow(); since = now - timedelta(days=14)
    classified = 0; linked = 0

    # (1) Enrich missing fields
    async for a in assets.find({"deleted_at": {"$exists": False}}):
        patch = {}
        if not a.get("type"): patch["type"] = _infer_type(a.get("name"))
        if not a.get("criticality"): patch["criticality"] = _crit_from_sens(a.get("data_sensitivity"))
        if patch:
            patch["updated_at"] = now
            await assets.update_one({"_id": a["_id"]}, {"$set": patch})
            await audits.insert_one({
                "at": now, "actor": "identify_agent",
                "entity": "asset", "entity_id": a["_id"],
                "changes": [{"field": k, "old": a.get(k), "new": v} for k, v in patch.items()]
            })
            print(patch)
            classified += 1

    # (2a) Link by IP
    async for ie in intel.find({"created_at": {"$gte": since}, "indicator_type": "ip"}):
        print(ie)
        async for a in assets.find({"ip": ie.get("indicator"), "deleted_at": {"$exists": False}}):
            res = await links.update_one(
                {"asset_id": a["_id"], "intel_id": ie["_id"]},
                {"$setOnInsert": {"asset_id": a["_id"], "intel_id": ie["_id"], "match_type": "ip", "created_at": now}},
                upsert=True
            )
            if res.upserted_id is not None: linked += 1

    # (2b) Link by hostname / domain
    async for ie in intel.find({"created_at": {"$gte": since}, "indicator_type": {"$in": ["hostname", "domain"]}}):
        dom = _norm(ie.get("indicator"))
        async for a in assets.find({"hostname": {"$exists": True}, "deleted_at": {"$exists": False}}):
            h = _norm(a.get("hostname"))
            if not h: continuea
            is_match = (h == dom) if ie["indicator_type"] == "hostname" else (h == dom or h.endswith("." + dom))
            if is_match:
                res = await links.update_one(
                    {"asset_id": a["_id"], "intel_id": ie["_id"]},
                    {"$setOnInsert": {"asset_id": a["_id"], "intel_id": ie["_id"], "match_type": "hostname", "created_at": now}},
                    upsert=True
                )
                if res.upserted_id is not None: linked += 1

    return {"classified": classified, "linked": linked}

@router.post("/run")
async def run_identify():
    result = await _classify_and_link()
    print(result)
    return {"ok": True, **result}

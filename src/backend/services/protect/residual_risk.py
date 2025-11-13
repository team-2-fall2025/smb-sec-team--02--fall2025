from typing import Dict, Any, List
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId

def _clamp(x, lo=0.0, hi=1.0): return max(lo, min(hi, x))

async def _effectiveness_for_asset(db, asset_id: ObjectId, weights: Dict[str, float]) -> float:
    eff = 0.0
    async for pa in db.policy_assignments.find({"asset_id": asset_id}):
        eff += float(weights.get(pa.get("status","Proposed"), 0.0))
        if eff >= 0.8:
            return 0.8
    return _clamp(eff, 0.0, 0.8)

async def update_residual_risk_for_assets(db, weights: Dict[str, float]) -> int:
    """
    inherent_risk = criticality × max_intel_severity_last_7d (assumes pre-computed on asset or risk item)
    residual_risk = round(inherent_risk * (1 - min(0.8, sum(effectiveness))))
    Also: mark risk item "Mitigation In-Progress" if residual <= 5
    """
    updated_risk_items = 0
    now = datetime.utcnow()

    # Load assets (assume fields: criticality [1..5], intel_max_sev_7d [0..5])
    assets = [a async for a in db.assets.find({})]
    for a in assets:
        aid = a.get("_id")
        if isinstance(aid, str):
            try:
                aid = ObjectId(aid)
            except InvalidId:
                # Previous logic skipped this asset on invalid ObjectId
                continue
        crit = int(a.get("criticality", 1))
        sev = int(a.get("intel_max_sev_7d", 0))
        inherent = crit * sev

        eff = await _effectiveness_for_asset(db, aid, weights)
        residual = int(round(inherent * (1.0 - eff)))

        # persist residual on asset
        await db.assets.update_one({"_id": aid}, {"$set": {"residual_risk": residual, "residual_updated_at": now}})

        # update linked risk_items (very simple MVP: any open item for this asset)
        async for r in db.risk_items.find({"asset_id": aid, "status": {"$in": ["Open","Mitigation Recommended","In-Progress"]}}):
            new_status = "In-Progress" if residual <= 5 else r.get("status", "Open")
            upd = {"residual_risk": residual, "updated_at": now}
            if new_status != r.get("status"):
                upd["status"] = new_status
            res = await db.risk_items.update_one({"_id": r["_id"]}, {"$set": upd})
            if res.modified_count:
                updated_risk_items += 1

    return updated_risk_items

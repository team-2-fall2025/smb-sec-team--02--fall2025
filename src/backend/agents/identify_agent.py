
from db.mongo import db
from datetime import datetime


async def generate_asset_intel_links():
    """
    Efficiently link assets ↔ intel_events using MongoDB aggregation
    based on matching IP or hostname (depending on indicator_type).
    """

    # ---- 1) Match IP-based intel ----
    ip_matches = db["intel_events"].aggregate([
        {"$match": {"indicator_type": "ip"}},
        {"$lookup": {
            "from": "assets",
            "localField": "indicator",
            "foreignField": "ip",
            "as": "matched_assets"
        }},
        {"$unwind": "$matched_assets"},
        {"$project": {
            "intel_id": "$_id",
            "asset_id": "$matched_assets._id",
            "asset_name": "$matched_assets.name",
            "intel_indicator": "$indicator",
            "match_type": {"$literal": "ip"}
        }}
    ])

    # ---- 2) Match hostname-based intel ----
    host_matches = db["intel_events"].aggregate([
        {"$match": {"indicator_type": {"$in": ["hostname", "domain"]}}},
        {"$lookup": {
            "from": "assets",
            "localField": "indicator",
            "foreignField": "hostname",
            "as": "matched_assets"
        }},
        {"$unwind": "$matched_assets"},
        {"$project": {
            "intel_id": "$_id",
            "asset_id": "$matched_assets._id",
            "asset_name": "$matched_assets.name",
            "intel_indicator": "$indicator",
            "match_type": {"$literal": "hostname"}
        }}
    ])

    # ---- 3) Insert combined results into bridge table ----
    inserted = 0

    async for match in ip_matches:
        await db["asset_intel_links"].update_one(
            {"asset_id": match["asset_id"], "intel_id": match["intel_id"]},
            {"$setOnInsert": {
                **match,
                "created_at": datetime.utcnow(),
            }},
            upsert=True
        )
        inserted += 1

    async for match in host_matches:
        await db["asset_intel_links"].update_one(
            {"asset_id": match["asset_id"], "intel_id": match["intel_id"]},
            {"$setOnInsert": {
                **match,
                "created_at": datetime.utcnow(),
            }},
            upsert=True
        )
        inserted += 1

    return {"message": f"Linked {inserted} asset↔intel pairs", "inserted": inserted}
    
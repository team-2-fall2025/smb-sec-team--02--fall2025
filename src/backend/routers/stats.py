# src/backend/routers/stats.py
from fastapi import APIRouter
from db.mongo import db

router = APIRouter()

@router.get("/stats")
async def stats():
    """返回数据库中 assets、intel_events、risk_items 三个集合的数量。"""
    async def safe_count(collection_name: str) -> int:
        try:
            return await db[collection_name].count_documents({})
        except Exception:
            # 集合不存在或计数失败时返回 0
            return 0

    assets = await safe_count("assets")
    intel_events = await safe_count("intel_events")
    # risk_items = await safe_count("risk_items")
    risk_items = await safe_count("risk_register")

    return {
        "assets": assets,
        "intel_events": intel_events,
        "risk_items": risk_items
    }

# routes/intel.py
@router.get("/events")
async def list_intel_events():
    events = await db.intel_events.find().sort("created_at", -1).to_list(length=None)
    for e in events:
        e["_id"] = str(e["_id"])
        e["asset_id"] = str(e["asset_id"])
        e["created_at"] = e["created_at"]
    return events
# src/backend/routers/stats.py
from fastapi import APIRouter
from backend.db.mongo import db

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

from fastapi import APIRouter
from src.backend.db.mongo import db

router = APIRouter()

@router.get("/stats")
async def stats():
    assets = await db.assets.count_documents({})
    intel_events = await db.intel_events.count_documents({})
    risk_items = await db.risk_items.count_documents({})
    return {
        "assets": assets,
        "intel_events": intel_events,
        "risk_items": risk_items
    }



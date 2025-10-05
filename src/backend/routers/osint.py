from fastapi import APIRouter
from db.mongo import db

router = APIRouter()

@router.post("/osint/test")
async def osint_test():
    sample = {
        "source": "otx",
        "indicator": "8.8.8.8",
        "raw": {"ok": True},
        "severity": 2
    }
    await db.intel_events.insert_one(sample)
    return {"inserted": 1}

@router.get("/osint/test")
async def osint_test_get():
    sample = {
        "source": "otx",
        "indicator": "8.8.8.8",
        "raw": {"ok": True},
        "severity": 2
    }
    await db.intel_events.insert_one(sample)
    return {"inserted": 1}

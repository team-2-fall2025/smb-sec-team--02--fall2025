from fastapi import APIRouter
router = APIRouter(prefix="/api/govern", tags=["detect"])

@router.get("/ping")
def ping_detect():
    return {"area": "detect", "ok": True}
from fastapi import APIRouter
router = APIRouter(prefix="/api/respond", tags=["respond"])

@router.get("/ping")
def ping_respond():
    return {"area": "respond", "ok": True}

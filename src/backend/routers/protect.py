from fastapi import APIRouter
router = APIRouter(prefix="/api/protect", tags=["protect"])

@router.get("/ping")
def ping_protect():
    return {"area": "protect", "ok": True}

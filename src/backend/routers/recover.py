from fastapi import APIRouter
router = APIRouter(prefix="/api/recover", tags=["recover"])

@router.get("/ping")
def ping_recover():
    return {"area": "recover", "ok": True}

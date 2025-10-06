from fastapi import APIRouter

router = APIRouter(prefix="/api/identify", tags=["identify"])

@router.get("/ping")
def ping_identify():
    return {"area": "identify", "ok": True}

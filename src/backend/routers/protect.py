# from fastapi import APIRouter
# router = APIRouter(prefix="/api/protect", tags=["protect"])

# @router.get("/ping")
# def ping_protect():
#     return {"area": "protect", "ok": True}


from fastapi import APIRouter, Request
from services.protect.policy_builder import run_policy_builder
from db.mongo import db

router = APIRouter(prefix="/api/protect", tags=["protect"])

@router.post("/run")
async def protect_run():
    summary = await run_policy_builder(db)
    return summary
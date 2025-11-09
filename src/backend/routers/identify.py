# routers/identify.py
from fastapi import APIRouter
from agents.identify_agent import generate_asset_intel_links, infere_asset_fields

router = APIRouter(prefix="/api/identify", tags=["identify"])


@router.get("/ping")
async def ping():
    return {"ok": True, "area": "identify"}


@router.post("/run")
async def run_identify():
    classified_count = await infere_asset_fields()
    linked_count = await generate_asset_intel_links()
    print(" Identify agent run complete.")
    result = {
        "classified_count": classified_count,
        "linked_count": linked_count,
    }

    return {"ok": True, **result}

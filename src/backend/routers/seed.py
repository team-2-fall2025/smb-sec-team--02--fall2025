from fastapi import APIRouter
from agents.identify_agent import generate_asset_intel_links
from db.seed_from_csv import main as seed_main

router = APIRouter()

@router.get("/db/seed")
@router.post("/db/seed")
async def run_seed():
    try:
        await seed_main()
        await generate_asset_intel_links()
        return {"status": "ok", "message": "Data imported successfully from CSV files."}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

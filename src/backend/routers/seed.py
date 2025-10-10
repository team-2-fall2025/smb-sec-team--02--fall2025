from fastapi import APIRouter
from ..db.seed_from_csv import main as seed_main

router = APIRouter()

@router.get("/db/seed")
@router.post("/db/seed")
async def run_seed():
    try:
        await seed_main()
        return {"status": "ok", "message": "Data imported successfully from CSV files."}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

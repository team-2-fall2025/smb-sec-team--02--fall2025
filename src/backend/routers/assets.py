from datetime import datetime, timedelta
import csv
import io
import json

from bson import ObjectId
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.params import Body
from pydantic import BaseModel
from db.mongo import db


router = APIRouter(prefix="/assets", tags=["assets"])


# ---------------------------
# 工具函数
# ---------------------------
def serialize_asset(asset: dict) -> dict:
    """Convert Mongo _id to string safely"""
    if asset and "_id" in asset:
        asset["_id"] = str(asset["_id"])
    return asset


# ---------------------------
# 基础 CRUD
# ---------------------------
@router.post("/", response_model=dict)
async def create_asset(asset: dict):
    """创建资产"""
    asset["created_at"] = datetime.utcnow()
    asset["updated_at"] = datetime.utcnow()

    result = await db["assets"].insert_one(asset)
    asset["_id"] = str(result.inserted_id)

    return {"message": "Asset created successfully", "data": asset}


@router.get("/", response_model=dict)
async def list_assets():
    """获取所有资产"""
    assets_cursor = db["assets"].find()
    assets = [serialize_asset(a) async for a in assets_cursor]
    return {"count": len(assets), "data": assets}


@router.get("/{asset_id}", response_model=dict)
async def get_asset(asset_id: str):
    # 1) Validate & load asset
    try:
        _id = ObjectId(asset_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid asset id")

    a = await db["assets"].find_one({"_id": _id, "deleted_at": {"$exists": False}})
    if not a:
        raise HTTPException(status_code=404, detail="Asset not found")

    # 2) Get intel event - handle case where it doesn't exist
    intel = await db["intel_events"].find_one({"_id": _id})
    
    # Set default values if intel event not found
    if not intel:
        print(f"No intel event found for asset_id: {asset_id}")
        intel_comp = 0  # Default severity when no intel found
        intel = {}  # Empty dict to avoid None errors
    else:
        print("Intel event found:")
        print(intel)
        # Safely get severity with default value
        intel_comp = int(intel.get("severity") or 0)

    print("----------------------------------------")

    # 3) Recent intel list pipeline
    since = datetime.utcnow() - timedelta(days=7)
    asset_id_values = [_id, str(_id)]
    
    recent_pipeline = [
        {"$match": {
            "asset_id": {"$in": asset_id_values},
            "created_at": {"$gte": since},
        }},
        {"$addFields": {"severity_num": {"$toInt": "$severity"}}},
        {"$project": {
            "_id": 0,
            "time": "$created_at",
            "source": "$source",
            "indicator": "$indicator",
            "indicator_type": "$indicator_type",
            "summary": "$summary",
            "severity": "$severity_num",
            "raw_severity": "$severity",
        }},
        {"$sort": {"time": -1}},
        {"$limit": 200},
    ]
    recent = [x async for x in db["intel_events"].aggregate(recent_pipeline)]

    # 4) Criticality & risk calculation
    crit = int(a.get("criticality") or 0)
    if not (1 <= crit <= 5):
        sens = (a.get("data_sensitivity") or "Low").lower()
        crit = 5 if sens == "high" else 3 if sens.startswith("mod") else 2
    crit = max(1, min(5, crit))
    
    # Use intel_comp which now has safe default value
    max_sev = max(1, min(5, intel_comp))
    score = crit * intel_comp

    # 5) Prepare response
    a["_id"] = str(a["_id"])
    return {
        "data": {
            **a,
            "recent_intel": recent,
            "risk": {
                "score": score,
                "components": {
                    "criticality": crit, 
                    "intel_max_severity_7d": max_sev,
                },
                "explain": f"crit {crit} × intel {intel_comp} = {score}",
                "window_days": 7,
            },
        }
    }

@router.delete("/{asset_id}", response_model=dict)
async def delete_asset(asset_id: str):
    """删除资产"""
    result = await db["assets"].delete_one({"_id": ObjectId(asset_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"message": "Asset deleted successfully"}


# ---------------------------
# 批量导入功能
# ---------------------------
@router.post("/import", response_model=dict)
async def import_assets(
    file: UploadFile = File(...),
    dry_run: bool = Query(False, description="If true, only validate without inserting"),
):
    """
    批量导入资产数据（支持 CSV / JSON）
    - dry_run=true 时只校验数据，不写入数据库
    """
    filename = file.filename.lower()
    content = await file.read()

    # --- 1️⃣ 解析文件内容 ---
    if filename.endswith(".csv"):
        text = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        assets = list(reader)
    elif filename.endswith(".json"):
        assets = json.loads(content)
    else:
        raise HTTPException(
            status_code=400, detail="Unsupported file format (only CSV or JSON)"
        )

    inserted, duplicates, errors = 0, 0, []

    # --- 2️⃣ 校验并去重 ---
    for i, asset in enumerate(assets):
        try:
            # 必填字段检查
            if not asset.get("name") or not asset.get("type"):
                errors.append(
                    {"row": i + 1, "error": "Missing required fields: name/type"}
                )
                continue

            # 设置时间戳
            asset["created_at"] = datetime.utcnow()
            asset["updated_at"] = datetime.utcnow()

            # 检查重复资产（根据 name 或 IP+hostname）
            query = {
                "$or": [
                    {"name": asset["name"]},
                    {"ip": asset.get("ip"), "hostname": asset.get("hostname")},
                ]
            }
            existing = await db["assets"].find_one(query)
            if existing:
                duplicates += 1
                continue

            if not dry_run:
                await db["assets"].insert_one(asset)
                inserted += 1
        except Exception as e:
            errors.append({"row": i + 1, "error": str(e)})

    # --- 3️⃣ 返回导入结果 ---
    return {
        "inserted": inserted,
        "duplicates_skipped": duplicates,
        "errors": errors,
        "dry_run": dry_run,
    }

class TopRiskRequest(BaseModel):
    limit: int = 5

@router.post("/top-risky", response_model=dict)
async def get_top_risky_assets(req: TopRiskRequest = Body(...)):
    """
    Return the top N risky assets, sorted by risk score (descending).
    Risk score = criticality × intel_max_severity_7d
    """
    limit = req.limit

    assets_cursor = db["assets"].find({"deleted_at": {"$exists": False}})
    assets_list = [a async for a in assets_cursor]

    risky_assets = []
    for a in assets_list:
        # Ensure _id is string
        a["_id"] = str(a["_id"])

        # Compute criticality
        crit = int(a.get("criticality") or 0)
        if not (1 <= crit <= 5):
            sens = (a.get("data_sensitivity") or "Low").lower()
            crit = 5 if sens == "high" else 3 if sens.startswith("mod") else 2
        crit = max(1, min(5, crit))

        # Get latest intel severity for this asset (max in last 7 days)
        since = datetime.utcnow() - timedelta(days=7)
        asset_id_values = [a["_id"], a.get("_id")]
        intel_pipeline = [
            {"$match": {"asset_id": {"$in": asset_id_values}, "created_at": {"$gte": since}}},
            {"$addFields": {"severity_num": {"$toInt": "$severity"}}},
            {"$sort": {"severity_num": -1}},
            {"$limit": 1},
        ]
        recent_intel = [x async for x in db["intel_events"].aggregate(intel_pipeline)]
        intel_severity = recent_intel[0]["severity_num"] if recent_intel else 1

        score = crit * intel_severity

        risky_assets.append({
            "_id": a["_id"],
            "name": a.get("name"),
            "risk": {"score": score, "criticality": crit, "intel_max_severity_7d": intel_severity},
        })

    # Sort descending and take top N
    risky_assets.sort(key=lambda x: x["risk"]["score"], reverse=True)
    top_assets = risky_assets[:limit]

    return {"count": len(top_assets), "data": top_assets}


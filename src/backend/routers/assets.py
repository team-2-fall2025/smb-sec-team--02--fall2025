from datetime import datetime
import csv
import io
import json

from bson import ObjectId
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from db.mongo import db


router = APIRouter(prefix="/api/assets", tags=["assets"])


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
    try:
        _id = ObjectId(asset_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid asset id")

    a = await db["assets"].find_one({"_id": _id, "deleted_at": {"$exists": False}})
    if not a:
        raise HTTPException(status_code=404, detail="Asset not found")

    # 7-day recent intel via links -> intel_events
    since = datetime.utcnow() - timedelta(days=7)
    pipeline = [
        {"$match": {"asset_id": _id}},
        {"$lookup": {"from": "intel_events", "localField": "intel_id", "foreignField": "_id", "as": "ie"}},
        {"$unwind": "$ie"},
        {"$match": {"ie.created_at": {"$gte": since}}},
        {"$project": {"_id": 0, "time": "$ie.created_at", "source": "$ie.source",
                      "indicator": "$ie.indicator", "severity": "$ie.severity", "match_type": "$match_type"}},
        {"$sort": {"time": -1}},
    ]
    recent = [x async for x in db["asset_intel_links"].aggregate(pipeline)]

    # risk seed = criticality(1..5) × max(1, max_severity_7d)
    crit = int(a.get("criticality") or 0)
    if not (1 <= crit <= 5):
        sens = (a.get("data_sensitivity") or "Low").lower()
        crit = 5 if sens == "high" else 3 if sens.startswith("mod") else 2
    crit = max(1, min(5, crit))
    max_sev = max([int(r.get("severity") or 0) for r in recent], default=0)
    intel_comp = max(1, max_sev)
    score = crit * intel_comp

    a["_id"] = str(a["_id"])
    return {
        "data": {
            **a,
            "recent_intel": recent,
            "risk": {
                "score": score,
                "components": {"criticality": crit, "intel_max_severity_7d": max_sev},
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

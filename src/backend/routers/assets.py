from datetime import datetime, timedelta
import csv
import io
import json

from bson import ObjectId
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.params import Body
from pydantic import BaseModel
from agents.identify_agent import generate_asset_intel_links
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
    await generate_asset_intel_links()

    return {"message": "Asset created successfully", "data": asset}

from fastapi import Body

@router.put("/", response_model=dict)
async def edit_asset(updated_asset: dict = Body(...)):
    """
    Replace an existing asset with the provided object.
    The full asset object should be provided in the request body.
    """
    print(updated_asset)
    try:
        _id = ObjectId(updated_asset["_id"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid asset id")

    # Ensure _id is not overwritten
    updated_asset["_id"] = _id
    updated_asset["updated_at"] = datetime.utcnow()

    # Keep the original created_at if it exists
    existing = await db["assets"].find_one({"_id": _id})
    if not existing:
        raise HTTPException(status_code=404, detail="Asset not found")
    updated_asset["created_at"] = existing.get("created_at", datetime.utcnow())

    # Replace the document
    result = await db["assets"].replace_one({"_id": _id}, updated_asset)
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Optionally regenerate links if key fields changed
    await generate_asset_intel_links()

    serialize_asset(updated_asset)
    return {"message": "Asset updated successfully", "data": updated_asset}


@router.get("/", response_model=dict)
async def list_assets():
    """获取所有资产"""
    days_ago = datetime.utcnow() - timedelta(days=100)

    pipeline = [
        # Lookup bridge table links
        {'$lookup': {
            'from': 'asset_intel_links',
            'localField': '_id',
            'foreignField': 'asset_id',
            'as': 'links'
        }},
        {'$unwind': {'path': '$links', 'preserveNullAndEmptyArrays': True}},
        
        # Lookup linked intel events
        {'$lookup': {
            'from': 'intel_events',
            'let': {'intel_id': '$links.intel_id'},
            'pipeline': [
                {'$match': {'$expr': {'$and': [
                    {'$eq': ['$_id', '$$intel_id']},
                    {'$gte': ['$created_at', days_ago.isoformat() + 'Z']}
                ]}}},
                {'$project': {'severity': 1, '_id': 0}}
            ],
            'as': 'intel_event'
        }},
        {'$unwind': {'path': '$intel_event', 'preserveNullAndEmptyArrays': True}},        
        # Group all severities under each asset
        {'$group': {
            "_id": "$_id",
            "org": {"$first": "$org"},
            "owner": {"$first": "$owner"},
            "business_unit": {"$first": "$business_unit"},
            "criticality": {"$first": "$criticality"},
            "data_sensitivity": {"$first": "$data_sensitivity"},
            "name": {"$first": "$name"},
            "type": {"$first": "$type"},
            "ip": {"$first": "$ip"},
            "hostname": {"$first": "$hostname"},
            'intel_events': {'$push': '$intel_event.severity'}
        }},
    ]
    assets = [x async for x in db["assets"].aggregate(pipeline)]
    # print(assets)
    for asset in assets:
        asset["_id"] = str(asset["_id"])
        
    
    
    return {"count": len(assets), "data": assets}


@router.get("/{asset_id}", response_model=dict)
async def get_asset(asset_id: str):
    # 1) Validate & load asset
    try:
        _id = ObjectId(asset_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid asset id")

    days_ago = datetime.now() - timedelta(days=30)

    pipeline = [
        {"$match": {"_id": _id}},
        {"$lookup": {
            "from": "asset_intel_links",
            "localField": "_id",
            "foreignField": "asset_id",
            "as": "links"
        }},
        {"$unwind": {"path": "$links", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "intel_events",
            "let": {"intel_id": "$links.intel_id"},
            "pipeline": [
                {"$match": {"$expr": {
                    "$and": [
                        {"$eq": ["$_id", "$$intel_id"]},
                        {"$gte": ["$created_at", days_ago.isoformat() + "Z"]}
                    ]
                }}}
            ],
            "as": "intel_event"
        }},
        {"$unwind": {"path": "$intel_event", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": "$_id",
            "org": {"$first": "$org"},
            "owner": {"$first": "$owner"},
            "business_unit": {"$first": "$business_unit"},
            "criticality": {"$first": "$criticality"},
            "data_sensitivity": {"$first": "$data_sensitivity"},
            "name": {"$first": "$name"},
            "type": {"$first": "$type"},
            "ip": {"$first": "$ip"},
            "hostname": {"$first": "$hostname"},
            "intel_events": {"$push": "$intel_event"}
        }}
    ]
    results = [x async for x in db.assets.aggregate(pipeline)]
    single_asset = results[0] if results else None

    single_asset["_id"] = str(single_asset["_id"])
    for event in single_asset.get("intel_events", []):
        event["_id"] = str(event["_id"])
    
    
    crit = int(single_asset["criticality"])
    max_sev = int(max((ie["severity"] for ie in single_asset["intel_events"]), default=0))
    risk = {
            "score": crit * max_sev,
            "explain": f"criticality ({crit}) × intel event ({max_sev})",
            "intel_max_severity_7d": max_sev,
        }
    single_asset["risk"] = risk

    return {
        "data": single_asset, 
    }

@router.delete("/{asset_id}", response_model=dict)
async def delete_asset(asset_id: str):
    """删除资产"""
    result = await db["assets"].delete_one({"_id": ObjectId(asset_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Asset not found")
    # Delete all links for this asset
    result = await db["asset_intel_links"].delete_many({"asset_id": asset_id})

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
    
    await generate_asset_intel_links()
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
    days_ago = datetime.now() - timedelta(days=100)
    
    pipeline = [
        {'$lookup': {
            'from': 'asset_intel_links',
            'localField': '_id',
            'foreignField': 'asset_id',
            'as': 'links'
        }},
        {'$unwind': {'path': '$links', 'preserveNullAndEmptyArrays': True}},
        {'$lookup': {
            'from': 'intel_events',
            'let': {'intel_id': '$links.intel_id'},
            'pipeline': [
                {'$match': {'$expr': {'$and': [
                    {'$eq': ['$_id', '$$intel_id']},
                    {'$gte': ['$created_at', days_ago.isoformat() + 'Z']}
                ]}}},
                {'$project': {'severity': 1, '_id': 0}}
            ],
            'as': 'intel_event'
        }},
        {'$unwind': {'path': '$intel_event', 'preserveNullAndEmptyArrays': True}},
        {'$match': {'intel_event': {'$exists': True}}},
        {'$group': {
            "_id": "$_id",
            "criticality": {"$first": "$criticality"},
            "name": {"$first": "$name"},
            'intel_events': {'$push': '$intel_event.severity'}
        }},
        {'$project': {'_id': 0, 'name': 1, 'criticality': 1, 'intel_events': 1}}
    ]

    # Execute the query
    assets = [x async for x in db["assets"].aggregate(pipeline)]
    risky_assets = []
    for asset in assets:
        max_sev = max(map(int, asset.get("intel_events", [0])))
        crit = int(asset.get("criticality") or 0)
        score = crit * max_sev
        risky_assets.append({
            "name": asset.get("name"),
            "risk": {"score": score, "criticality": crit, "intel_max_severity_7d": max_sev},
        })
    # Sort descending and take top N
    risky_assets.sort(key=lambda x: x["risk"]["score"], reverse=True)
    top_assets = risky_assets[:limit]
    return {"count": len(top_assets), "data": top_assets}


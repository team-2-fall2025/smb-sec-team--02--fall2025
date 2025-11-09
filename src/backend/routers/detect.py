from http.client import HTTPException
import os
from typing import Optional
from bson import ObjectId
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import APIRouter, Query

from agents.detect_agent import compute_detection, create_or_update_risk_item, group_by_dedup_key, send_teams_alert
from db.mongo import db

load_dotenv()

router = APIRouter(prefix="/detect", tags=["detect"])
TIME_MULTIPLIER = int(os.getenv("TIME_MULTIPLIER", "1"))

@router.get("/ping")
async def ping_detect():
    return {"area": "detect", "ok": True}


@router.post("/run")
async def run_detect():
    """
    MVP Detect Agent:
    - Pull intel from last 24h
    - Dedup by (asset_id, indicator, source)
    - Create or update detection
    - Return summary
    """
    window_hours = 24 * TIME_MULTIPLIER
    print ("TIME_MULTIPLIER:", TIME_MULTIPLIER)
    cutoff = datetime.utcnow() - timedelta(hours=window_hours)

    # 1. Get recent intel
    recent_intel = []
    async for doc in db["intel_events"].find({"created_at": {"$gte": cutoff.isoformat() + 'Z'}}):
        recent_intel.append(doc)
    print(f"Recent intel count: {len(recent_intel)}")
    if not recent_intel:
        return {"new_detections": 0, "deduped": 0, "alerts_sent": 0, "risk_items_opened": 0}

    summary = {
        "new_detections": 0,
        "deduped": 0,
        "alerts_sent": 0,
        "risk_items_opened": 0,
    }

    # 2. Process each dedup group
    for group in group_by_dedup_key(recent_intel):
        if not group:
            continue
        dedup_key = (
            group[0]["asset_id"],
            group[0]["indicator"],
            group[0]["source"]
        )

        # 3. Check for existing detection in window
        existing = await db["detections"].find_one({
            "asset_id": dedup_key[0],
            "indicator": dedup_key[1],
            "source": dedup_key[2],
            "last_seen": {"$gte": cutoff}
        })

        detection = compute_detection(group)
        if existing:
            # --- DEDUP: update hit_count & last_seen ---
            await db["detections"].update_one(
                {"_id": existing["_id"]},
                {
                    "$inc": {"hit_count": len(group)},
                    "$set": {"last_seen": datetime.utcnow()}
                }
            )
            summary["deduped"] += 1
        else:
            # --- NEW: insert ---
            detection_dict = detection.model_dump(by_alias=True, exclude={"id"})
            result = await db.detections.insert_one(detection_dict)
            detection_dict["_id"] = result.inserted_id
            summary["new_detections"] += 1
            print("at new detection:", detection_dict)
            await create_or_update_risk_item(detection_dict)
            summary["risk_items_opened"] += 1  # Even if upsert, count as "handled"
            # Send alert only on NEW qualifying detection
            asset = db.assets.find_one({"_id": detection_dict["asset_id"]})
            # --- SEND TEAMS ALERT ONLY ON NEW ---
            asset = await db.assets.find_one({"_id": detection_dict["asset_id"]})
            if asset and detection_dict["severity"] >= 4:
                if send_teams_alert(detection_dict, asset):
                    summary["alerts_sent"] += 1

    return summary


@router.get("/detections", response_model=dict)
async def get_detections(
    skip: int = Query(0, ge=0, description="Pagination: skip N records"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    severity: Optional[int] = Query(None, ge=1, le=5),
    source: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None),
    ttp: Optional[str] = Query(None),
    since: Optional[str] = Query(None),  # ISO format
):
    """
    Returns paginated detections.
    Frontend does client-side filtering → we return full page.
    """
    query: dict = {}

    if severity is not None:
        query["severity"] = severity
    if source:
        query["source"] = {"$regex": source, "$options": "i"}
    if asset_id:
        query["asset_id"] = {"$regex": asset_id, "$options": "i"}
    if ttp:
        query["ttp"] = {"$regex": ttp, "$options": "i"}
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            query["first_seen"] = {"$gte": since_dt}
        except ValueError:
            raise HTTPException(
                400,
                "Invalid 'since' format. Use ISO: 2025-11-01T00:00:00Z or +00:00"
            )

    # 1. Count total
    total = await db.detections.count_documents(query)

    # 2. Fetch paginated docs using to_list()
    cursor = db.detections.find(query).sort("last_seen", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    
    # Get asset names for all unique asset_ids
    asset_ids = [doc["asset_id"] for doc in docs if doc.get("asset_id")]
    asset_names_map = {}
    
    if asset_ids:
        assets_cursor = db["assets"].find({"_id": {"$in": asset_ids}})
        assets = await assets_cursor.to_list(length=len(asset_ids))
        asset_names_map = {str(asset["_id"]): asset.get("name", "Unknown") for asset in assets}

    # 4. Transform docs and add asset_name
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        doc["asset_id"] = str(doc["asset_id"])
        # Add asset_name field
        doc["asset_name"] = asset_names_map.get(str(doc["asset_id"]), "Unknown")

    return {"data": docs, "total": total, "skip": skip, "limit": limit}

@router.get("/detections/{det_id}", response_model=dict)
async def get_detection_detail(det_id: str):
    """
    Get full detection detail by ID.
    Includes: asset context, intel samples, analyst_note, history.
    """
    if not ObjectId.is_valid(det_id):
        raise HTTPException(400, "Invalid detection ID")

    # Add await to all database operations
    doc = await db.detections.find_one({"_id": ObjectId(det_id)})
    if not doc:
        raise HTTPException(404, "Detection not found")

    # Enrich with asset name (optional) - add await
    asset = await db.assets.find_one({"_id": doc["asset_id"]})
    if asset:
        doc["asset_name"] = asset.get("name", "Unknown")
        doc["asset_criticality"] = asset.get("criticality", "Unknown")
        doc["asset_bu"] = asset.get("business_unit", "Unknown")
        doc["asset_owner"] = asset.get("owner", "Unknown")
        

    # Add raw intel samples (from raw_ref) - add await and fix async operations
    intel_ids = doc.get("raw_ref", {}).get("intel_ids", [])
    intel_samples = []
    if intel_ids:
        # Convert to ObjectId list
        object_ids = [ObjectId(i) for i in intel_ids if ObjectId.is_valid(i)]
        if object_ids:
            # Use to_list() for async cursor
            cursor = db.intel_events.find({"_id": {"$in": object_ids}}).limit(3)
            intel_samples = await cursor.to_list(length=3)
            for sample in intel_samples:
                sample["_id"] = str(sample["_id"])
                sample["asset_id"] = str(sample["asset_id"])

    doc["intel_samples"] = intel_samples
    doc["_id"] = str(doc["_id"])
    doc["asset_id"] = str(doc["asset_id"])

    return doc

@router.get("/risk_items", response_model=dict)
async def get_risk_items(
    asset_id: str = Query(..., description="Required: asset_id to fetch risk items")
):
    """
    Get ALL risk items for a specific asset.
    Used by RiskItemsPanel in frontend.
    No pagination — returns full list.
    """
    if not ObjectId.is_valid(ObjectId(asset_id)):
        raise HTTPException(400, "Invalid asset_id format. Must be a valid ObjectId.")

    query = {"asset_id": ObjectId(asset_id)}
    cursor = db.risk_items.find(query).sort("due", 1)
    docs = await cursor.to_list(length=None)  # None = no limit

    # Convert ObjectId to str
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        doc["asset_id"] = str(doc["asset_id"])

    return {
        "data": docs
    }

@router.get("/lastDay", response_model=int)
async def get_detections_24h():
    """
    Returns count of detections in last 24 hours.
    Used by Dashboard → Detections (24h) widget.
    """
    cutoff = datetime.utcnow() - timedelta(hours=24 * TIME_MULTIPLIER)
    count = await db["detections"].count_documents({"last_seen": {"$gte": cutoff}})
    return count


@router.get("/trend", response_model=dict)
async def get_detections_trend(days: int = Query(7, ge=1, le=30)):
    """
    Returns daily detection counts for last N days.
    Used by Dashboard → mini trendline.
    """
    end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=abs(days - 1 * TIME_MULTIPLIER))
    pipeline = [
        {"$match": {"last_seen": {"$gte": start_date}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": {"$toDate": "$last_seen"}
                    }
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]

    result = await db.detections.aggregate(pipeline).to_list(length=None)
    data = [{"date": r["_id"], "count": r["count"]} for r in result]
    return {"data": data}


@router.get("/high-sev", response_model=dict)
async def get_top_high_sev_detections(
    limit: int = Query(5, ge=1, le=10),
    min_severity: int = Query(4, ge=1, le=5)
):
    """
    Returns top N high-severity detections, sorted by last_seen (desc).
    Used by Dashboard → Top 5 High-Severity Detections.
    """
    cursor = (
        db.detections
        .find({"severity": {"$gte": min_severity}})
        .sort([("severity", -1), ("last_seen", -1)])
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)

    # Enrich with asset name
    asset_ids = [doc["asset_id"] for doc in docs if doc.get("asset_id")]
    asset_names_map = {}
    if asset_ids:
        assets = await db["assets"].find({"_id": {"$in": asset_ids}}).to_list(length=len(asset_ids))
        asset_names_map = {str(a["_id"]): a.get("name", "Unknown") for a in assets}

    for doc in docs:
        doc["_id"] = str(doc["_id"])
        doc["asset_id"] = str(doc["asset_id"])
        doc["asset_name"] = asset_names_map.get(str(doc["asset_id"]), "Unknown")

    return {"data": docs}

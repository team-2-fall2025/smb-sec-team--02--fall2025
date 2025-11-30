from datetime import datetime
from typing import Dict, List, Literal, Optional
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from agents.protect_agent import get_coverage, run_protect_agent
from db.mongo import db
import markdown2


router = APIRouter(prefix="/api/protect", tags=["protect"])

@router.get("/ping")
def ping_protect():
    return {"area": "protect", "ok": True}

@router.get("/run")
async def trigger_protect_agent():
    result = await run_protect_agent()
    return result

@router.get("/coverage", response_model=Dict[str, float])
async def get_protect_coverage() -> Dict[str, float]:
    return await get_coverage()

# ----------------------------------------------------------------------
# 1. Controls List + Filtering
# ----------------------------------------------------------------------
@router.get("/", response_model=List[dict])
async def list_controls(
    family: Optional[str] = Query(None, description="Filter by family: AC, AU, SC, etc."),
    csf_category: Optional[str] = Query(None, description="e.g., PR.AC, PR.DS"),
    status: Optional[Literal["Proposed", "In-Progress", "Implemented", "Declined"]] = Query(None),
    limit: int = Query(100, le=200),
    skip: int = Query(0, ge=0)
):
    """
    Returns filtered list of controls.
    Supports: family, csf_category, status.
    Used by Governance → Controls table.
    """
    query = {"implementation_status": {"$ne": "Declined"}}  # default: hide declined

    if family:
        query["family"] = family.upper()
    if csf_category:
        query["csf_category"] = csf_category.upper()
    if status:
        query["implementation_status"] = status
    controls = await db.controls.find(query, {
        "_id": 1,
        "control_id": 1,
        "title": 1,
        "family": 1,
        "csf_function": 1,
        "csf_category": 1,
        "subcategory": 1,
        "implementation_status": 1,
        "created_at": 1
    }).sort("control_id").skip(skip).limit(limit).to_list(length=None)

    # Convert ObjectId to str
    for c in controls:
        c["_id"] = str(c["_id"])

    return controls


# ----------------------------------------------------------------------
# 2. Control Detail (includes SOP as HTML + evidence list)
# ----------------------------------------------------------------------
@router.get("/{control_id}", response_model=dict)
async def get_control_detail(control_id: str):
    """
    Full control detail page.
    Returns:
      - title, family, status
      - CSF mapping
      - applicable assets (via policy_assignments)
      - SOP rendered as safe HTML
      - list of evidence records
    """
    # 1. Find the control (by control_id like "IA-2")
    control = await db.controls.find_one({"control_id": control_id})
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")

    # 2. Get SOP and render as HTML
    sop_html = "<p>No SOP attached.</p>"
    if control.get("sop_id"):
        sop_doc = await db.sops.find_one({"_id": control["sop_id"]})
        if sop_doc and sop_doc.get("content"):
            # sop_html = sop_doc["content"]
            sop_html = markdown2.markdown(sop_doc["content"], extras=["fenced-code-blocks", "tables", "break-on-newline"])

    # 3. Applicable assets (via policy_assignments)
    assignments = await db.policy_assignments.find(
        {"control_id": control_id},
        {"asset_id": 1, "status": 1, "owner": 1}
    ).to_list(length=None)
    asset_ids = [a["asset_id"] for a in assignments]
    assets = await db.assets.find(
        {"_id": {"$in": asset_ids}},
        {"name": 1, "ip_address": 1, "asset_type": 1, "tags": 1}
    ).to_list(length=None) if asset_ids else []

    # Convert asset ObjectIds
    for asset in assets:
        asset["_id"] = str(asset["_id"])

    # 4. Evidence records
    evidence = await db.control_evidence.find(
        {"control_id": control_id},
        {"evidence_type": 1, "location": 1, "submitted_by": 1, "submitted_at": 1}
    ).sort("submitted_at", -1).to_list(length=None)

    for ev in evidence:
        ev["_id"] = str(ev["_id"])
        ev["submitted_at"] = ev["submitted_at"].isoformat()

    # 5. Final response
    response = {
        "control_id": control["control_id"],
        "title": control["title"],
        "family": control["family"],
        "csf_function": control.get("csf_function", "Protect"),
        "csf_category": control.get("csf_category", "PR.AC"),
        "implementation_status": control["implementation_status"],
        "applicability_rule": control.get("applicability_rule", {}),
        "sop_html": sop_html,
        "applicable_assets": [
            {
                "asset_id": str(a["_id"]),
                "name": a.get("name", "Unnamed"),
                "ip_address": a.get("ip_address", ""),
                "asset_type": a.get("asset_type", ""),
                "tags": a.get("tags", []),
                "assignment_status": next((pa["status"] for pa in assignments if str(pa["asset_id"]) == str(a["_id"])), "Proposed")
            }
            for a in assets
        ],
        "evidence": evidence,
        "created_at": control["created_at"].isoformat()
    }

    return response


# GET assignments for an asset
@router.get("/get-assignments/{asset_id}", response_model=List[dict])
async def get_assignments_for_asset(asset_id: str):
    assignments = await db.policy_assignments.find({"asset_id": ObjectId(asset_id)}).to_list(length=None)
    for a in assignments:
        control = await db.controls.find_one({"control_id": a["control_id"]})
        a["control_title"] = control["title"] if control else "Unknown"
        a["family"] = control["family"] if control else "??"
        a["csf_category"] = control.get("csf_category", "N/A")
        evidences = await db.control_evidence.find({"control_assignment_id": str(a["_id"])}).to_list(length=None)
        for ev in evidences:
            ev["_id"] = str(ev["_id"])
        a["evidence"] = evidences
        a["_id"] = str(a["_id"])
        # a["sop_id"] = str(a["sop_id"])
        a["asset_id"] = str(a["asset_id"])
        a["control_object_id"] = str(a["control_object_id"])
    return assignments

# PUT status
@router.put("/update_assignment/{assignment_id}")
async def update_assignment(assignment_id: str, update: dict):
    await db.policy_assignments.update_one({"_id": ObjectId(assignment_id)}, {"$set": update})
    return {"status": "updated"}

# POST evidence (metadata only)
@router.post("/upload_evidence")
async def upload_evidence(ev: dict):
    ev["submitted_at"] = datetime.utcnow()
    ev["submitted_by"] = "current_user@smb.com"  # stub
    result = await db.control_evidence.insert_one(ev)
    return {"id": str(result.inserted_id)}
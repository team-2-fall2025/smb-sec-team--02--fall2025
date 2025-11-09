
import re
from db.mongo import db
from datetime import datetime

_HW_PAT = re.compile(r"server|srv|vm|host|router|switch|firewall|loadbalancer|nas|san|laptop|desktop|printer|device|hardware|hw|physical|machine|tablet|phone|mobile", re.I)
_SW_PAT = re.compile(r"app|application|software|program|tool|system|platform|website|webapp|portal|cms|database|db|mysql|postgres|oracle|mongodb", re.I)
_SERVICE_PAT = re.compile(r"api|endpoint|gateway|proxy|microservice|webservice|rest|soap|graphql|interface|connector|adapter", re.I)
_DATA_PAT = re.compile(r"dataset|data|file|repository|archive|backup|log|audit|record|document|report|table|schema|collection|bucket|config|setting|secret|certificate", re.I)
_USER_PAT = re.compile(r"user|account|employee|staff|personnel|admin|administrator|team|group|department|division|customer|client", re.I)

# Email pattern
_EMAIL_PAT = re.compile(r"@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

def infer_type(name: str | None, hostname: str | None = None, owner: str | None = None) -> str:
    """
    Simple asset type inference using nested if-else logic
    """
    if not name:
        return "SW"
    
    n = name.lower()
    h = (hostname or "").lower()
    o = (owner or "").lower()
    
    # Check for email patterns first (strong indicator for User)
    if _EMAIL_PAT.search(n) or _EMAIL_PAT.search(o):
        return "User"
    
    # Check hostname patterns
    if h:
        if h.startswith(('api.', 'svc.', 'service.', 'ws.', 'gateway.')):
            return "Service"
        if h.startswith(('db.', 'database.', 'mysql.', 'postgres.')):
            return "SW"
        if h.startswith(('srv.', 'server.', 'vm.', 'host.')):
            return "HW"
        if h.startswith(('user-', 'account-', 'admin-', 'team-')):
            return "User"
    
    # Check name patterns in priority order
    if _HW_PAT.search(n):
        return "HW"
    
    if _SERVICE_PAT.search(n):
        return "Service"
    
    if _DATA_PAT.search(n):
        return "Data"
    
    if _USER_PAT.search(n):
        return "User"
    
    if _SW_PAT.search(n):
        return "SW"
    
    # Default fallback
    return "SW"

def crit_from_sens(s: str | None) -> int:
    s = (s or "Low").lower()
    if s == "high":
        return 5
    if s.startswith("mod"):
        return 3
    return 2

async def generate_asset_intel_links():
    """
    Efficiently link assets ↔ intel_events using MongoDB aggregation
    based on matching IP or hostname (depending on indicator_type).
    Also updates intel_events with matched asset_id.
    """

    # ---- 1) Match IP-based intel ----
    ip_matches = db["intel_events"].aggregate([
        {"$match": {"indicator_type": "ip"}},
        {"$lookup": {
            "from": "assets",
            "localField": "indicator",
            "foreignField": "ip",
            "as": "matched_assets"
        }},
        {"$unwind": "$matched_assets"},
        {"$project": {
            "intel_id": "$_id",
            "asset_id": "$matched_assets._id",
            "asset_name": "$matched_assets.name",
            "intel_indicator": "$indicator",
            "match_type": {"$literal": "ip"}
        }}
    ])

    # ---- 2) Match hostname-based intel ----
    host_matches = db["intel_events"].aggregate([
        {"$match": {"indicator_type": {"$in": ["hostname", "domain"]}}},
        {"$lookup": {
            "from": "assets",
            "localField": "indicator",
            "foreignField": "hostname",
            "as": "matched_assets"
        }},
        {"$unwind": "$matched_assets"},
        {"$project": {
            "intel_id": "$_id",
            "asset_id": "$matched_assets._id",
            "asset_name": "$matched_assets.name",
            "intel_indicator": "$indicator",
            "match_type": {"$literal": "hostname"}
        }}
    ])

    # ---- 3) Insert combined results into bridge table and update intel_events ----
    inserted = 0

    async for match in ip_matches:
        # Update asset_intel_links bridge table
        await db["asset_intel_links"].update_one(
            {"asset_id": match["asset_id"], "intel_id": match["intel_id"]},
            {"$setOnInsert": {
                **match,
                "created_at": datetime.utcnow(),
            }},
            upsert=True
        )
        
        # Add asset_id to the intel_event entry
        await db["intel_events"].update_one(
            {"_id": match["intel_id"]},
            {"$set": {"asset_id": match["asset_id"]}}
        )
        
        inserted += 1

    async for match in host_matches:
        # Update asset_intel_links bridge table
        await db["asset_intel_links"].update_one(
            {"asset_id": match["asset_id"], "intel_id": match["intel_id"]},
            {"$setOnInsert": {
                **match,
                "created_at": datetime.utcnow(),
            }},
            upsert=True
        )
        
        # Add asset_id to the intel_event entry
        await db["intel_events"].update_one(
            {"_id": match["intel_id"]},
            {"$set": {"asset_id": match["asset_id"]}}
        )
        
        inserted += 1

    return inserted
    
async def infere_asset_fields():
    """
    Process assets table and infer missing type/criticality fields.
    """
    
    # Get all assets
    assets = [asset async for asset in db["assets"].find()]
    
    updated_count = 0
    
    # Process each asset
    for asset in assets:
        update_fields = {}
        
        # Infer type only if it doesn't exist or is empty
        if not asset.get("type"):
            inferred_type = infer_type(
                name=asset.get("name"), 
                hostname=asset.get("hostname"), 
                owner=asset.get("owner")
            )
            update_fields["type"] = inferred_type
        
        # Infer criticality only if it doesn't exist
        if not asset.get("criticality"):
            inferred_criticality = crit_from_sens(asset.get("data_sensitivity"))
            update_fields["criticality"] = inferred_criticality
        
        # Update asset only if we have fields to update
        if update_fields:
            await db["assets"].update_one(
                {"_id": asset["_id"]},
                {"$set": update_fields}
            )
            updated_count += 1
    
    return updated_count
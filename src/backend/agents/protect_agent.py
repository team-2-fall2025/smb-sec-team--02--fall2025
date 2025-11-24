# backend/agents/protect_agent.py
# Policy Builder Agent MVP — NO CSF PROFILE REQUIRED
# Works purely on assets + detections + risks

from datetime import datetime, timedelta
from typing import List, Dict, Any
from bson import ObjectId
from agents.detect_agent import TIME_MULTIPLIER
from db.mongo import db


NIST_TITLES = {
    "AC-2":   "Account Management",
    "IA-2":   "Multifactor Authentication (MFA)",
    "IA-5":   "Authenticator Management",
    "SC-13":  "Cryptographic Protection",
    "SC-28":  "Protection of Information at Rest",
    "SI-4":   "System Monitoring",
    "SI-7":   "Software, Firmware, and Information Integrity",
    "CM-6":   "Configuration Settings",
    "AU-6":   "Audit Record Review, Analysis, and Reporting",
    "CP-9":   "System Backup",
    "CP-10":  "System Recovery and Reconstitution",
    "IR-4":   "Incident Handling",
    "MA-2":   "Controlled Maintenance",
    "RA-3":   "Risk Assessment",
    "CA-2":   "Control Assessments",
}

# Rule format: (condition function) → list of control_ids
SMB_RULES = [
    # High criticality + internet-facing → strong access controls
    (lambda a: int(a.get("criticality", 0)) >= 4 and "internet-facing" in a.get("tags", []), ["AC-2", "IA-2", "IA-5"]),

    # Remote access assets → MFA mandatory
    (lambda a: "remote-access" in a.get("tags", []), ["IA-2"]),

    # Assets containing PHI or PII → encryption at rest
    (lambda a: any(t in a.get("tags", []) for t in ["phi", "pii", "sensitive"]), ["SC-28", "SC-13"]),

    # Windows servers → hardening + integrity
    (lambda a: "windows" in a.get("tags", []), ["CM-6", "SI-7"]),

    # Any asset with recent high-sev detection → monitoring + audit
    (lambda a, recent_detections: any(d.get("asset_id") == str(a["_id"]) for d in recent_detections), ["SI-4", "AU-6"]),

    # High criticality assets → backup & recovery
    (lambda a: int(a.get("criticality", 0)) >= 4, ["CP-9", "CP-10"]),

    # Any open risk → incident handling & risk assessment
    (lambda a, open_risks: any(r.get("asset_id") == str(a["_id"]) for r in open_risks), ["IR-4", "RA-3", "CA-2"]),
]

# ----------------------------------------------------------------------
# 4. Simple SOP stub (≤12 steps, Markdown)
# ----------------------------------------------------------------------
def generate_sop(control_id: str) -> str:
    templates = {
        "IA-2": "# Enable Multi-Factor Authentication (MFA)\n**Owner:** IT Admin\n**Cadence:** One-time + quarterly verification\n\n**Steps:**\n1. Log into IdP (Okta/Azure AD)\n2. Enable MFA for all users\n3. Enforce for privileged accounts\n4. Test with test account\n5. Document exceptions\n**Evidence:** IdP policy screenshot + test log",
        "SC-28": "# Encrypt Data at Rest\n**Owner:** SysAdmin\n**Cadence:** One-time\n\n**Steps:**\n1. Enable BitLocker (Windows) or LUKS (Linux)\n2. Verify encryption status on all drives\n3. Update asset inventory\n**Evidence:** BitLocker status report",
        # Default fallback
    }
    default = f"# SOP for {control_id}: {NIST_TITLES.get(control_id, 'Unknown')}\n**Owner:** IT Admin\n**Cadence:** Quarterly\n\n**Steps:**\n1. Review current configuration\n2. Implement recommended control\n3. Test and verify\n4. Document evidence"
    return templates.get(control_id, default)

# ----------------------------------------------------------------------
# 5. Main Agent Logic
# ----------------------------------------------------------------------
async def run_protect_agent() -> Dict[str, Any]:
    # --- Load inputs ---
    seven_days_ago = datetime.utcnow() - timedelta(days=7 * TIME_MULTIPLIER)

    high_crit_assets = await db["assets"].find({"criticality": {"$gte": "4"}}).to_list(length=None)
    
    recent_detections = await db["detections"].find({"first_seen": {"$gte": seven_days_ago}, "severity": {"$gte": 3}}).to_list(length=None)
    
    open_risks = await db.risk_items.find({"status": "Open"}).to_list(length=None)
    

    # --- Generate recommendations ---
    seen_control_ids = set()  # deduplication
    recommendations = []

    for asset in high_crit_assets:
        asset_tags = asset.get("tags", [])

        for condition_fn, control_ids in SMB_RULES:
            # Some conditions need extra data
            if "recent_detections" in condition_fn.__code__.co_varnames:
                applies = condition_fn(asset, recent_detections)
            elif "open_risks" in condition_fn.__code__.co_varnames:
                applies = condition_fn(asset, open_risks)
            else:
                applies = condition_fn(asset)

            if applies:
                for cid in control_ids:
                    if cid not in seen_control_ids and cid in NIST_TITLES:
                        seen_control_ids.add(cid)

                        # Create SOP
                        sop_content = generate_sop(cid)
                        sop_doc = await db.sops.insert_one({
                            "control_id": cid,
                            "content": sop_content,
                            "created_at": datetime.utcnow()
                        })
                        sop_id = sop_doc.inserted_id
                        # Build Control document
                        control = {
                            "family": cid.split("-")[0],
                            "control_id": cid,
                            "title": NIST_TITLES[cid],
                            "csf_function": "Protect",  # we can infer later
                            "csf_category": "PR.AC",    # placeholder – fine for MVP
                            "subcategory": f"{cid}-1",
                            "applicability_rule": {
                                "criticality_gte": 4,
                                "tags": asset_tags
                            },
                            "implementation_status": "Proposed",
                            "evidence_required": ["Screenshot", "Config export"],
                            "sop_id": sop_id,
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }

                        # Insert Control
                        control_result = await db.controls.insert_one(control)
                        control_obj_id = control_result.inserted_id
                        
                        # Create assignment to this asset
                        db.policy_assignments.insert_one({
                            "asset_id": asset["_id"],
                            "control_id": cid,
                            "control_object_id": control_obj_id,
                            "status": "Proposed",
                            "owner": "it-admin@company.com",
                            "created_at": datetime.utcnow()
                        })

                        recommendations.append(control)

    # --- Simple coverage (for dashboard widget) ---
    unique_families = len({c["family"] for c in recommendations})
    coverage = {
        "CSF.Protect": round(min(unique_families / 6, 1.0), 2),  # rough estimate
        "total_recommended": len(recommendations)
    }

    return {
        "new_controls": len(recommendations),
        "policies_created": 0,
        "coverage": coverage,
        "risk_items_updated": 0  # you’ll add residual risk later
    }
    
async def get_coverage() -> Dict[str, float]:
    """
    Returns only CSF coverage percentages.
    Example response:
    {
      "CSF.Identify": 0.40,
      "CSF.Protect": 0.78,
      "CSF.Detect": 0.65,
      "CSF.Respond": 0.50,
      "CSF.Recover": 0.60,
      "CSF.Govern": 0.55
    }
    """
    # Count recommended/implemented controls per function
    pipeline = [
        {"$match": {
            "implementation_status": {"$in": ["Proposed", "In-Progress", "Implemented"]},
        }},
        {"$group": {
            "_id": "$csf_function",
            "count": {"$sum": 1}
        }}
    ]
    
    results = await db.controls.aggregate(pipeline).to_list(length=None)
    coverage_by_function = {item["_id"]: item["count"] for item in results}

    # Define target numbers for SMB (realistic MVP targets)
    TARGETS = {
        # "Identify": 8,
        "Protect": 6,
        # "Detect": 12,
        # "Respond": 10,
        # "Recover": 8,
        # "Govern": 10
    }

    # Compute percentages
    coverage = {
        f"CSF.{func}": round(min(coverage_by_function.get(func, 0) / TARGETS[func], 1.0), 2)
        for func in TARGETS
    }

    return coverage
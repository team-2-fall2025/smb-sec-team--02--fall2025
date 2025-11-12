from datetime import datetime, timedelta
from typing import Dict, List, Any, Set, Tuple
from bson import ObjectId
from .sop_generator import build_sop_for_control
from .coverage import compute_csf_coverage
from .residual_risk import update_residual_risk_for_assets

# ---- Normalizers (add these above RULES) ----
def safe_int(v, default=0):
    """Coerce v to int if possible (handles '5', '5.0', 5, 5.0, True/False)."""
    try:
        if isinstance(v, bool):
            return int(v)
        if isinstance(v, int):
            return v
        if isinstance(v, float):
            return int(v)
        if isinstance(v, str):
            s = v.strip()
            # try plain int
            try:
                return int(s)
            except ValueError:
                # try float like '4.0'
                return int(float(s))
        return default
    except Exception:
        return default

_SENS_MAP = {
    "very low": "Very Low",
    "low": "Low",
    "medium": "Medium",
    "med": "Medium",
    "moderate": "Medium",
    "high": "High",
    "very high": "Very High",
}

def norm_sensitivity(v) -> str:
    """
    Map various inputs to one of:
    {'Very Low','Low','Medium','High','Very High'}.
    Accepts numbers 1-5 (as int/str/float) or text labels.
    """
    if v is None:
        return "Unknown"
    # numeric?
    try:
        n = safe_int(v, None)
        if n is not None:
            return ["Very Low", "Low", "Medium", "High", "Very High"][max(1, min(5, n)) - 1]
    except Exception:
        pass
    # text?
    if isinstance(v, str):
        key = v.strip().lower()
        return _SENS_MAP.get(key, v)  # fall back to original text if unknown
    return "Unknown"

def has_sensitive_tag(asset) -> bool:
    tags = set(asset.get("tags", [])) if isinstance(asset.get("tags"), list) else set()
    return any(t in tags for t in ["PII", "PHI", "Finance"])

def crit_gte(asset, threshold: int) -> bool:
    return safe_int(asset.get("criticality", 1), 1) >= threshold

# ---- Helper: safe get ----
def _get(d: dict, path: str, default=None):
    cur = d
    for p in path.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur

# ---- Deterministic rules (MVP) ----
# If you prefer YAML, move these into /config/policy_rules.yaml; for MVP we inline.
# ---- Deterministic rules (MVP) ----
RULES: List[Dict[str, Any]] = [
    # Access/MFA
    {
        "name": "High-criticality + High-sensitivity -> MFA",
        "when": lambda asset: crit_gte(asset, 4) and norm_sensitivity(_get(asset, "data.sensitivity")) in {"High", "Very High"},
        "controls": [
            {"control_id": "IA-2", "family": "IA", "title": "Identification and Authentication (Users)",
             "csf_function": "Protect", "csf_category": "PR.AC", "subcategory": "PR.AC-1"}
        ]
    },
    # Data protection
    {
        "name": "Stores PII/PHI -> Crypto + At-rest encryption",
        "when": lambda asset: has_sensitive_tag(asset),
        "controls": [
            {"control_id": "SC-13", "family": "SC", "title": "Cryptographic Protection",
             "csf_function": "Protect", "csf_category": "PR.DS", "subcategory": "PR.DS-1"},
            {"control_id": "SC-28", "family": "SC", "title": "Protection of Information at Rest",
             "csf_function": "Protect", "csf_category": "PR.DS", "subcategory": "PR.DS-1"}
        ]
    },
    # Monitoring from detections context (last 7d)
    {
        "name": "Recent high-sev detections -> Monitoring & Audit Review",
        "when": lambda asset: True,  # evaluated per-asset with detections joined below
        "controls": [
            {"control_id": "SI-4", "family": "SI", "title": "System Monitoring",
             "csf_function": "Detect", "csf_category": "DE.CM", "subcategory": "DE.CM-7"},
            {"control_id": "AU-6", "family": "AU", "title": "Audit Review, Analysis, and Reporting",
             "csf_function": "Detect", "csf_category": "DE.CM", "subcategory": "DE.CM-3"}
        ],
        "gate": {"min_severity": 3}
    },
    # Governance baseline
    {
        "name": "Org baseline -> Risk Assessment cadence",
        "when": lambda asset: asset.get("_scope", "org") == "org",
        "controls": [
            {"control_id": "RA-3", "family": "RA", "title": "Risk Assessment",
             "csf_function": "Govern", "csf_category": "GV.RM", "subcategory": "GV.RM-01"}
        ]
    },
]

EFFECTIVENESS_BY_STATUS = {"Proposed": 0.1, "In-Progress": 0.3, "Implemented": 0.6}

async def _load_assets(db) -> List[Dict[str, Any]]:
    # Expect your assets collection to exist already
    return [a async for a in db.assets.find({})]

async def _load_recent_detections(db, days: int = 7) -> Dict[ObjectId, List[Dict[str, Any]]]:
    since = datetime.utcnow() - timedelta(days=days)
    det_map: Dict[ObjectId, List[Dict[str, Any]]] = {}
    async for d in db.detections.find({"created_at": {"$gte": since}}):
        aid = d.get("asset_id")
        if isinstance(aid, str):
            try: aid = ObjectId(aid)
            except: pass
        det_map.setdefault(aid, []).append(d)
    return det_map

async def _ensure_control_master(db, c: Dict[str, Any]) -> Tuple[ObjectId, Dict[str, Any]]:
    # Upsert control master in `controls` (status Proposed by default); link SOP if not present
    now = datetime.utcnow()
    payload = dict(c)
    payload.setdefault("implementation_status", "Proposed")
    payload.setdefault("created_at", now)
    payload.setdefault("updated_at", now)
    await db.controls.update_one(
        {"control_id": payload["control_id"]},
        {"$setOnInsert": payload},
        upsert=True
    )
    found = await db.controls.find_one({"control_id": payload["control_id"]})
    return found["_id"], found

async def _ensure_sop(db, control: Dict[str, Any]) -> ObjectId | None:
    # If control.sop_id is missing, generate and store a SOP doc (Markdown)
    if control.get("sop_id"):
        return control["sop_id"]
    sop_md = build_sop_for_control(control)
    if not sop_md:
        return None
    # Store SOP in a simple `sops` collection
    sop_doc = {
        "control_id": control["control_id"],
        "title": f"SOP: {control['title']} ({control['control_id']}, {control['csf_category']})",
        "markdown": sop_md,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res = await db.sops.insert_one(sop_doc)
    await db.controls.update_one({"_id": control["_id"]}, {"$set": {"sop_id": res.inserted_id, "updated_at": datetime.utcnow()}})
    return res.inserted_id

async def _assign_control_to_asset(db, asset_id: ObjectId, control_id: str) -> bool:
    # Idempotent: unique by (asset_id, control_id)
    now = datetime.utcnow()
    res = await db.policy_assignments.update_one(
        {"asset_id": asset_id, "control_id": control_id},
        {"$setOnInsert": {
            "asset_id": asset_id, "control_id": control_id,
            "status": "Proposed", "owner": None, "due_date": None, "last_verified_at": None,
            "created_at": now, "updated_at": now
        }},
        upsert=True
    )
    return res.upserted_id is not None

async def _gate_by_detections(det_list: List[Dict[str, Any]], min_sev: int) -> bool:
    if not det_list:
        return False
    return any(int(det.get("severity", 0)) >= min_sev for det in det_list)

async def run_policy_builder(db) -> Dict[str, Any]:
    """
    1) Load assets + recent detections (7d)
    2) Apply deterministic rules -> ensure control masters, SOPs, assignments
    3) Compute CSF coverage
    4) Update residual risk per asset (simple effectiveness model)
    5) Return summary {new_controls, policies_created, coverage:{...}, risk_items_updated}
    """
    assets = await _load_assets(db)
    det_map = await _load_recent_detections(db, days=7)

    new_controls: Set[str] = set()
    new_assignments = 0

    # Pseudo-asset "org" to trigger org-wide rules once
    if not any(a.get("_scope") == "org" for a in assets):
        assets = [{"_id": ObjectId(), "name": "ORG", "_scope": "org", "criticality": 5, "data": {"sensitivity": "High"}, "tags": ["ORG"]}] + assets

    for asset in assets:
        a_id = asset.get("_id")
        if isinstance(a_id, str):
            try: a_id = ObjectId(a_id)
            except: continue

        recent_dets = det_map.get(a_id, [])
        for rule in RULES:
            if not rule["when"](asset):
                continue
            # Optional detection gate
            gate = rule.get("gate")
            if gate and not await _gate_by_detections(recent_dets, gate.get("min_severity", 0)):
                continue

            for c in rule["controls"]:
                _id, master = await _ensure_control_master(db, c)
                await _ensure_sop(db, master)
                if await _assign_control_to_asset(db, a_id, c["control_id"]):
                    new_assignments += 1
                if c["control_id"] not in new_controls:
                    # consider "new control" if just created (no reliable upsert feedback here, but fine for MVP)
                    new_controls.add(c["control_id"])

    # Coverage by CSF function/category/subcategory
    coverage = await compute_csf_coverage(db)

    # Residual risk update (per asset & linked risk_items)
    risk_items_updated = await update_residual_risk_for_assets(db, EFFECTIVENESS_BY_STATUS)

    summary = {
        "new_controls": len(new_controls),
        "policies_created": 0,  # none in MVP
        "coverage": coverage,
        "risk_items_updated": risk_items_updated
    }
    return summary

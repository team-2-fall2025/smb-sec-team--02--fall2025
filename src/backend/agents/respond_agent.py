from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from bson import ObjectId
from db.mongo import db  # this should be your AsyncIOMotorDatabase

import requests

SLACK_WEBHOOK_URL = "XXXXX"  # 你的 webhook



incident_evidence_col = db["incident_evidence"]


async def add_incident_evidence(incident_id: ObjectId, payload: Dict[str, Any]):      # step 5
    """
    Add metadata-only evidence entry.
    File upload is optional; metadata is required.
    """
    now = datetime.utcnow()

    # Required fields
    required = ["type", "location", "submitted_by"]
    for f in required:
        if f not in payload:
            raise ValueError(f"Missing required field: {f}")

    doc = {
        "incident_id": incident_id,
        "type": payload["type"],
        "location": payload["location"],
        "hash": payload.get("hash"),
        "submitted_by": payload["submitted_by"],
        "submitted_at": now,
        "chain_of_custody": payload.get("chain_of_custody", []),
    }

    result = await incident_evidence_col.insert_one(doc)

    # timeline event
    await incident_timeline_col.insert_one(
        {
            "incident_id": incident_id,
            "ts": now,
            "actor": payload["submitted_by"],
            "event_type": "evidence",
            "detail": {
                "type": payload["type"],
                "location": payload["location"],
            },
        }
    )

    return result.inserted_id



async def send_incident_notification(incident: Dict[str, Any]):     # step 4
    """
    Send Slack/Webhook alert and log a comms event to the timeline.
    """
    message = (
        f"[{incident.get('severity')}] New Incident {incident.get('_id')} "
        f"Asset: {incident.get('primary_asset_id')} "
        f"Phase: {incident.get('status')} "
        f"SLA Due: {incident.get('sla_due_at')}"
    )

    # Send Slack message
    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": message})
    except Exception as e:
        print("Slack send failed:", e)

    # Store comms event in timeline
    await incident_timeline_col.insert_one(
        {
            "incident_id": incident["_id"],
            "ts": datetime.utcnow(),
            "actor": "system",
            "event_type": "comms",
            "detail": {
                "message": message,
                "channel": "slack",
            },
        }
    )



# ---- Collections (Motor) ----
incidents_col = db["incidents"]
incident_tasks_col = db["incident_tasks"]
incident_timeline_col = db["incident_timeline"]
detections_col = db["detections"]  # adjust name if your collection is different

# ---- Config ----

SLA_HOURS: Dict[str, int] = {
    "P1": 4,
    "P2": 8,
    "P3": 24,
    "P4": 72,
}

# ---- Incident phases & allowed transitions ----

INCIDENT_PHASES = [
    "Open",
    "Triage",
    "Containment",
    "Eradication",
    "Recovery",
    "Closed",
]

ALLOWED_TRANSITIONS = {
    "Open": {"Triage"},
    "Triage": {"Containment"},
    "Containment": {"Eradication"},
    "Eradication": {"Recovery"},
    "Recovery": {"Closed"},
}


def compute_sla_status(now: datetime, opened_at: datetime, sla_due_at: datetime) -> str:
    """
    Return: "ok" | "at_risk" | "breached"
    - breached: now >= sla_due_at
    - at_risk: less than 25% of SLA window time remaining
    - ok: otherwise
    """
    total = (sla_due_at - opened_at).total_seconds()
    remaining = (sla_due_at - now).total_seconds()

    if total <= 0:
        return "breached"
    if remaining <= 0:
        return "breached"

    if remaining / total < 0.25:
        return "at_risk"

    return "ok"

def severity_to_sla(severity: str) -> timedelta:
    hours = SLA_HOURS.get(severity, 24)
    return timedelta(hours=hours)


# --------- Helpers for dedup / grouping ---------


def _build_dedup_key(det: Dict[str, Any]) -> Dict[str, str]:
    """
    What we consider 'same incident'.
    Adjust to match your detection schema.
    """
    asset_id = det.get("asset_id")
    indicator = det.get("indicator")
    source = det.get("source")

    return {
        "asset_id": str(asset_id) if asset_id is not None else "",
        "indicator": indicator or "",
        "source": source or "",
    }


async def find_existing_incident(
    dedup_key: Dict[str, str],
    window_hours: int = 12,
) -> Optional[Dict[str, Any]]:
    """
    Check if there is an open (non-Closed) incident within the time window
    that matches the same dedup key.
    """
    now = datetime.utcnow()
    window_start = now - timedelta(hours=window_hours)

    q = {
        "status": {"$ne": "Closed"},
        "dedup_key.asset_id": dedup_key["asset_id"],
        "dedup_key.indicator": dedup_key["indicator"],
        "dedup_key.source": dedup_key["source"],
        "opened_at": {"$gte": window_start},
    }
    return await incidents_col.find_one(q)


# --------- Playbook task generation ---------


async def _generate_playbook_tasks(incident_id: ObjectId, severity: str) -> None:
    """
    Very simple phase-based tasks for MVP.
    You can change titles later without breaking the rest of the code.
    """
    now = datetime.utcnow()
    base_due = now + timedelta(hours=2)

    templates = [
        ("Triage", "Review detection details and confirm scope on affected asset(s)."),
        ("Containment", "Contain the incident (isolate host/account, block indicators)."),
        ("Eradication", "Remove malicious artifacts and confirm systems are clean."),
        ("Recovery", "Restore services and monitor for recurrence."),
        ("Closed", "Document incident, root cause, and lessons learned."),
    ]

    docs: List[Dict[str, Any]] = []
    for order, (phase, title) in enumerate(templates, start=1):
        docs.append(
            {
                "incident_id": incident_id,
                "phase": phase,
                "title": title,
                "assignee": None,
                "due_at": base_due,
                "status": "Open",
                "notes": "Auto-generated task (Respond MVP)",
                "order": order,
                "created_at": now,
                "updated_at": now,
            }
        )

    if docs:
        await incident_tasks_col.insert_many(docs)


# --------- Incident creation / attachment ---------


async def create_incident_from_detection(det: Dict[str, Any]) -> ObjectId:    # step 6
    """
    Create a new incident document from a detection.
    """
    now = datetime.utcnow()
    severity = det.get("severity", "P3")
    dedup_key = _build_dedup_key(det)

    sla_due_at = now + severity_to_sla(severity)
    sla_status = compute_sla_status(now, now, sla_due_at)

    title = (
        det.get("title")
        or det.get("summary")
        or f"Auto incident for detection {str(det.get('_id'))}"
    )

    incident_doc: Dict[str, Any] = {
        "asset_refs": [det.get("asset_id")] if det.get("asset_id") else [],

        "title": title,
        "severity": severity,
        "status": "Triage",
        "opened_at": now,
        "updated_at": now,
        "closed_at": None,
        "owner": None,
        "sla_due_at": sla_due_at,
        "sla_status": sla_status,
        "primary_asset_id": det.get("asset_id"),
        "detection_refs": [det["_id"]],
        "summary": "",
        "root_cause": "",
        "lessons_learned": "",
        "tags": det.get("tags", []),
        "risk_item_refs": det.get("risk_item_refs", []),
        "dedup_key": {
            "asset_id": dedup_key["asset_id"],
            "indicator": dedup_key["indicator"],
            "source": dedup_key["source"],
            "window_start": now,
        },
    }

    result = await incidents_col.insert_one(incident_doc)
    incident_id = result.inserted_id

    # Timeline: opened
    await incident_timeline_col.insert_one(
        {
            "incident_id": incident_id,
            "ts": now,
            "actor": "system",
            "event_type": "opened",
            "detail": {
                "note": "Incident auto-opened by Respond agent.",
                "detection_id": str(det["_id"]),
            },
        }
    )

    # Generate tasks
    await _generate_playbook_tasks(incident_id, severity)

    # --- NEW: send notification ---
    incident_doc["_id"] = incident_id
    await send_incident_notification(incident_doc)

    return incident_id

async def link_asset_to_incident(incident_id: ObjectId, asset_id: str):
    await incidents_col.update_one(
        {"_id": incident_id},
        {"$addToSet": {"asset_refs": asset_id}}
    )

async def link_risk_to_incident(incident_id: ObjectId, risk_id: str):
    await incidents_col.update_one(
        {"_id": incident_id},
        {"$addToSet": {"risk_item_refs": risk_id}}
    )


async def attach_detection_to_incident(   # step 6
    incident: Dict[str, Any],
    det: Dict[str, Any],
) -> None:
    """
    Attach a detection to an existing incident (no new incident).
    """
    now = datetime.utcnow()
    await incidents_col.update_one(
        {"_id": incident["_id"]},
        {
            "$addToSet": {"detection_refs": det["_id"]},
            "$set": {"updated_at": now},
        },
    )

    await incident_timeline_col.insert_one(
        {
            "incident_id": incident["_id"],
            "ts": now,
            "actor": "system",
            "event_type": "link_added",
            "detail": {
                "note": "New detection attached by Respond agent.",
                "detection_id": str(det["_id"]),
            },
        }
    )


# --------- Main Respond Agent function (async) ---------


async def run_respond_agent(limit: int = 50) -> Dict[str, int]:
    """
    MVP Respond Agent (async):

    - Look for detections that aren't yet linked to an incident
      (incident_handled != True).
    - For each detection:
        * Build dedup key
        * If existing open incident in window -> attach
        * Else -> create new incident
    - Mark detection as handled.
    - Return counters.
    """

    counters = {
        "incidents_opened": 0,
        "incidents_attached": 0,
        "alerts_sent": 0,           # "notifications", for MVP == opened
        "suppressed_duplicates": 0, # for now == attached
    }

    # Async cursor -> to_list(...)
    detections: List[Dict[str, Any]] = await detections_col.find(
        {"incident_handled": {"$ne": True}}
    ).to_list(length=limit)

    if not detections:
        return counters

    for det in detections:
        dedup_key = _build_dedup_key(det)
        existing = await find_existing_incident(dedup_key)

        if existing:
            await attach_detection_to_incident(existing, det)
            counters["incidents_attached"] += 1
            counters["suppressed_duplicates"] += 1
        else:
            await create_incident_from_detection(det)
            counters["incidents_opened"] += 1

        # Mark detection as handled so we don't re-open incidents on next run
        await detections_col.update_one(
            {"_id": det["_id"]},
            {"$set": {"incident_handled": True}},
        )

    # For MVP: each new incident → one alert
    counters["alerts_sent"] = counters["incidents_opened"]

    return counters

async def update_incident_status(
    incident_id: ObjectId,
    new_status: str,
    actor: str | None = None,
) -> Dict[str, Any]:
    incident = await incidents_col.find_one({"_id": incident_id})
    if not incident:
        raise ValueError("Incident not found")

    current = incident.get("status", "Open")

    if new_status not in INCIDENT_PHASES:
        raise ValueError(f"Invalid status {new_status}")

    # allow no-op: same status is OK
    if new_status == current:
        return incident

    allowed_next = ALLOWED_TRANSITIONS.get(current, set())
    if new_status not in allowed_next:
        return incident
        # This code will has the error if we broke the rules
        # raise ValueError(f"Transition {current} -> {new_status} not allowed")

    # derive actor: prefer owner, else "user"
    if not actor:
        actor = incident.get("owner") or "user"

    now = datetime.utcnow()
    opened_at = incident.get("opened_at", now)
    sla_due_at = incident.get("sla_due_at", now)
    sla_status = compute_sla_status(now, opened_at, sla_due_at)

    update_doc: Dict[str, Any] = {
        "status": new_status,
        "updated_at": now,
        "sla_status": sla_status,
    }
    if new_status == "Closed":
        update_doc["closed_at"] = now

    await incidents_col.update_one(
        {"_id": incident_id},
        {"$set": update_doc},
    )

    await incident_timeline_col.insert_one(
        {
            "incident_id": incident_id,
            "ts": now,
            "actor": actor,  # now just the resolved value
            "event_type": "status_change",
            "detail": {
                "from": current,
                "to": new_status,
            },
        }
    )

    updated = await incidents_col.find_one({"_id": incident_id})
    return updated
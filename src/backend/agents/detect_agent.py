import os
from typing import List, Dict, Any, Iterable
from itertools import groupby
from operator import itemgetter
from datetime import datetime, timedelta

from dotenv import load_dotenv
import httpx
from db.mongo import db
from db.models import Detection


load_dotenv()

TIME_MULTIPLIER = int(os.getenv("TIME_MULTIPLIER", "1"))
TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")
FRONTEND_URL = os.getenv("FRONTEND_URL")

# --- Source bias & TTP keyword map (tune later) ---
SOURCE_BIAS = {
    "shodan": 1,
    "censys": 1,
    "otx": 0,
    "greynoise": 0,
    "abuseipdb": -1,
    "vt": 0,
}

TTP_KEYWORDS = {
    # Initial Access
    "brute": ["T1110"],
    "bruteforce": ["T1110"],
    "password spray": ["T1110"],
    "exploit": ["T1190", "T1210", "T1211"],
    "vulnerability": ["T1190"],
    "cve": ["T1190"],
    "phishing": ["T1566"],
    "spear phishing": ["T1566.001", "T1566.002", "T1566.003"],
    "malware": ["T1204", "T1204.001", "T1204.002", "T1204.003"],
    "ransomware": ["T1486"],
    "trojan": ["T1204.002"],
    
    # Discovery & Reconnaissance
    "scan": ["T1046", "T1190", "T1595"],
    "scanning": ["T1046", "T1190", "T1595"],
    "port scan": ["T1046"],
    "network scan": ["T1046", "T1595.001"],
    "recon": ["T1595"],
    "reconnaissance": ["T1595"],
    "enumeration": ["T1087", "T1069", "T1018", "T1046"],
    "host discovery": ["T1018"],
    "service discovery": ["T1046"],
    
    # Command and Control
    "c2": ["T1071", "T1090", "T1095", "T1105"],
    "command and control": ["T1071", "T1090", "T1095", "T1105"],
    "beacon": ["T1071"],
    "dns": ["T1071.004", "T1090.004"],
    "http": ["T1071.001"],
    "https": ["T1071.001"],
    "web shell": ["T1505.003"],
    "reverse shell": ["T1059.003", "T1105"],
    
    # Persistence
    "persistence": ["T1136", "T1547", "T1053", "T1505"],
    "backdoor": ["T1505", "T1136"],
    "scheduled task": ["T1053", "T1053.005"],
    "cron": ["T1053.003"],
    "startup": ["T1547"],
    
    # Lateral Movement
    "lateral": ["T1021", "T1550"],
    "psexec": ["T1021.002"],
    "winrm": ["T1021.006"],
    "ssh": ["T1021.004"],
    "rdp": ["T1021.001"],
    "smb": ["T1021.002"],
    "wmi": ["T1047"],
    "pass the hash": ["T1550.002"],
    "pass the ticket": ["T1550.003"],
    
    # Credential Access
    "credential": ["T1110", "T1003", "T1555", "T1552"],
    "password": ["T1110", "T1003", "T1555"],
    "hash": ["T1003", "T1550.002"],
    "kerberoast": ["T1558.003"],
    "asreproast": ["T1558.004"],
    "lsass": ["T1003.001"],
    "keylogger": ["T1056.001"],
    
    # Defense Evasion
    "evasion": ["T1027", "T1036", "T1112", "T1140"],
    "obfuscation": ["T1027", "T1140"],
    "encoding": ["T1132", "T1140"],
    "encryption": ["T1027", "T1573"],
    "bypass": ["T1218", "T1553", "T1562"],
    "disable": ["T1562", "T1562.001"],
    "uac": ["T1548.002"],
    "amsi": ["T1562.001"],
    
    # Collection & Exfiltration
    "exfil": ["T1041", "T1048", "T1020"],
    "exfiltration": ["T1041", "T1048", "T1020"],
    "data theft": ["T1041", "T1114", "T1115"],
    "upload": ["T1105"],
    "download": ["T1105"],
    "compress": ["T1560"],
    "archive": ["T1560"],
    "zip": ["T1560.001"],
    
    # Impact
    "destruction": ["T1485", "T1489"],
    "wipe": ["T1485"],
    "delete": ["T1485"],
    "encrypt": ["T1486"],
    "deface": ["T1491"],
    "resource hijack": ["T1496"],
    
    # Specific Protocols & Services
    "ldap": ["T1087.002"],
    "active directory": ["T1087.002", "T1482", "T1069.002"],
    "kerberos": ["T1558", "T1558.001", "T1558.002", "T1558.003"],
    "ntlm": ["T1552.004"],
    "ftp": ["T1071.002"],
    "smtp": ["T1071.003"],
    "icmp": ["T1095"],
    "tcp": ["T1071"],
    "udp": ["T1071"],
    
    # Specific Tools & Techniques
    "metasploit": ["T1588.001"],
    "cobalt strike": ["T1588.001"],
    "mimikatz": ["T1003.001"],
    "bloodhound": ["T1595.001"],
    "responder": ["T1557.001"],
    "empire": ["T1588.001"],
    "powershell": ["T1059.001"],
    "cmd": ["T1059.003"],
    "python": ["T1059.006"],
    
    # Network-based Indicators
    "tor": ["T1090.003", "T1188"],
    "proxy": ["T1090", "T1188"],
    "vpn": ["T1090.002"],
    "tunnel": ["T1572"],
    "domain fronting": ["T1090.004"],
    
    # System Artifacts
    "registry": ["T1112", "T1547.001"],
    "process injection": ["T1055"],
    "dll injection": ["T1055.001"],
    "code signing": ["T1553.002"],
    "certificate": ["T1588.003"],
}

def match_ttp(text: str) -> List[str]:
    text = text.lower()
    return [ttp for keyword, ttps in TTP_KEYWORDS.items() for ttp in ttps if keyword in text]

def group_by_dedup_key(intel_events: List[Dict[str, Any]]) -> Iterable[List[Dict[str, Any]]]:
    """
    Group intel by (asset_id, indicator, source)
    """
    if not intel_events:
        return
    sorted_events = sorted(
        intel_events,
        key=itemgetter("asset_id", "indicator", "source")
    )
    for _, group in groupby(sorted_events, key=itemgetter("asset_id", "indicator", "source")):
        yield list(group)

def compute_detection(group: List[Dict[str, Any]]) -> Detection:
    """
    Compute severity, confidence, TTPs, and analyst note from a group of intel events.
    """
    if not group:
        raise ValueError("Empty group")

    base = group[0]
    source = base["source"]
    indicator = base["indicator"]
    asset_id = base["asset_id"]
    # Severity
    intel_sev = base.get("severity", 3)
    bias = SOURCE_BIAS.get(source, 0)
    severity = max(1, min(5, int(intel_sev) + bias))

    # Confidence
    confidence = 60
    if len(group) > 1:
        confidence += 20
    confidence = min(100, confidence)

    # TTPs
    summary = base.get("summary", "") + " " + indicator
    ttp = match_ttp(summary)

    # Analyst note
    # note = f"{severity}-sev {source} activity on ({indicator})"
    note = f"{severity}-sev {source} activity on {asset_id} ({indicator})"
    
    if ttp:
        note += f". TTPs: {', '.join(ttp)}"
    note += ". Review logs and consider mitigation."
    note = note[:240]
    
    return Detection(
        asset_id=str(asset_id),
        source=source,
        indicator=indicator,
        severity=severity,
        confidence=confidence,
        ttp=ttp,
        analyst_note=note,
        first_seen=datetime.utcnow(),
        last_seen=datetime.utcnow(),
        hit_count=len(group),
        raw_ref={"intel_ids": [str(ev["_id"]) for ev in group]}
    )
    
async def create_or_update_risk_item(detection: Dict[str, Any]) -> None:
    """
    Upsert a risk item if detection meets threshold:
    - severity >= 4 OR (severity >= 3 AND confidence >= 70)
    """
    sev = detection["severity"]
    conf = detection["confidence"]

    if not (sev >= 4 or (sev >= 3 and conf >= 70)):
        return  # No risk

    asset_id = detection["asset_id"]
    
    # Convert asset_id to ObjectId if it's a string
    if isinstance(asset_id, str):
        from bson import ObjectId
        try:
            asset_id = ObjectId(asset_id)
        except Exception:
            print(f"Invalid asset_id: {asset_id}")
            return

    # Await the async find_one operation
    asset = await db["assets"].find_one({"_id": asset_id})

    if not asset:
        print(f"Asset not found: {asset_id}")
        return

    title = f"Detection: {detection['source']} {detection['indicator']}"
    
    criticality = asset.get("criticality", 3)  # 1-5
    score = int(criticality) * int(sev)

    # Upsert key
    upsert_filter = {"asset_id": asset_id, "title": title}

    # New or updated data
    update_data = {
        "$set": {
            "status": "Open",
            "owner": asset.get("owner", "security-team@smb.com"),
            "due": datetime.utcnow() + timedelta(days=14),
            "score": score,
            "updated_at": datetime.utcnow()
        },
        "$setOnInsert": {
            "title": title,
            "asset_id": asset_id,
            "created_at": datetime.utcnow()
        }
    }

    # Await the async update operation
    await db["risk_items"].update_one(
        upsert_filter,
        update_data,
        upsert=True
    )

    # Update asset risk_score (7-day max severity)
    seven_days_ago = datetime.utcnow() - timedelta(days=7 * TIME_MULTIPLIER)
    recent_high = await db["detections"].find_one(
        {"asset_id": asset_id, "last_seen": {"$gte": seven_days_ago}},
        sort=[("severity", -1)]
    )
    
    if recent_high:
        max_sev = recent_high["severity"]
        asset_risk_score = int(max_sev) * int(criticality)
        await db["assets"].update_one(
            {"_id": asset_id},
            {"$set": {"risk_score": asset_risk_score}}
        )
      
def send_teams_alert(detection: dict, asset: dict) -> bool:
    """
    Sends URGENT Teams MessageCard with @channel mention for high-severity.
    Triggers push notification.
    """
    try:
        link = f"{FRONTEND_URL}/detection/{detection['_id']}"

        # Determine urgency
        is_urgent = detection["severity"] >= 4
        theme_color = "d32f2f" if is_urgent else "f57c00"
        mention = "@channel" if is_urgent else ""

        card = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_color,
            "summary": "URGENT: New Security Detection" if is_urgent else "New Detection",
            "title": f"{'[URGENT] ' if is_urgent else ''}New Detection: {detection['indicator']}",
            "sections": [{
                "activityTitle": f"**{mention}** Asset: **{asset.get('name', 'Unknown')}**",
                "activitySubtitle": f"Severity: **{detection['severity']}/5** | Confidence: {detection['confidence']}%",
                "facts": [
                    {"name": "Indicator", "value": f"`{detection['indicator']}`"},
                    {"name": "TTPs", "value": ", ".join(detection.get("ttp", [])) or "None"},
                    {"name": "Analyst Note", "value": detection.get("analyst_note", "N/A")},
                ],
                "markdown": True
            }],
            "potentialAction": [{
                "@type": "OpenUri",
                "name": "View in Dashboard",
                "targets": [{"os": "default", "uri": link}]
            }]
        }

        response = httpx.post(TEAMS_WEBHOOK_URL, json=card, timeout=10.0)
        if response.status_code == 200:
            print(f"Teams URGENT alert sent: {detection['indicator']} (severity {detection['severity']})")
            return True
        else:
            print(f"Teams alert failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"Teams alert error: {e}")
        return False
    

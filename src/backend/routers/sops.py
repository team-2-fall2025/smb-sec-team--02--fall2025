#!/usr/bin/env python3
import os
from datetime import datetime
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "smbsec")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]


# =======================================================
#  Family-based SOP Templates
# =======================================================

def sop_access(control):
    """AC-xx 访问控制类控制措施 SOP"""
    cid = control["control_id"]
    title = control.get("title", "")
    return f"""
# SOP: {title} ({cid})
**Scope:** All user accounts and access-controlled systems  
**Owner:** Security / IAM  
**Cadence:** Quarterly review  

## Steps
1. Review all active user accounts and validate least-privilege.
2. Disable or remove stale or unused accounts (>90 days).
3. Audit group memberships for privileged roles.
4. Validate access approval workflow documentation.
5. Reconcile HR onboarding/offboarding logs with account records.
6. Document exceptions and obtain approvals.

## Evidence to collect
- User list export  
- Group membership report  
- Privileged access log  

## Success criteria
- No unauthorized or stale accounts  
- Privileged roles limited to approved users  
""".strip()


def sop_identity(control):
    """IA-xx 身份验证 / MFA 类 SOP"""
    cid = control["control_id"]
    title = control.get("title", "")
    return f"""
# SOP: {title} ({cid})
**Scope:** Identity Provider, VPN, Admin Portals  
**Owner:** IAM / NetOps  
**Cadence:** One-time + Quarterly verification  

## Steps
1. Enable MFA for all remote access systems.
2. Enforce MFA for privileged roles in IdP.
3. Validate break-glass accounts follow compensating controls.
4. Review MFA enrollment logs for anomalies.
5. Perform test login with normal user + privileged user.
6. Document exceptions and obtain approval.

## Evidence to collect
- IdP policy screenshot  
- VPN gateway config  
- Login test logs  

## Success criteria
- MFA challenge is enforced for all users  
- Privileged access requires MFA  
""".strip()


def sop_security(control):
    """SC-xx 安全保护 / 加密 / 传输保护类 SOP"""
    cid = control["control_id"]
    title = control.get("title", "")
    return f"""
# SOP: {title} ({cid})
**Scope:** All systems handling sensitive data  
**Owner:** Security Engineering  
**Cadence:** Annual + after major config change  

## Steps
1. Enforce encryption in transit (TLS 1.2+).
2. Ensure encryption at rest for storage systems.
3. Validate key rotation policies.
4. Review cipher suite configuration.
5. Test certificate expiration monitoring.
6. Document exceptions and compensating controls.

## Evidence to collect
- TLS config screenshot  
- Storage encryption settings  
- Key rotation logs  

## Success criteria
- All sensitive data is encrypted in transit and at rest  
""".strip()


def sop_config(control):
    """CM-xx 配置管理类 SOP"""
    cid = control["control_id"]
    title = control.get("title", "")
    return f"""
# SOP: {title} ({cid})
**Scope:** All servers, endpoints, and cloud workloads  
**Owner:** IT Operations  
**Cadence:** Monthly  

## Steps
1. Apply baseline configuration according to CIS / vendor benchmarks.
2. Validate OS patch levels are up to date.
3. Review configuration drift reports.
4. Remediate unauthorized configuration changes.
5. Update configuration documentation.

## Evidence to collect
- Patch report  
- Configuration drift log  
- Baseline compliance screenshot  

## Success criteria
- No high-risk configuration drift  
- Systems meet baseline security configuration  
""".strip()


def sop_logging(control):
    """AU-xx 审计 / 日志类 SOP"""
    cid = control["control_id"]
    title = control.get("title", "")
    return f"""
# SOP: {title} ({cid})
**Scope:** SIEM, system audit logs, cloud logs  
**Owner:** Security Operations  
**Cadence:** Daily + Weekly review  

## Steps
1. Ensure auditing is enabled for authentication, privilege use, and system events.
2. Validate logs flow correctly into SIEM.
3. Review alerts for anomalous behavior.
4. Check log retention settings meet policy.
5. Address missing or misconfigured log sources.

## Evidence to collect
- SIEM ingestion report  
- Log retention policy screenshot  

## Success criteria
- Auditing enabled and logs continuously ingested  
""".strip()


def sop_incident(control):
    """IR-xx 事件响应 SOP"""
    cid = control["control_id"]
    title = control.get("title", "")
    return f"""
# SOP: {title} ({cid})
**Scope:** All security events and incidents  
**Owner:** Security Incident Response Team  
**Cadence:** Per-incident + quarterly tabletop  

## Steps
1. Triage incoming alerts based on severity.
2. Contain affected systems (network isolation, credential resets).
3. Collect forensic evidence.
4. Perform root-cause analysis.
5. Implement lessons learned and update playbooks.

## Evidence to collect
- Incident ticket  
- Containment logs  
- RCA documentation  

## Success criteria
- Incident contained and resolved  
- Follow-up actions completed  
""".strip()


def sop_generic(control):
    """其他类别控制的通用 SOP"""
    cid = control["control_id"]
    title = control.get("title", "")
    return f"""
# SOP: {title} ({cid})
**Scope:** Applicable systems and processes  
**Owner:** Security / IT  
**Cadence:** Periodic  

## Steps
1. Review relevant configurations for this control.
2. Validate enforcement on assets.
3. Collect required evidence.
4. Document exceptions.
5. Update control status.

## Evidence to collect
- Screenshots  
- Config exports  

## Success criteria
- Control implemented and verifiable  
""".strip()


# =======================================================
#  Template Router
# =======================================================

def generate_sop(control):
    family = control.get("family", "").upper()

    if family == "AC":
        return sop_access(control)
    elif family == "IA":
        return sop_identity(control)
    elif family == "SC":
        return sop_security(control)
    elif family == "CM":
        return sop_config(control)
    elif family == "AU":
        return sop_logging(control)
    elif family == "IR":
        return sop_incident(control)
    else:
        return sop_generic(control)


# =======================================================
#  Main Execution
# =======================================================

def run_sop_generation():
    controls = list(db.controls.find({"sop_id": {"$exists": False}}))
    results = []

    for control in controls:
        md = generate_sop(control)
        sop_id = db.sops.insert_one({
            "control_id": control["control_id"],
            "markdown": md,
            "created_at": datetime.utcnow()
        }).inserted_id

        db.controls.update_one(
            {"_id": control["_id"]},
            {"$set": {"sop_id": sop_id}}
        )

        results.append(f"SOP created for {control['control_id']}")

    return {
        "count": len(results),
        "details": results
    }



# def main():
#     controls = list(db.controls.find({"sop_id": {"$exists": False}}))
#     print(f"Found {len(controls)} controls requiring SOPs")
#
#     for control in controls:
#         md = generate_sop(control)
#         sop_id = db.sops.insert_one({
#             "control_id": control["control_id"],
#             "markdown": md,
#             "created_at": datetime.utcnow()
#         }).inserted_id
#
#         db.controls.update_one(
#             {"_id": control["_id"]},
#             {"$set": {"sop_id": sop_id}}
#         )
#
#         print(f"[OK] SOP created for {control['control_id']}")
#
#     print("[DONE] SOP generation complete.")


# if __name__ == "__main__":
#     main()

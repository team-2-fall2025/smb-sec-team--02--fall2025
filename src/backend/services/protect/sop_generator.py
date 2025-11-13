from typing import Dict

def build_sop_for_control(control: Dict) -> str | None:
    cid = control.get("control_id")
    title = control.get("title", "")
    csf = control.get("csf_category", "")
    # Minimal templating by control_id; expand as needed
    if cid == "IA-2":
        return _sop_mfa(title, cid, csf)
    if cid == "SC-13":
        return _sop_crypto(title, cid, csf)
    if cid == "SC-28":
        return _sop_at_rest(title, cid, csf)
    if cid == "SI-4":
        return _sop_monitoring(title, cid, csf)
    if cid == "AU-6":
        return _sop_audit_review(title, cid, csf)
    # Fallback generic SOP
    return _sop_generic(title, cid, csf)

def _sop_header(title: str, cid: str, csf: str) -> str:
    return f"# SOP: {title} ({cid}, {csf})\n**Scope:** Org / internet-facing systems\n**Owner:** Security\n**Cadence:** One-time + quarterly verification\n"

def _sop_generic(title: str, cid: str, csf: str) -> str:
    return _sop_header(title, cid, csf) + """
**Steps:**
1. Define scope and stakeholders.
2. Configure control per vendor guidance.
3. Validate on pilot system.
4. Roll out to full scope.
5. Document exceptions and compensating controls.
**Evidence to collect:** Config export, screenshots, test logs.
**Success criteria:** Control enforced and observable in logs.
"""

def _sop_mfa(title, cid, csf) -> str:
    return _sop_header(title, cid, csf) + """
**Steps:**
1. Enable MFA in IdP for all remote access portals and admin roles.
2. Enforce conditional access for high-risk sign-ins.
3. Require break-glass account with hardware token; store securely.
4. Test with non-admin and admin users; confirm challenge.
5. Roll out to all VPN/gateway/admin consoles.
**Evidence to collect:** IdP policy screenshot, VPN config export, test logs.
**Success criteria:** MFA challenge for remote/admin logins; logs confirm enforcement.
"""

def _sop_crypto(title, cid, csf) -> str:
    return _sop_header(title, cid, csf) + """
**Steps:**
1. Define crypto standards (TLS 1.2+, AES-256 where applicable).
2. Enforce TLS on all external endpoints; disable weak ciphers.
3. Centralize key management in KMS; rotate keys every 180 days.
4. Validate via SSL scan and config checks.
**Evidence to collect:** KMS policy, TLS scan report.
**Success criteria:** All endpoints pass TLS policy; keys managed in KMS.
"""

def _sop_at_rest(title, cid, csf) -> str:
    return _sop_header(title, cid, csf) + """
**Steps:**
1. Enable default encryption for disks/volumes and object storage.
2. Enforce encryption policy in IaC/templates.
3. Verify encryption on existing volumes; migrate non-compliant.
4. Monitor drift with periodic scans.
**Evidence to collect:** Cloud policy export, encryption status logs.
**Success criteria:** 100% storage encrypted; drift alerts configured.
"""

def _sop_monitoring(title, cid, csf) -> str:
    return _sop_header(title, cid, csf) + """
**Steps:**
1. Route endpoint, auth, and network logs to SIEM.
2. Implement detections for brute-force, privilege escalation, and malware.
3. Triage runbook: classify sev, assign owner, track in ticketing.
4. Weekly tuning of false positives.
**Evidence to collect:** SIEM rule exports, alert screenshots, tickets.
**Success criteria:** Detections fire on test scenarios; MTTR improving.
"""

def _sop_audit_review(title, cid, csf) -> str:
    return _sop_header(title, cid, csf) + """
**Steps:**
1. Define log retention and review cadence (weekly).
2. Review admin actions, failed logins, and changes to critical systems.
3. Escalate anomalies per incident workflow.
4. Archive review results for 1 year.
**Evidence to collect:** Review checklist, tickets, exported reports.
**Success criteria:** Reviews completed per cadence; anomalies tracked to closure.
"""

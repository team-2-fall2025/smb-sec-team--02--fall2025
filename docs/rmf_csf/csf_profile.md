# SMB CSF Profile --- Dr. Lin's Dental Clinic (Week 1 Submission)

## Org Snapshot

-   **Sector:** Healthcare (Dental clinic)
-   **Size:** 6 employees, 1 site; cloud‑first EHR; limited in‑house IT
-   **Regulatory Context:** HIPAA/HITECH; PCI DSS for card payments
-   **Environment:** Front‑desk laptop, Wi‑Fi router, local backup
    server, card reader, cloud EHR/portal
-   **Risk Appetite:** **Low** --- patient safety, PHI confidentiality,
    and uptime are mission‑critical

## Crown Jewels (Top 4)

1.  **Patient PHI** in cloud EHR (records, images, treatment history)
2.  **Identity & Access** (SSO/MFA, staff credentials, VPN/admin
    accounts)
3.  **Payments & Billing** (card reader, merchant portal, invoice data)
4.  **Backups & Recovery Material** (backup server, restore keys,
    RPO/RTO docs)

## NIST CSF Functions --- Focus Areas

-   **Identify (ID):** Asset inventory (HW/SW/Cloud), data
    classification for PHI, vendor risk, business impact/RTO/RPO
-   **Protect (PR):** MFA everywhere, least privilege, patching/cadence,
    endpoint hardening, secrets handling, EDR/AV, secure Wi‑Fi
-   **Detect (DE):** Centralize auth logs, alert failed
    logins/anomalies, basic threat intel (KEV/OTX), integrity monitoring
-   **Respond (RS):** Playbooks (phishing, ransomware, account
    compromise), comms tree, evidence preservation, legal/regulatory
    steps
-   **Recover (RC):** Tested backups, restore procedures, tabletop
    exercises, lessons learned & control updates

## Current vs Target Profile (High‑Level)

| Function   | Current                                          | Target                                                   | Priority |
|------------|---------------------------------------------------------------|------------------------------------------------------------------------------|----------|
| **Identify** | Informal inventory; no PHI data map; vendor risk ad-hoc       | Living asset list; PHI data flow diagram; third-party risk checklist per vendor | **P1**   |
| **Protect**  | MFA not enforced on all portals; weak Wi-Fi config; inconsistent patching; shared local admin | Enforce MFA; harden Wi-Fi (WPA3, guest VLAN); monthly KEV-driven patching; remove local admin; password policy | **P1**   |
| **Detect**   | Logs siloed in apps; no alerting; no baseline                 | Route auth/sys logs; rules for brute-force, geo-anomaly; weekly review; KEV watch | **P1**   |
| **Respond**  | No documented playbooks; unclear roles                       | 1-page runbooks (phish, ransomware, lost laptop); comms tree; evidence checklist | **P2**   |
| **Recover**  | Backups exist but untested; unknown RPO/RTO                   | Quarterly restore tests; defined RPO=24h, RTO=8h; recovery checklist             | **P1**   |

## OSINT / External Feeds (≥3)

-   **CISA KEV (KEVin API):** Automate checks for newly exploited CVEs
    and vendor filters; drive KEV-priority patching and emergency
    advisories.
-   **AlienVault OTX:** Pull Pulse IOCs for phishing/malware campaigns;
    seed blocklists/detections and watchlists.
-   **NVD CVE Search API:** Track CVE/CVSS changes and affected
    products; correlate with your asset inventory for risk scoring.
-   **IPQuery.io:** Enrich suspicious IPs (ASN, geolocation, risk
    signals) to reduce false positives and prioritize triage.
-   **IPInfoDB:** Secondary IP intel source (geo/host data) to
    corroborate enrichment and catch data gaps.

## Top Risks

-   **Phishing → credential theft → SSO/EHR abuse** (Initial Access →
    Credential Access → Impact)
-   **Unpatched edge/VPN or router → KEV exploit → lateral movement**
    (Execution/Privilege Escalation)
-   **Secret leakage in repos or workstation** → cloud portal misuse
    (Discovery/Exfiltration)

## Near‑Term Controls & Tasks

-   **Access:** Enforce MFA on EHR/portal/email; disable shared
    accounts; least privilege
-   **Hardening:** Wi‑Fi WPA3, separate guest VLAN; disable WPS; rotate
    admin creds; encrypt laptops; auto‑lock screens
-   **Patching:** Monthly cycle + **KEV‑driven out‑of‑band** for
    exploited vulns; firmware updates for router
-   **Detection:** Centralize minimal logs (auth, EDR, router); alerts
    on brute‑force, impossible travel, MFA fatigue
-   **Backups:** Verify scope; quarterly restore tests; document
    RPO/RTO; offline copy for ransomware resilience
-   **Awareness:** Phish simulation & 10‑minute micro‑training for
    front‑desk workflows

## Validation / Acceptance Criteria

-   Asset & data‑flow diagrams committed to `docs/` and referenced in
    runbooks
-   MFA enforced and verified for EHR/email/SSO; Wi‑Fi hardened &
    documented
-   KEV watch procedure and patch notes recorded monthly
-   At least **one** successful backup restore to a clean host
    (documented)
-   Detections generate a test alert (screenshot/log snippet) and weekly
    review notes

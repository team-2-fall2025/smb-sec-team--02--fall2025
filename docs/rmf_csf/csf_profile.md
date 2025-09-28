# SMB CSF Profile --- Dr. Lin's Dental Clinic (Draft)

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

  -----------------------------------------------------------------------
  Function          Current (Key      Target (This      Priority
                    Gaps)             Semester)         
  ----------------- ----------------- ----------------- -----------------
  **Identify**      Informal          Living asset      **P1**
                    inventory; no PHI list; PHI data    
                    data map; vendor  flow diagram;     
                    risk ad‑hoc       third‑party risk  
                                      checklist per     
                                      vendor            

  **Protect**       MFA not enforced  Enforce MFA;      **P1**
                    on all portals;   harden Wi‑Fi      
                    weak Wi‑Fi        (WPA3, guest      
                    config;           VLAN); monthly    
                    inconsistent      KEV‑driven        
                    patching; shared  patching; remove  
                    local admin       local admin;      
                                      password policy   

  **Detect**        Logs siloed in    Route auth/sys    **P1**
                    apps; no          logs; rules for   
                    alerting; no      brute‑force,      
                    baseline          geo‑anomaly;      
                                      weekly review;    
                                      KEV watch         

  **Respond**       No documented     1‑page runbooks   **P2**
                    playbooks;        (phish,           
                    unclear roles     ransomware, lost  
                                      laptop); comms    
                                      tree; evidence    
                                      checklist         

  **Recover**       Backups exist but Quarterly restore **P1**
                    untested; unknown tests; defined    
                    RPO/RTO           RPO=24h, RTO=8h;  
                                      recovery          
                                      checklist         
  -----------------------------------------------------------------------

> **Implementation Tier (aspiration):** Tier 1 (Partial) → **Tier 2
> (Risk‑Informed)** by semester end

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

> **Planned automations:** daily KEV ingest, weekly NVD diffs, on-demand
> IOC lookups from OTX; IP enrichers called inside playbooks/detections.

## Top Risks (Week‑1 Hypotheses)

-   **Phishing → credential theft → SSO/EHR abuse** (Initial Access →
    Credential Access → Impact)
-   **Unpatched edge/VPN or router → KEV exploit → lateral movement**
    (Execution/Privilege Escalation)
-   **Secret leakage in repos or workstation** → cloud portal misuse
    (Discovery/Exfiltration)

## Near‑Term Controls & Tasks (This Semester)

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

## Traceability to Repo

-   **Location:** `docs/rmf_csf/csf_profile.md`
-   **References:** `docs/runbooks/` (RS), `docs/diagrams/` (ID),
    `ops/patching/` (PR), `ops/logging/` (DE), `ops/backup-restore/`
    (RC)

# Protect Agent User Guide

The **Protect Agent** automatically recommends NIST 800-53 security controls based on your environment.

### How It Works

**Inputs**
- Asset inventory (criticality, tags, sensitivity)
- Open risk items
- Recent high-severity detections

**Outputs**
- Recommended NIST controls (e.g., IA-2 MFA, SC-28 encryption)
- Auto-generated SOPs (Standard Operating Procedures) in Markdown
- Policy assignments linking controls to specific assets
- Updated CSF coverage metrics

### How Coverage Is Calculated

Coverage = % of CSF subcategories addressed by at least one **Implemented** or **In-Progress** control.

- Protect coverage is shown prominently on the Dashboard
- All six CSF functions (Identify, Protect, Detect, Respond, Recover, Govern) are tracked
- Updated automatically when you change control status

### Triggering the Agent

Run manually via API (or nightly via scheduler):

```bash
curl -X POST http://localhost:8000/api/protect/run
# Detections Guide

## How Detections Are Created

The **Detect Agent** runs hourly (or manually via `POST /api/detect/run`) and processes `intel_events` from the last 24 hours.

### Steps:
1. **Group** intel by `(asset_id, indicator, source)` → deduplication key.
2. **For each group**:
   - **Severity**: `intel_sev + source_bias` (e.g., Shodan +1, OTX 0)
   - **Confidence**: 60 base + 20 if multi-source
   - **TTPs**: Keyword map (e.g., "scan" → T1190)
   - **Analyst Note**: Auto-generated triage note (<240 chars)
3. **Dedup Check**: If same key exists in 24h → increment `hit_count`
4. **Insert** new detection if not deduped

---

## Thresholds

| Action | Condition |
|------|-----------|
| **Create Risk Item** | `severity >= 4` OR `(severity >= 3 AND confidence >= 70)` |
| **Send Alert** | New detection meets above threshold |

---

## API Endpoints

- `GET /api/detections` – List with filters
- `GET /api/detections/{id}` – Detail (includes `asset_name`, `intel_samples`)
- `POST /api/detect/run` – Run agent manually

---

> **Triage Tip**: Use `/detections` → Filter `severity=4` → Click **View** → **Open Risk Item**
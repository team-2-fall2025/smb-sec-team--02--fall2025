#!/usr/bin/env python3
"""
STEP 3: CSF → 800-53 Mapping & Coverage Metrics Generator

功能：
1. 为每条 control 自动生成 CSF 映射（如不存在则补齐）
2. 自动构建 800-53 映射（基于 family，如 AC → AC-xx）
3. 生成 coverage metrics 写入 csf_metrics 集合

运行:
  python scripts/csf.py
"""

import os
from datetime import datetime
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "smbsec")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]


# ==========================================================
# 默认 CSF Category 与 NIST 800-53 family 映射（简化版）
# ==========================================================

FAMILY_TO_CSF = {
    "AC": ("Protect", "PR.AC"),
    "IA": ("Protect", "PR.AC"),
    "SC": ("Protect", "PR.DS"),
    "CM": ("Protect", "PR.IP"),
    "AU": ("Detect",  "DE.AE"),
    "IR": ("Respond", "RS.RP"),
}

# 由于你的 controls 中已有 subcategory，如 PR.AC-1，优先使用现成数据
# 如果没有，就自动生成 xx-1
def default_subcategory(csf_category):
    return f"{csf_category}-1"


# ==========================================================
# Step 1 — 为 control 补齐映射字段
# ==========================================================

def update_control_mappings():
    controls = list(db.controls.find({}))
    updated = 0

    for c in controls:
        family = c.get("family", "").upper()
        cid = c.get("control_id")

        if not family or not cid:
            continue

        # CSF Function / Category
        csf_func, csf_cat = FAMILY_TO_CSF.get(family, ("Identify", "ID.GOV"))

        # Subcategory
        csf_subcat = c.get("subcategory")
        if not csf_subcat:
            csf_subcat = default_subcategory(csf_cat)

        # 800-53 Mappings
        nist_ctrl = [cid.split("-")[0] + "-*"]  # 如 IA-*，SC-*，AC-*

        update_doc = {
            "csf_function": c.get("csf_function", csf_func),
            "csf_category": c.get("csf_category", csf_cat),
            "csf_subcategory": c.get("subcategory", csf_subcat),
            "nist_800_53": c.get("nist_800_53", nist_ctrl),
            "updated_at": datetime.utcnow()
        }

        db.controls.update_one({"_id": c["_id"]}, {"$set": update_doc})
        updated += 1

    print(f"[OK] Updated {updated} control mapping records.")


# ==========================================================
# Step 2 — 计算 CSF 覆盖率并写入 csf_metrics 集合
# ==========================================================

def generate_coverage_metrics():
    db.csf_metrics.drop()  # 重建

    pipeline = [
        {
            "$group": {
                "_id": "$csf_category",
                "csf_function": {"$first": "$csf_function"},
                "total": {"$sum": 1},
                "implemented": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$implementation_status", "Implemented"]},
                            1,
                            0
                        ]
                    }
                }
            }
        }
    ]

    results = list(db.controls.aggregate(pipeline))
    inserted = 0

    for row in results:
        coverage = (
            row["implemented"] / row["total"]
            if row["total"] > 0 else 0
        )

        record = {
            "csf_category": row["_id"],
            "csf_function": row["csf_function"],
            "total_controls": row["total"],
            "implemented_controls": row["implemented"],
            "coverage": round(coverage, 3),
            "generated_at": datetime.utcnow()
        }

        db.csf_metrics.insert_one(record)
        inserted += 1

    print(f"[OK] Inserted {inserted} CSF coverage metric records.")


# ==========================================================
# Main
# ==========================================================

def main():
    print("=== STEP 3: Generating CSF → 800-53 Mappings & Coverage ===")

    update_control_mappings()
    generate_coverage_metrics()

    print("[DONE] Step 3 completed successfully.")


def run_csf_mapping_and_metrics():
    update_control_mappings()
    generate_coverage_metrics()

    return {
        "status": "OK",
        "message": "CSF mappings and metrics generated successfully.",
        "timestamp": datetime.utcnow()
    }


# if __name__ == "__main__":
#     main()

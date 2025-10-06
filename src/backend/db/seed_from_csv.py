import csv
import json
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "smbsec"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# 文件路径映射
CSV_FILES = {
    "assets": os.path.join(DATA_DIR, "assets.csv"),
    "vulnerabilities": os.path.join(DATA_DIR, "vulnerabilities.csv"),
    "intel_events": os.path.join(DATA_DIR, "intel_events.csv"),
    "risk_register": os.path.join(DATA_DIR, "risk_register.csv"),
    "asset_intel_links": os.path.join(DATA_DIR, "asset_intel_links_expected.csv"),
}

# ✅ 各文件字段映射：CSV列名 → Mongo字段名
FIELD_MAP = {
    "assets": {
        "Name": "name",
        "Type": "type",
        "Criticality": "criticality",
    },
    "intel_events": {
        "Source": "source",
        "Indicator": "indicator",
        "Raw": "raw",
        "Severity": "severity",
        "Created_At": "created_at",
    },
    "risk_register": {
        "Asset ID": "asset_id",
        "Title": "title",
        "Likelihood": "likelihood",
        "Impact": "impact",
    },
    "vulnerabilities": {
        "Vuln ID": "vuln_id",
        "Asset Name": "asset_name",
        "CVE": "cve",
        "Severity": "severity",
        "Description": "description",
    },
    "asset_intel_links": {
        "Asset Name": "asset_name",
        "Indicator": "indicator",
        "Match Type": "match_type",
    },
}

# ✅ 类型转换规则（按字段名自动转换）
def normalize_value(key, value):
    if value == "" or value is None:
        return None

    # 整型字段
    if key in {"criticality", "severity", "likelihood", "impact"}:
        try:
            return int(value)
        except ValueError:
            return None

    # JSON字段
    if key == "raw":
        try:
            return json.loads(value)
        except Exception:
            return {"data": value}  # 如果不是JSON，直接包裹成dict

    return value  # 默认保留字符串


async def import_csv_to_mongo(collection_name, file_path):
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    try:
        with open(file_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = []
            for row in reader:
                mapped_row = {}
                for csv_key, mongo_key in FIELD_MAP.get(collection_name, {}).items():
                    if csv_key in row:
                        mapped_row[mongo_key] = normalize_value(mongo_key, row[csv_key])
                if mapped_row:
                    rows.append(mapped_row)

            if not rows:
                print(f"⚠️ No valid data in {file_path}, skipping.")
                return

            await db[collection_name].delete_many({})  # 清空旧数据
            await db[collection_name].insert_many(rows)
            print(f"✅ Imported {len(rows)} records into '{collection_name}' collection.")

    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except Exception as e:
        print(f"❌ Error importing {collection_name}: {e}")


async def main():
    for collection, path in CSV_FILES.items():
        await import_csv_to_mongo(collection, path)


if __name__ == "__main__":
    asyncio.run(main())

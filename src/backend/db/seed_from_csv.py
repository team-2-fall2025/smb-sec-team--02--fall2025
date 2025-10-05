import csv
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "smbsec"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# 文件路径映射（根据你的实际路径调整）
CSV_FILES = {
    "assets": os.path.join(DATA_DIR, "assets.csv"),
    "vulnerabilities": os.path.join(DATA_DIR, "vulnerabilities.csv"),
    "intel_events": os.path.join(DATA_DIR, "intel_events.csv"),
    "risk_register": os.path.join(DATA_DIR, "risk_register.csv"),
    "asset_intel_links": os.path.join(DATA_DIR, "asset_intel_links_expected.csv")
}


async def import_csv_to_mongo(collection_name, file_path):
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    # 跳过空文件
    try:
        with open(file_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            data = [row for row in reader]
            if not data:
                print(f"⚠️ {file_path} is empty, skipping.")
                return
            # 插入前清空旧数据（避免重复）
            await db[collection_name].delete_many({})
            await db[collection_name].insert_many(data)
            print(f"✅ Imported {len(data)} records into '{collection_name}' collection.")
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except Exception as e:
        print(f"❌ Error importing {collection_name}: {e}")

async def main():
    for collection, path in CSV_FILES.items():
        await import_csv_to_mongo(collection, path)

if __name__ == "__main__":
    asyncio.run(main())

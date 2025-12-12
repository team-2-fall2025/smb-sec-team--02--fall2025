import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "smbsec")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

lines = []
for name in sorted(db.list_collection_names()):
    coll = db[name]
    lines.append(f"## {name}\n")
    for idx_name, idx in coll.index_information().items():
        lines.append(f"- {idx_name}: {idx}\n")
    lines.append("\n")

out_path = os.path.join("docs", "reports", "audit", "db-indexes.md")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"Wrote {out_path}")

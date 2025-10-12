from db.mongo import db

def init_indexes():
    db["assets"].create_index("ip")
    db["assets"].create_index("hostname")

    # ✅ 改进版：添加部分过滤条件
    db["asset_intel_links"].create_index(
        [("asset_id", 1), ("intel_id", 1)],
        unique=True,
        partialFilterExpression={"asset_id": {"$exists": True}, "intel_id": {"$exists": True}}
    )

    print("✅ MongoDB indexes initialized successfully.")

if __name__ == "__main__":
    init_indexes()

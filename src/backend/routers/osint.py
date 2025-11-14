# src/backend/routers/osint.py
from fastapi import APIRouter

from datetime import datetime
from ..db.mongo import db
from ..db.models import IntelEvent

router = APIRouter()

# 🧩 POST /api/osint/test  —— 插入一条标准化 intel_event 记录
@router.post("/osint/test")
async def osint_test():
    item = IntelEvent(
        source="otx",
        indicator="8.8.8.8",
        raw={"ok": True},
        severity=2,
        created_at=datetime.utcnow(),
    )
    # 插入数据
    res = await db.intel_events.insert_one(item.model_dump(by_alias=True, exclude_none=True))

    # 查询刚插入的文档
    inserted = await db.intel_events.find_one({"_id": res.inserted_id})

    # 把 ObjectId 转成字符串
    inserted["_id"] = str(inserted["_id"])

    return {"inserted": 1, "data": inserted}

# 🧾 GET /api/osint/test  —— 返回最近 5 条 intel_event 记录
@router.get("/osint/test")
async def osint_test_get():
    docs = await db.intel_events.find().sort("created_at", -1).to_list(5)
    # 转换每条记录中的 ObjectId
    for d in docs:
        d["_id"] = str(d["_id"])
    return {"recent_events": docs}

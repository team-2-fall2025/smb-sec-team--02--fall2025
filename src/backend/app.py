from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/health")
def health():
    return {
        "status": "ok",
        "env": os.getenv("APP_ENV", "dev")
    }
from fastapi import FastAPI
from src.backend.database import db

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "FastAPI is running"}

@app.get("/ping_db")
async def ping_db():
    test_doc = {"msg": "hello database"}
    result = await db.test.insert_one(test_doc)   # 插入一条测试数据
    doc = await db.test.find_one({"_id": result.inserted_id})
    doc["_id"] = str(doc["_id"])  # ObjectId 转字符串，避免 JSON 报错
    return {"status": "ok", "data": doc}


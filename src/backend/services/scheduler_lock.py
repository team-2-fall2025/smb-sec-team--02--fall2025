import time
from datetime import datetime, timedelta, timezone
from pymongo.collection import Collection
from pymongo import ReturnDocument


def utcnow():
    return datetime.now(timezone.utc)


def acquire_lock(locks: Collection, name: str, ttl_seconds: int) -> bool:
    """
    Acquire a distributed lock in MongoDB.
    Lock expires automatically after ttl_seconds (stale lock protection).
    """
    now = utcnow()
    expires_at = now + timedelta(seconds=ttl_seconds)

    doc = locks.find_one_and_update(
        {"_id": name, "$or": [{"expires_at": {"$lte": now}}, {"expires_at": {"$exists": False}}]},
        {"$set": {"expires_at": expires_at, "updated_at": now}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    # If we updated/created and expires_at is in the future, we "own" it.
    return doc is not None and doc.get("expires_at") == expires_at


def release_lock(locks: Collection, name: str) -> None:
    locks.update_one({"_id": name}, {"$set": {"expires_at": utcnow()}})

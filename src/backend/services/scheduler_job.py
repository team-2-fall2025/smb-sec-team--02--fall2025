import asyncio
import os
import random
import logging
from pymongo.database import Database
from .scheduler_lock import acquire_lock, release_lock

logger = logging.getLogger("scheduler")


async def run_with_retries(fn, retries: int = 3, base_delay: float = 1.0):
    last = None
    for i in range(retries):
        try:
            return await fn()
        except Exception as e:
            last = e
            delay = base_delay * (2 ** i) + random.random()
            logger.warning("job failed attempt=%s delay=%.2fs err=%r", i + 1, delay, e)
            await asyncio.sleep(delay)
    raise last


async def scheduled_job(db: Database):
    """
    Example scheduled task: run policy builder / cleanup / health checks.
    Replace the body with your real scheduled work.
    """
    # TODO: call your real logic
    await asyncio.sleep(0.1)


async def scheduler_loop(db: Database):
    interval = int(os.getenv("SCHED_INTERVAL_SECONDS", "300"))  # 5 min default
    jitter = int(os.getenv("SCHED_JITTER_SECONDS", "10"))
    lock_ttl = int(os.getenv("SCHED_LOCK_TTL_SECONDS", "240"))  # < interval

    locks = db.get_collection("locks")
    lock_name = "scheduler:main"

    while True:
        # jitter before attempting
        await asyncio.sleep(random.randint(0, max(jitter, 0)))

        got = acquire_lock(locks, lock_name, ttl_seconds=lock_ttl)
        if not got:
            logger.info("scheduler skip (lock held)")
        else:
            logger.info("scheduler run start")
            try:
                # hard timeout prevents hung job
                await asyncio.wait_for(
                    run_with_retries(lambda: scheduled_job(db), retries=3, base_delay=1.0),
                    timeout=120,
                )
                logger.info("scheduler run success")
            except asyncio.TimeoutError:
                logger.error("scheduler run timeout")
            except Exception as e:
                logger.exception("scheduler run failed: %r", e)
            finally:
                release_lock(locks, lock_name)

        # sleep until next tick
        await asyncio.sleep(interval)

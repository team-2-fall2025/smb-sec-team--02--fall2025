import os
from fastapi import FastAPI
from dotenv import load_dotenv
from agents.identify_agent import generate_asset_intel_links
from db.init_db import init_indexes
from routers import assets
from routers import stats, osint, seed, identify, protect, detect, respond, recover, govern, sops, csf
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from services.scheduler_job import scheduler_loop
from db.mongo import db
from observability.logging_setup import setup_logging
from middleware.request_id import RequestIdMiddleware
from middleware.access_log import AccessLogMiddleware

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="SMB Sec Platform", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow your frontend origin
    allow_credentials=True,                   # Allow cookies or auth headers if needed
    allow_methods=["*"],                      # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],                      # Allow all headers
)

@app.get("/")
async def root():
    return {"message": "FastAPI is running"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🚀 应用启动时执行
    init_indexes()
    print("Indexes initialized!")

    # yield 相当于应用运行期间
    yield

    # # 🛑 应用关闭时（可选）
    # print("App shutting down...")

# app = FastAPI(lifespan=lifespan)

@app.get("/generate-links")
async def generate_links():
    return await generate_asset_intel_links()

@app.get("/health")
def health():
    return {"version": "1.0", "status": "healthy"}

@app.get("/version")
def version():
    return {"version": "Week2-Skeleton"}



@app.get("/run/sop-generate")
def run_sop():
    result = sops.run_sop_generation()
    return result

@app.get("/run/csf-metrics")
def run_csf_metrics():
    result = csf.run_csf_mapping_and_metrics()
    return result

# 注册路由
app.include_router(stats.router, prefix="/api")
app.include_router(osint.router, prefix="/api")
app.include_router(seed.router, prefix="/api")
app.include_router(assets.router, prefix="/api")

app.include_router(identify.router)
app.include_router(protect.router)
app.include_router(detect.router)
app.include_router(respond.router)
app.include_router(recover.router)
app.include_router(govern.router)

origins_env = os.getenv("CORS_ORIGINS", "")
allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,     # DO NOT use ["*"] for Week 9
    allow_credentials=True,            # if cookies or auth headers
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    expose_headers=["X-Request-ID"],   # optional if you add request IDs later
)

@app.on_event("startup")
async def start_scheduler():
    asyncio.create_task(scheduler_loop(db))

setup_logging()

app.add_middleware(RequestIdMiddleware)
app.add_middleware(AccessLogMiddleware)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=9000, reload=True)
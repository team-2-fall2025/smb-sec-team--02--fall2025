
from fastapi import FastAPI
from dotenv import load_dotenv
from agents.identify_agent import fetch_pulses, generate_asset_intel_links
from agents.osint.otx_client import otx_intel_events
from agents.DS_agent import query_deepseek
from db.init_db import init_indexes
from routers import assets
from routers import stats, osint, seed, identify, protect, detect, respond, recover, govern, sops, csf
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

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

@app.get("/t")
async def t():
    # query_deepseek("on a scale of 1 to 5, how severe is the threat described as: (only return the number)" + ".net exploit kit is a sophisticated malware framework used by cybercriminals to deliver various types of malicious payloads to victims through drive-by download attacks.")
    # return otx_intel_events("103.235.46.102")
    await fetch_pulses()


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
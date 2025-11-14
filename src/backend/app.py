
from fastapi import FastAPI
from dotenv import load_dotenv

from .routers import stats, osint, seed, identify, protect, detect, respond, recover, govern
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/health")
def health():
    return {"version": "1.0", "status": "healthy"}

@app.get("/version")
def version():
    return {"version": "Week2-Skeleton"}

# 注册路由
app.include_router(stats.router, prefix="/api")
app.include_router(osint.router, prefix="/api")
app.include_router(seed.router, prefix="/api")

app.include_router(identify.router)
app.include_router(protect.router)
app.include_router(detect.router)
app.include_router(respond.router)
app.include_router(recover.router)
app.include_router(govern.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
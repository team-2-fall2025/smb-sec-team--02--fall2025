from fastapi import FastAPI
from routers import stats, osint, seed, identify, protect, detect, respond, recover, govern

app = FastAPI(title="SMB Sec Platform", version="0.2.0")

@app.get("/health")
def health():
    return {"status": "ok"}

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
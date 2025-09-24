from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/health")
def health():
    return {
        "status": "ok",
        "env": os.getenv("APP_ENV", "dev")
    }

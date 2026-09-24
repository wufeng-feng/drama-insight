import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.analyze import router as analyze_router
from app.services.video_processor import VideoProcessor

load_dotenv()

app = FastAPI(title="DramaInsight API", version="0.2.0")

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router, prefix="/api", tags=["分析"])


@app.get("/")
async def root():
    return {"message": "DramaInsight API", "version": "0.2.0"}


@app.get("/health")
async def health():
    dependencies = VideoProcessor.dependency_status()
    ready = all(dependencies.values())
    return {
        "status": "ok" if ready else "degraded",
        "dependencies": dependencies,
    }

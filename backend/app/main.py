import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routes.analyze import router as analyze_router

load_dotenv()

app = FastAPI(title="DramaInsight API", version="0.1.0")

# CORS配置，允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router, prefix="/api", tags=["分析"])


@app.get("/")
async def root():
    return {"message": "DramaInsight API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}

"""
MenoSmooth Backend - FastAPI Application Entry Point
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from app.config import settings
from app.database import init_db, close_db
from app.redis import close_redis, init_redis
from app.api.v1 import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    await init_db()
    await init_redis()
    yield
    await close_redis()
    await close_db()

app = FastAPI(
    title=settings.APP_NAME,
    description="更年不期 - AI 更年期健康助手",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.API_PREFIX)

static_dir = Path(__file__).parent.parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "version": "1.0.0"}

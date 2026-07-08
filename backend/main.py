"""
ZyLabs AI Research Copilot — FastAPI Application Entry Point
"""
import os

# CRITICAL: Disable TensorFlow before ANY imports to avoid Protobuf crash
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import init_db
from routers import sessions, workflow, chat

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"Starting {settings.app_name}")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down")


# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    description="AI-powered sales research copilot using LangGraph",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(sessions.router, prefix="/api")
app.include_router(workflow.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.effective_llm_model,
        "search_engine": settings.search_engine,
    }


@app.get("/", tags=["health"])
async def root():
    return {"message": f"{settings.app_name} API", "docs": "/docs"}

"""
api/main.py
SentinelIQ FastAPI application.
"""
from __future__ import annotations

import logging

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.alerts import router as alerts_router
from api.routes.query import router as query_router
from api.schemas import HealthResponse
from config import get_settings

settings = get_settings()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=settings.log_level.upper())
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        logging.getLevelName(settings.log_level.upper())
    )
)
logger = structlog.get_logger()

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="SentinelIQ",
    description=(
        "AI-powered threat intelligence platform. "
        "Ask security questions in plain English — get answers grounded in live CVE and SIEM data."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(query_router)
app.include_router(alerts_router)


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health() -> HealthResponse:
    """System health check."""
    return HealthResponse(
        status="ok",
        services={
            "api": "ok",
            "pinecone": "connected",  # TODO: live ping
            "elastic": "connected",   # TODO: live ping
        },
    )


@app.on_event("startup")
async def startup() -> None:
    logger.info("SentinelIQ starting", env=settings.env)


@app.on_event("shutdown")
async def shutdown() -> None:
    logger.info("SentinelIQ shutting down")

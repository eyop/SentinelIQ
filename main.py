"""
api/main.py
SentinelIQ FastAPI application.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.alerts import router as alerts_router
from api.routes.auth import router as auth_router
from api.routes.dashboard import router as dashboard_router
from api.routes.ingest import router as ingest_router
from api.routes.query import router as query_router
from api.routes.stream import router as stream_router
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle handlers."""
    logger.info("SentinelIQ starting", env=settings.env)
    yield
    logger.info("SentinelIQ shutting down")


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
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _check_service_health() -> dict[str, str]:
    """Ping each configured service and report live status."""
    services: dict[str, str] = {"api": "ok"}

    # Database (PostgreSQL)
    try:
        from scripts.init_db import DATABASE_URL

        url = DATABASE_URL
        if url and url.startswith("postgresql"):
            services["database"] = "configured"
        else:
            services["database"] = "not_configured"
    except Exception:
        services["database"] = "not_configured"

    # Redis
    try:
        from redis import Redis

        redis_cfg = settings.redis_url
        if redis_cfg:
            client = Redis.from_url(redis_cfg, socket_connect_timeout=1)
            client.ping()
            services["redis"] = "connected"
        else:
            services["redis"] = "not_configured"
    except Exception:
        services["redis"] = "disconnected"

    # Elasticsearch / SIEM
    try:
        from siem.client import ping as es_ping

        services["elastic"] = "connected" if es_ping() else "unavailable"
    except Exception:
        services["elastic"] = "unavailable"

    # Vector store
    services["vectorstore"] = settings.vectorstore or "in-memory"

    return services


# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(query_router)
app.include_router(alerts_router)
app.include_router(ingest_router)
app.include_router(dashboard_router)
app.include_router(stream_router)


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health() -> HealthResponse:
    """System health check with live service pings."""
    services = _check_service_health()
    status = "ok" if services.get("api") == "ok" else "degraded"
    return HealthResponse(status=status, services=services)
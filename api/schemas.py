from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    services: dict[str, str]


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    k: int = Field(default=5, ge=1, le=20)
    severity_filter: str | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    retrieved_count: int = 0


class AlertResponse(BaseModel):
    id: str | None = None
    source: str
    severity: str | None = None
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    correlated_cves: list[str] = Field(default_factory=list)


class IngestRequest(BaseModel):
    lookback_days: int = Field(default=7, ge=1, le=90)


class CorrelateRequest(BaseModel):
    event_text: str = Field(..., min_length=1)
    k: int = Field(default=5, ge=1, le=20)


class CorrelateResponse(BaseModel):
    explicit_ids: list[str] = Field(default_factory=list)
    similarity_ids: list[str] = Field(default_factory=list)
    llm_report: str | None = None
    correlated: list[str] = Field(default_factory=list)


class TokenRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str

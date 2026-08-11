from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from api.auth import require_auth
from api.schemas import AlertResponse, CorrelateRequest, CorrelateResponse
from siem.client import search_logs
from siem.correlator import correlate_event, correlate_and_persist

router = APIRouter(tags=["alerts"])


def _event_to_alert(event: dict[str, Any]) -> AlertResponse:
    """Convert a normalised SIEM event into an AlertResponse."""
    message = event.get("message") or ""
    severity = "High" if "exploit" in message.lower() or "brute" in message.lower() else "Medium"
    if "port scan" in message.lower():
        severity = "Medium"
    return AlertResponse(
        id=str(event.get("id") or ""),
        source=event.get("event_module") or event.get("index") or "siem",
        severity=severity,
        message=message,
        metadata={
            "timestamp": event.get("timestamp"),
            "rule_name": event.get("rule_name"),
            "source_ip": event.get("source_ip"),
            "destination_ip": event.get("destination_ip"),
            "destination_port": event.get("destination_port"),
            "user_name": event.get("user_name"),
            "process_name": event.get("process_name"),
        },
    )


@router.get("/alerts", response_model=list[AlertResponse], dependencies=[Depends(require_auth)])
async def list_alerts() -> list[AlertResponse]:
    """Return recent correlated alerts from SIEM event stream (or sample fallback)."""
    events = search_logs(size=50)
    return [_event_to_alert(evt) for evt in events]


@router.post("/alerts/correlate", response_model=CorrelateResponse)
async def correlate(request: CorrelateRequest) -> CorrelateResponse:
    """Correlate a freeform log event with known CVEs and return findings."""
    result = correlate_event(request.event_text, k=request.k)
    return CorrelateResponse(
        explicit_ids=result["explicit_ids"],
        similarity_ids=result["similarity_ids"],
        llm_report=result["llm_report"],
        correlated=result["correlated"],
    )


@router.post("/alerts/persist", response_model=CorrelateResponse)
async def persist(request: CorrelateRequest) -> CorrelateResponse:
    """Correlate a log event and persist the resulting alert to the DB."""
    alert: dict[str, Any] = {
        "source": "api",
        "severity": "Medium",
        "message": request.event_text,
    }
    result = await correlate_and_persist(alert, k=request.k)
    return CorrelateResponse(
        explicit_ids=result["explicit_ids"],
        similarity_ids=result["similarity_ids"],
        llm_report=result["llm_report"],
        correlated=result["correlated"],
    )
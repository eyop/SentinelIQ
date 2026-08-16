"""SIEM correlator — Phase 4: alert correlation engine.

Extracts explicit CVE IDs
- explicit CVE ID extraction
- vectorstore similarity lookup
- optional LLM-based correlation via `rag.chain.correlate_log_event`

Also includes a helper to persist correlated alerts into the DB.
"""

from __future__ import annotations

import re
from typing import Any

from config import get_settings
from rag.vectorstore import similarity_search
from rag.chain import correlate_log_event

try:
    # Local import to avoid circular import at package import time
    from scripts.init_db import save_alerts
except Exception:
    save_alerts = None


_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)


def extract_cve_ids(text: str) -> list[str]:
    """Return explicit CVE IDs found in freeform text."""
    if not text:
        return []
    found = _CVE_RE.findall(text)
    # Normalize to uppercase
    return [f.upper() for f in found]


def correlate_event(log_event_text: str, k: int = 5) -> dict[str, Any]:
    """Correlate a log event to known CVEs.

    Returns a dict with keys:
    - `explicit_ids`: CVE IDs explicitly referenced in the log
    - `similarity_ids`: CVE IDs found by vectorstore similarity
    - `llm_report`: optional human-friendly report from the LLM (if configured)
    - `correlated`: merged list of correlated CVE IDs (deduped)
    """
    explicit = extract_cve_ids(log_event_text)

    sim_docs = similarity_search(log_event_text, k=k)
    sim_ids: list[str] = []
    for d in sim_docs:
        meta = d.get("metadata") or {}
        # Try common metadata fields
        cid = meta.get("id") or meta.get("doc_id") or meta.get("cve_id")
        if cid:
            sim_ids.append(str(cid))

    llm_report = None
    llm_related: list[str] = []
    settings = get_settings()
    if settings.openai_api_key:
        try:
            res = correlate_log_event(log_event_text, k=k)
            llm_report = res.get("correlation_report")
            llm_related = [str(i) for i in (res.get("related_docs") or []) if i]
        except Exception:
            llm_report = "(LLM correlation failed)"

    # Merge order: explicit -> similarity -> llm_related
    merged: list[str] = []
    for s in (explicit + sim_ids + llm_related):
        if s and s not in merged:
            merged.append(s)

    return {
        "explicit_ids": explicit,
        "similarity_ids": sim_ids,
        "llm_report": llm_report,
        "correlated": merged,
    }


async def correlate_and_persist(alert: dict[str, Any], k: int = 5) -> dict[str, Any]:
    """Correlate the alert and persist it (if DB helpers are available).

    Returns the correlation result (same as `correlate_event`).
    """
    result = correlate_event(alert.get("message") or "", k=k)
    alert["correlated_cves"] = result["correlated"]

    if save_alerts:
        try:
            await save_alerts([alert])
        except Exception:
            # Persist failures should not raise here; log elsewhere if needed
            pass

    return result

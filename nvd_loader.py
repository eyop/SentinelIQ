"""
ingestion/nvd_loader.py
Fetches CVE records from the NVD REST API v2.
Produces a list of normalised dicts ready for embedding.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

NVD_BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"
PAGE_SIZE = 2000  # NVD max per request


def fetch_recent_cves(lookback_days: int | None = None) -> list[dict[str, Any]]:
    """
    Pull CVEs published in the last `lookback_days` days from the NVD API.
    Returns a list of normalised CVE dicts.
    """
    days = lookback_days or settings.nvd_lookback_days
    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(days=days)

    pub_start = start.strftime("%Y-%m-%dT%H:%M:%S.000")
    pub_end = end.strftime("%Y-%m-%dT%H:%M:%S.000")

    logger.info("Fetching CVEs from NVD: %s → %s", pub_start, pub_end)

    results: list[dict] = []
    start_index = 0

    with httpx.Client(timeout=30) as client:
        while True:
            params = {
                "pubStartDate": pub_start,
                "pubEndDate": pub_end,
                "startIndex": start_index,
                "resultsPerPage": PAGE_SIZE,
            }
            resp = client.get(NVD_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()

            vulnerabilities = data.get("vulnerabilities", [])
            for item in vulnerabilities:
                normalised = _normalise(item.get("cve", {}))
                if normalised:
                    results.append(normalised)

            total = data.get("totalResults", 0)
            start_index += len(vulnerabilities)
            logger.info("Fetched %d / %d CVEs", start_index, total)

            if start_index >= total:
                break

    logger.info("NVD ingestion complete: %d CVEs", len(results))
    return results


def _normalise(cve: dict) -> dict | None:
    """Flatten a raw NVD CVE object into a clean document dict."""
    cve_id = cve.get("id", "")
    if not cve_id:
        return None

    # Description (English preferred)
    descriptions = cve.get("descriptions", [])
    description = next(
        (d["value"] for d in descriptions if d.get("lang") == "en"),
        descriptions[0]["value"] if descriptions else "",
    )

    # CVSS v3.1 score (fall back to v3.0, then v2)
    metrics = cve.get("metrics", {})
    cvss_score, severity = _extract_cvss(metrics)

    # Affected products (CPE)
    affected_products = _extract_products(cve.get("configurations", []))

    # References
    refs = [r.get("url", "") for r in cve.get("references", [])]

    published = cve.get("published", "")
    modified = cve.get("lastModified", "")

    return {
        "id": cve_id,
        "source": "nvd",
        "description": description,
        "cvss_score": cvss_score,
        "severity": severity,
        "published": published,
        "modified": modified,
        "affected_products": affected_products,
        "references": refs[:5],  # cap to avoid token bloat
        # Pre-formatted text for embedding
        "text": (
            f"CVE ID: {cve_id}\n"
            f"Severity: {severity} (CVSS {cvss_score})\n"
            f"Published: {published}\n"
            f"Description: {description}\n"
            f"Affected products: {', '.join(affected_products) or 'unspecified'}"
        ),
    }


def _extract_cvss(metrics: dict) -> tuple[float, str]:
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entries = metrics.get(key, [])
        if entries:
            data = entries[0].get("cvssData", {})
            score = data.get("baseScore", 0.0)
            severity = data.get("baseSeverity", "UNKNOWN")
            return float(score), severity
    return 0.0, "UNKNOWN"


def _extract_products(configurations: list) -> list[str]:
    products = set()
    for config in configurations:
        for node in config.get("nodes", []):
            for cpe_match in node.get("cpeMatch", []):
                uri = cpe_match.get("criteria", "")
                # cpe:2.3:a:vendor:product:version → "vendor product"
                parts = uri.split(":")
                if len(parts) >= 5:
                    products.add(f"{parts[3]} {parts[4]}")
    return list(products)[:20]  # cap

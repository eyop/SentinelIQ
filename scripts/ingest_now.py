"""Run an ingestion cycle for local testing."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingestion.mitre_loader import fetch_attack_techniques
from ingestion.normaliser import cve_to_document, technique_to_document
from ingestion.nvd_loader import fetch_recent_cves
from scripts.init_db import save_alerts, save_cves


def run_ingestion(lookback_days: int = 7) -> dict[str, int]:
    cves = fetch_recent_cves(lookback_days=lookback_days)
    techniques = fetch_attack_techniques()

    cve_docs = [cve_to_document(cve) for cve in cves]
    technique_docs = [technique_to_document(technique) for technique in techniques]

    try:
        import asyncio

        asyncio.run(save_cves(cves))
        asyncio.run(
            save_alerts(
                [{"source": "ingest", "severity": "info", "message": "ingestion complete", "metadata": {"count": len(cve_docs)}}]
            )
        )
    except Exception:
        pass

    return {
        "cve_count": len(cve_docs),
        "technique_count": len(technique_docs),
        "total_documents": len(cve_docs) + len(technique_docs),
    }


if __name__ == "__main__":
    print(run_ingestion())

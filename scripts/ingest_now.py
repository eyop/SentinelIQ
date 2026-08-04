"""Run an ingestion cycle for local testing."""

from __future__ import annotations

from ingestion.mitre_loader import fetch_attack_techniques
from ingestion.normaliser import cve_to_document, technique_to_document
from ingestion.nvd_loader import fetch_recent_cves


def run_ingestion(lookback_days: int = 7) -> dict[str, int]:
	cves = fetch_recent_cves(lookback_days=lookback_days)
	techniques = fetch_attack_techniques()

	cve_docs = [cve_to_document(cve) for cve in cves]
	technique_docs = [technique_to_document(technique) for technique in techniques]

	return {
		"cve_count": len(cve_docs),
		"technique_count": len(technique_docs),
		"total_documents": len(cve_docs) + len(technique_docs),
	}


if __name__ == "__main__":
	print(run_ingestion())

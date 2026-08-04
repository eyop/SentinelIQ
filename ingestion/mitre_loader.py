"""ATT&CK MITRE ingestion helpers."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


DEFAULT_URLS = [
	"https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json",
	"https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json",
]


def fetch_attack_techniques() -> list[dict[str, Any]]:
	"""Fetch ATT&CK techniques and return normalized records."""
	for url in DEFAULT_URLS:
		try:
			with httpx.Client(timeout=20) as client:
				response = client.get(url)
				response.raise_for_status()
				payload = response.json()
				objects = payload.get("objects", []) if isinstance(payload, dict) else []
				techniques = []
				for item in objects:
					if not isinstance(item, dict):
						continue
					if item.get("type") != "attack-pattern":
						continue
					techniques.append(normalize_technique(item))
				if techniques:
					return techniques
		except Exception as exc:  # pragma: no cover - network fallback
			logger.warning("MITRE fetch failed for %s: %s", url, exc)

	return [
		{
			"id": "T1059",
			"name": "Command and Scripting Interpreter",
			"tactic": "Execution",
			"description": "Adversaries may abuse command interpreters to execute commands",
			"platforms": ["windows", "linux", "macos"],
			"mitigations": ["Restrict scripting environments and monitor command-line activity"],
			"source": "mitre",
		},
		{
			"id": "T1566",
			"name": "Phishing",
			"tactic": "Initial Access",
			"description": "Adversaries may use phishing to gain initial access",
			"platforms": ["windows", "linux", "macos"],
			"mitigations": ["Email filtering and user training"],
			"source": "mitre",
		},
	]


def normalize_technique(item: dict[str, Any]) -> dict[str, Any]:
	"""Normalize a MITRE ATT&CK object into a simple document schema."""
	external_references = item.get("external_references") or []
	name = item.get("name") or ""
	kill_chain_phases = item.get("kill_chain_phases") or []
	tactic = ""
	if kill_chain_phases:
		tactic = kill_chain_phases[0].get("phase_name", "")

	return {
		"id": item.get("external_references", [{}])[0].get("external_id") or item.get("id") or "UNKNOWN",
		"name": name,
		"tactic": tactic,
		"description": item.get("description") or "",
		"platforms": item.get("x_mitre_platforms") or [],
		"mitigations": [],
		"source": "mitre",
	}

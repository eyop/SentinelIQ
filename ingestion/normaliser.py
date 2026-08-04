"""Normalization helpers for ingestion documents."""

from __future__ import annotations

from typing import Any


def cve_to_document(raw_cve: dict[str, Any]) -> dict[str, Any]:
	"""Convert a raw CVE-like record into a normalized document payload."""
	description = raw_cve.get("description") or ""
	severity = (raw_cve.get("severity") or "UNKNOWN").upper()
	score = raw_cve.get("cvss_score") or 0.0
	affected_products = raw_cve.get("affected_products") or []
	references = raw_cve.get("references") or []
	text = raw_cve.get("text") or ""

	if not text:
		text = (
			f"CVE ID: {raw_cve.get('id', 'UNKNOWN')}\n"
			f"Severity: {severity}\n"
			f"Description: {description}"
		)

	return {
		"id": raw_cve.get("id") or "UNKNOWN",
		"source": raw_cve.get("source") or "nvd",
		"description": description,
		"severity": severity,
		"cvss_score": float(score) if score is not None else 0.0,
		"published": raw_cve.get("published"),
		"modified": raw_cve.get("modified"),
		"affected_products": list(affected_products),
		"references": list(references),
		"text": text,
		"doc_type": "cve",
		"metadata": {
			"source": raw_cve.get("source") or "nvd",
			"id": raw_cve.get("id") or "UNKNOWN",
			"severity": severity,
			"doc_type": "cve",
		},
	}


def technique_to_document(raw_technique: dict[str, Any]) -> dict[str, Any]:
	"""Convert a raw ATT&CK technique into a normalized document payload."""
	name = raw_technique.get("name") or ""
	tactic = raw_technique.get("tactic") or ""
	description = raw_technique.get("description") or ""
	platforms = raw_technique.get("platforms") or []
	mitigations = raw_technique.get("mitigations") or []

	text = (
		f"Technique ID: {raw_technique.get('id', 'UNKNOWN')}\n"
		f"Name: {name}\n"
		f"Tactic: {tactic}\n"
		f"Description: {description}"
	)

	return {
		"id": raw_technique.get("id") or "UNKNOWN",
		"source": raw_technique.get("source") or "mitre",
		"name": name,
		"tactic": tactic,
		"description": description,
		"platforms": list(platforms),
		"mitigations": list(mitigations),
		"text": text,
		"doc_type": "technique",
		"metadata": {
			"source": raw_technique.get("source") or "mitre",
			"id": raw_technique.get("id") or "UNKNOWN",
			"doc_type": "technique",
			"platforms": list(platforms),
		},
	}


def normalize_cve_data(raw_cve: dict[str, Any]) -> dict[str, Any]:
	return cve_to_document(raw_cve)


def normalize_technique_data(raw_technique: dict[str, Any]) -> dict[str, Any]:
	return technique_to_document(raw_technique)

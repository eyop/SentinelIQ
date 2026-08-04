"""Simple in-memory vector store for local development."""

from __future__ import annotations

import re
from typing import Any

_documents: list[dict[str, Any]] = []


def upsert_documents(documents: list[dict[str, Any]]) -> None:
	"""Store chunks in an in-memory list for retrieval."""
	_documents.extend(documents)


def similarity_search(query: str, k: int = 5, filter: dict[str, Any] | None = None) -> list[dict[str, Any]]:
	"""Perform a simple keyword-based similarity search."""
	query_terms = {term.lower() for term in re.findall(r"\w+", query)}
	if not query_terms:
		return []

	scored: list[tuple[float, dict[str, Any]]] = []
	for item in _documents:
		metadata = item.get("metadata") or {}
		if filter:
			if any(metadata.get(key) != value for key, value in filter.items()):
				continue
		text_terms = {term.lower() for term in re.findall(r"\w+", str(item.get("text") or ""))}
		overlap = len(query_terms & text_terms)
		if overlap:
			scored.append((float(overlap), item))

	scored.sort(key=lambda entry: entry[0], reverse=True)
	return [item for _, item in scored[:k]]

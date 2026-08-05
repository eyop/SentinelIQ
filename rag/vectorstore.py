"""In-memory vector store for local development with optional OpenAI embeddings.

This module computes and stores embeddings for documents on `upsert_documents`.
When OpenAI credentials are present the `rag.embedder` module will call the
OpenAI embeddings API; otherwise a deterministic local fallback is used.
"""

from __future__ import annotations

import math
import re
from typing import Any, List

from rag.embedder import embed_texts
from config import get_settings

_documents: List[dict[str, Any]] = []


def _cosine_similarity(a: List[float], b: List[float]) -> float:
	denom_a = math.sqrt(sum(x * x for x in a))
	denom_b = math.sqrt(sum(x * x for x in b))
	if denom_a == 0 or denom_b == 0:
		return 0.0
	return sum(x * y for x, y in zip(a, b)) / (denom_a * denom_b)


def upsert_documents(documents: list[dict[str, Any]]) -> None:
	"""Store chunks and compute embeddings for retrieval.

	Each document may be a dict with at least `text` and optional `metadata`.
	This function will attach an `embedding` key to each stored document.
	"""
	texts = [doc.get("text", "") for doc in documents]
	embeddings = embed_texts(texts)
	for doc, emb in zip(documents, embeddings):
		# Keep a shallow copy to avoid surprising callers
		stored = dict(doc)
		stored["embedding"] = emb
		_documents.append(stored)


def similarity_search(query: str, k: int = 5, filter: dict[str, Any] | None = None) -> list[dict[str, Any]]:
	"""Search by embedding similarity when embeddings exist, otherwise fallback
	to a simple keyword overlap heuristic.
	"""
	# Attempt to use embeddings for the query
	if not query or not _documents:
		return []

	# Prefer embedding-based ranking only when a real OpenAI key is configured.
	settings = get_settings()
	have_real_key = bool(settings.openai_api_key)
	# Documents may have embeddings attached; but only use embedding ranking
	# when we know embeddings were produced by the upstream provider.
	have_embeddings = any(d.get("embedding") for d in _documents) and have_real_key
	candidates: list[tuple[float, dict[str, Any]]] = []

	if have_embeddings:
		query_emb = embed_texts([query])[0]
		for item in _documents:
			metadata = item.get("metadata") or {}
			if filter and any(metadata.get(key) != value for key, value in filter.items()):
				continue
			emb = item.get("embedding")
			if not emb:
				continue
			score = _cosine_similarity(query_emb, emb)
			candidates.append((float(score), item))
		candidates.sort(key=lambda e: e[0], reverse=True)
		return [item for _, item in candidates[:k]]

	# Fallback: keyword overlap
	query_terms = {term.lower() for term in re.findall(r"\w+", query)}
	if not query_terms:
		return []

	for item in _documents:
		metadata = item.get("metadata") or {}
		if filter and any(metadata.get(key) != value for key, value in filter.items()):
			continue
		text_terms = {term.lower() for term in re.findall(r"\w+", str(item.get("text") or ""))}
		overlap = len(query_terms & text_terms)
		if overlap:
			candidates.append((float(overlap), item))

	candidates.sort(key=lambda entry: entry[0], reverse=True)
	return [item for _, item in candidates[:k]]

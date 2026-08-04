"""Simple document chunking helpers for local retrieval."""

from __future__ import annotations

from typing import Any


def chunk_documents(documents: list[dict[str, Any]], chunk_size: int = 200, overlap: int = 20) -> list[dict[str, Any]]:
	"""Split text documents into smaller overlapping chunks."""
	chunks: list[dict[str, Any]] = []
	for doc in documents:
		text = str(doc.get("text") or "")
		if not text:
			continue
		if len(text) <= chunk_size:
			chunks.append(_build_chunk(doc, text, 0))
			continue

		start = 0
		while start < len(text):
			end = min(len(text), start + chunk_size)
			piece = text[start:end]
			chunks.append(_build_chunk(doc, piece, start))
			if end >= len(text):
				break
			start = max(0, end - overlap)

	return chunks


def _build_chunk(doc: dict[str, Any], text: str, start_index: int) -> dict[str, Any]:
	metadata = dict(doc.get("metadata") or {})
	metadata.setdefault("doc_id", doc.get("id"))
	metadata.setdefault("doc_type", doc.get("doc_type"))
	metadata["chunk_index"] = start_index
	return {
		"id": f"{doc.get('id')}:{start_index}",
		"text": text,
		"metadata": metadata,
	}

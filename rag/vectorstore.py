"""In-memory vector store for local development with optional OpenAI embeddings.

This module computes and stores embeddings for documents on `upsert_documents`.
When OpenAI credentials are present the `rag.embedder` module will call the
OpenAI embeddings API; otherwise a deterministic local fallback is used.
"""

from __future__ import annotations

import math
import re
import logging
from typing import Any, List

from rag.embedder import embed_texts
from config import get_settings

_logger = logging.getLogger(__name__)

# Internal in-memory storage
_documents: List[dict[str, Any]] = []


def _cosine_similarity(a: List[float], b: List[float]) -> float:
	denom_a = math.sqrt(sum(x * x for x in a))
	denom_b = math.sqrt(sum(x * x for x in b))
	if denom_a == 0 or denom_b == 0:
		return 0.0
	return sum(x * y for x, y in zip(a, b)) / (denom_a * denom_b)


def _mem_upsert_documents(documents: list[dict[str, Any]]) -> None:
	"""In-memory upsert: compute embeddings and store locally."""
	texts = [doc.get("text", "") for doc in documents]
	embeddings = embed_texts(texts)
	for doc, emb in zip(documents, embeddings):
		stored = dict(doc)
		stored["embedding"] = emb
		_documents.append(stored)


def _mem_similarity_search(query: str, k: int = 5, filter: dict[str, Any] | None = None) -> list[dict[str, Any]]:
	"""In-memory search: prefer embedding similarity only when OpenAI key present."""
	if not query or not _documents:
		return []

	settings = get_settings()
	have_real_key = bool(settings.openai_api_key)
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


# --- Optional Pinecone production vectorstore support ---
_pinecone_available = False
_pinecone_index = None
_pinecone_name = None
try:
	import pinecone  # type: ignore
	_pinecone_available = True
except Exception:
	_pinecone_available = False


# --- Optional FAISS local vectorstore support ---
_faiss_available = False
_faiss_index = None
_faiss_meta: dict[str, dict[str, Any]] = {}
_faiss_dim = None
try:
 	import faiss  # type: ignore
 	import numpy as _np  # type: ignore
 	_faiss_available = True
except Exception:
 	_faiss_available = False


def _init_pinecone_if_configured() -> None:
	global _pinecone_index, _pinecone_name
	settings = get_settings()
	if not _pinecone_available or not settings.pinecone_api_key:
		return
	try:
		pinecone.init(api_key=settings.pinecone_api_key, environment=settings.pinecone_environment)
		_index_name = getattr(settings, "pinecone_index", "sentineliq")
		# create index if missing will be attempted lazily during upsert
		_pinecone_name = _index_name
		_pinecone_index = pinecone.Index(_pinecone_name)
		_logger.info("Connected to Pinecone index %s", _pinecone_name)
	except Exception as exc:
		_logger.exception("Pinecone init failed: %s", exc)
		_pinecone_index = None


def _pinecone_upsert_documents(documents: list[dict[str, Any]]) -> None:
	"""Upsert documents into Pinecone index. Falls back to in-memory on failure."""
	settings = get_settings()
	if not _pinecone_available or not settings.pinecone_api_key:
		_mem_upsert_documents(documents)
		return

	texts = [doc.get("text", "") for doc in documents]
	embeddings = embed_texts(texts)
	# Ensure index exists with appropriate dimension
	try:
		if _pinecone_name not in pinecone.list_indexes():
			dim = len(embeddings[0]) if embeddings else 512
			pinecone.create_index(_pinecone_name, dimension=dim)
		index = pinecone.Index(_pinecone_name)
		vectors = []
		for doc, emb in zip(documents, embeddings):
			meta = dict(doc.get("metadata") or {})
			vec_id = meta.get("id") or meta.get("doc_id") or doc.get("id")
			if not vec_id:
				# fallback id
				vec_id = f"doc-{len(_documents)+1}"
			vectors.append((str(vec_id), emb, meta))
			# keep local copy too
			stored = dict(doc)
			stored["embedding"] = emb
			_documents.append(stored)
		index.upsert(vectors=vectors)
	except Exception:
		_logger.exception("Pinecone upsert failed, falling back to in-memory storage")
		_mem_upsert_documents(documents)


def _pinecone_similarity_search(query: str, k: int = 5, filter: dict[str, Any] | None = None) -> list[dict[str, Any]]:
	settings = get_settings()
	if not _pinecone_available or not settings.pinecone_api_key:
		return _mem_similarity_search(query, k=k, filter=filter)

	try:
		q_emb = embed_texts([query])[0]
		index = pinecone.Index(_pinecone_name)
		resp = index.query(vector=q_emb, top_k=k, include_metadata=True)
		matches = []
		# Support response formats across SDK versions
		for m in getattr(resp, "matches", []) or resp.get("matches", []):
			meta = getattr(m, "metadata", None) or m.get("metadata") if isinstance(m, dict) else None
			text = None
			if meta:
				text = meta.get("text") or meta.get("content")
			matches.append({"id": getattr(m, "id", None) or m.get("id"), "text": text or "", "metadata": meta or {}})
		return matches
	except Exception:
		_logger.exception("Pinecone query failed; falling back to in-memory similarity")
		return _mem_similarity_search(query, k=k, filter=filter)


def upsert_documents(documents: list[dict[str, Any]]) -> None:
	"""Public upsert: route to Pinecone if configured, otherwise in-memory."""
	settings = get_settings()
	if settings.vectorstore and settings.vectorstore.lower() == "pinecone" and _pinecone_available and settings.pinecone_api_key:
		_init_pinecone_if_configured()
		if _pinecone_name:
			_pinecone_upsert_documents(documents)
			return

	# Default
	_mem_upsert_documents(documents)


def similarity_search(query: str, k: int = 5, filter: dict[str, Any] | None = None) -> list[dict[str, Any]]:
	"""Public similarity search: route to Pinecone if configured, otherwise in-memory."""
	settings = get_settings()
	if settings.vectorstore and settings.vectorstore.lower() == "pinecone" and _pinecone_available and settings.pinecone_api_key:
		_init_pinecone_if_configured()
		if _pinecone_name:
			return _pinecone_similarity_search(query, k=k, filter=filter)
	return _mem_similarity_search(query, k=k, filter=filter)


def _init_faiss_if_configured(dim: int) -> None:
 	global _faiss_index, _faiss_dim
 	settings = get_settings()
 	if not _faiss_available or not settings.vectorstore or settings.vectorstore.lower() != "faiss":
 		return
 	try:
 		# Use IndexFlatIP on normalized vectors for cosine similarity
 		_index = faiss.IndexFlatIP(dim)
 		_faiss_index = _index
 		_faiss_dim = dim
 		_logger.info("Initialized FAISS index with dim=%s", dim)
 	except Exception:
 		_logger.exception("FAISS init failed")


def _faiss_upsert_documents(documents: list[dict[str, Any]]) -> None:
 	"""Insert documents into an in-memory FAISS index.

	This keeps a local metadata map `_faiss_meta` to map vector ids to document metadata/text.
	"""
 	settings = get_settings()
 	if not _faiss_available or not settings.vectorstore or settings.vectorstore.lower() != "faiss":
 		_mem_upsert_documents(documents)
 		return

 	texts = [doc.get("text", "") for doc in documents]
 	embeddings = embed_texts(texts)
 	if not embeddings:
 		return

 	# ensure index initialized
 	_dim = len(embeddings[0])
 	_init_faiss_if_configured(_dim)
 	if _faiss_index is None:
 		_mem_upsert_documents(documents)
 		return

 	# normalize embeddings for cosine via inner product
 	arr = _np.array(embeddings, dtype=_np.float32)
 	_norms = _np.linalg.norm(arr, axis=1, keepdims=True)
 	_norms[_norms == 0] = 1.0
 	arr = arr / _norms

 	start_id = _faiss_index.ntotal
 	try:
 		_faiss_index.add(arr)
 		# register metadata
 		for i, doc in enumerate(documents):
 			vec_id = f"faiss-{start_id + i}"
 			_meta = dict(doc.get("metadata") or {})
 			_meta.update({"text": doc.get("text", "")})
 			_faiss_meta[vec_id] = _meta
 			# also keep local copy for other fallbacks
 			stored = dict(doc)
 			stored["embedding"] = embeddings[i]
 			_documents.append(stored)
 	except Exception:
 		_logger.exception("FAISS upsert failed; falling back to in-memory")
 		_mem_upsert_documents(documents)


def _faiss_similarity_search(query: str, k: int = 5, filter: dict[str, Any] | None = None) -> list[dict[str, Any]]:
 	settings = get_settings()
 	if not _faiss_available or not settings.vectorstore or settings.vectorstore.lower() != "faiss":
 		return _mem_similarity_search(query, k=k, filter=filter)

 	query_emb = embed_texts([query])[0]
 	if _faiss_index is None:
 		return _mem_similarity_search(query, k=k, filter=filter)

 	import numpy as _np
 	q = _np.array([query_emb], dtype=_np.float32)
 	qnorm = _np.linalg.norm(q, axis=1, keepdims=True)
 	qnorm[qnorm == 0] = 1.0
 	q = q / qnorm
 
 	try:
 		distances, indices = _faiss_index.search(q, k)
 		results: list[dict[str, Any]] = []
 		for score, idx in zip(distances[0], indices[0]):
 			if idx < 0:
 				continue
 			vec_id = f"faiss-{idx}"
 			meta = _faiss_meta.get(vec_id, {})
 			results.append({"id": vec_id, "text": meta.get("text", ""), "metadata": meta, "score": float(score)})
 		return results
 	except Exception:
 		_logger.exception("FAISS query failed; falling back to in-memory")
 		return _mem_similarity_search(query, k=k, filter=filter)

"""Embedding helper: use OpenAI embeddings when available, otherwise deterministic fallback."""

from __future__ import annotations

import hashlib
from typing import List

import openai

from config import get_settings


DEFAULT_DIM = 512


def _deterministic_embedding(text: str, dim: int = DEFAULT_DIM) -> List[float]:
    """Create a deterministic pseudo-embedding from text using SHA256.

    This ensures consistent fallback embeddings when OpenAI isn't configured.
    """
    h = hashlib.sha256(text.encode("utf-8")).digest()
    # Expand hash deterministically to requested dimension
    values: List[float] = []
    i = 0
    while len(values) < dim:
        # Re-hash with a counter to expand
        chunk = hashlib.sha256(h + i.to_bytes(2, "big")).digest()
        for b in chunk:
            if len(values) >= dim:
                break
            # map byte 0-255 -> -1.0 .. 1.0
            values.append((b / 127.5) - 1.0)
        i += 1
    return values


def embed_texts(texts: List[str], model: str | None = None) -> List[List[float]]:
    settings = get_settings()
    if settings.openai_api_key:
        try:
            openai.api_key = settings.openai_api_key
            model_name = model or "text-embedding-3-small"
            resp = openai.Embedding.create(model=model_name, input=texts)
            return [e.embedding for e in resp.data]
        except Exception:
            # Log at caller if desired; fall through to deterministic fallback
            pass

    # Fallback deterministic embeddings
    return [_deterministic_embedding(t) for t in texts]

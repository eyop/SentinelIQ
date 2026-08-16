"""Backward-compat shim.

The canonical RAG chain now lives at `rag/chain.py` with offline fallback
support. This module re-exports the key functions so existing references
such as `from chain import answer_query` continue to work.
"""

from rag.chain import answer_query, correlate_log_event

__all__ = ["answer_query", "correlate_log_event"]

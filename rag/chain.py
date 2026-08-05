"""Lightweight RAG chain with an offline fallback for local development."""

from __future__ import annotations

import logging
from typing import Any

from config import get_settings
from rag.prompts import ANALYST_PROMPT, CORRELATION_PROMPT
from rag.vectorstore import similarity_search
from rag.llm import chat_completion

logger = logging.getLogger(__name__)


def _format_docs_for_context(docs: list[dict[str, Any]]) -> str:
    parts = []
    for i, d in enumerate(docs, 1):
        meta = d.get("metadata") or {}
        header = f"[{i}] Source: {meta.get('source','?')} | ID: {meta.get('id','?')}"
        parts.append(f"{header}\n{d.get('text','')}")
    return "\n\n---\n\n".join(parts)


def answer_query(question: str, k: int = 5, severity_filter: str | None = None) -> dict[str, Any]:
    settings = get_settings()

    filter_dict = None
    if severity_filter:
        filter_dict = {"severity": severity_filter.upper()}

    docs = similarity_search(question, k=k, filter=filter_dict)
    context = _format_docs_for_context(docs)

    # If OpenAI key present, use chat completion wrapper. Otherwise, return a simple fallback.
    if settings.openai_api_key:
        try:
            prompt = ANALYST_PROMPT.format(context=context, question=question)
            resp = chat_completion(prompt, stream=False, model=settings.llm_model, max_tokens=512)
            answer = resp if isinstance(resp, str) else str(resp)
        except Exception as exc:  # pragma: no cover - external API
            logger.exception("LLM call failed: %s", exc)
            answer = "(LLM call failed) " + (context[:400] or "No context available")
    else:
        # Fallback: summarize top docs
        if not docs:
            answer = "No relevant documents found for the query."
        else:
            snippets = [d.get("text","")[:300] for d in docs[:3]]
            answer = "Fallback summary:\n" + "\n\n".join(snippets)

    sources = [d.get("metadata") or {} for d in docs]

    return {
        "answer": answer,
        "sources": sources,
        "retrieved_count": len(docs),
    }


def correlate_log_event(log_event_text: str, k: int = 5) -> dict[str, Any]:
    docs = similarity_search(log_event_text, k=k)
    context = _format_docs_for_context(docs)

    settings = get_settings()
    if settings.openai_api_key:
        try:
            prompt = CORRELATION_PROMPT.format(context=context, log_event=log_event_text)
            resp = chat_completion(prompt, stream=False, model=settings.llm_model, max_tokens=512)
            report = resp if isinstance(resp, str) else str(resp)
        except Exception:  # pragma: no cover - external API
            report = "(LLM call failed)"
    else:
        report = "Fallback correlation: related documents -> " + ", ".join(
            [d.get("metadata", {}).get("id", "?") for d in docs]
        )

    return {"correlation_report": report, "related_docs": [d.get("metadata", {}).get("id") for d in docs]}

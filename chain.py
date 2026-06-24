"""
rag/chain.py
The SentinelIQ RAG chain.
Retrieves relevant CVE/ATT&CK/SIEM docs from Pinecone,
injects them as context, and returns a grounded GPT-4o answer.
"""
from __future__ import annotations

import logging
from typing import AsyncIterator

from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from config import get_settings
from rag.prompts import ANALYST_PROMPT, CORRELATION_PROMPT
from rag.vectorstore import similarity_search

logger = logging.getLogger(__name__)


def _get_llm() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.llm_model,
        temperature=0.1,  # low temp for factual security answers
        openai_api_key=settings.openai_api_key,
        streaming=True,
    )


def _format_docs(docs: list[Document]) -> str:
    """Format retrieved docs into the context block for the prompt."""
    parts = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        header = f"[{i}] Source: {meta.get('source','?').upper()} | ID: {meta.get('id','?')}"
        if meta.get("severity"):
            header += f" | Severity: {meta['severity']}"
        if meta.get("cvss_score"):
            header += f" | CVSS: {meta['cvss_score']}"
        parts.append(f"{header}\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def answer_query(
    question: str,
    chat_history: list[BaseMessage] | None = None,
    k: int = 5,
    severity_filter: str | None = None,
) -> dict:
    """
    Run the full RAG pipeline for an analyst question.

    Returns:
        {
            "answer": str,
            "sources": list[dict],   # metadata from retrieved docs
            "retrieved_count": int
        }
    """
    filter_dict = None
    if severity_filter:
        filter_dict = {"severity": severity_filter.upper()}

    docs = similarity_search(question, k=k, filter=filter_dict)
    context = _format_docs(docs)

    llm = _get_llm()
    chain = ANALYST_PROMPT | llm | StrOutputParser()

    answer = chain.invoke(
        {
            "context": context,
            "question": question,
            "chat_history": chat_history or [],
        }
    )

    sources = [
        {
            "id": d.metadata.get("id"),
            "source": d.metadata.get("source"),
            "severity": d.metadata.get("severity"),
            "cvss_score": d.metadata.get("cvss_score"),
            "doc_type": d.metadata.get("doc_type"),
        }
        for d in docs
    ]

    logger.info(
        "Query answered | docs_retrieved=%d | question_len=%d",
        len(docs),
        len(question),
    )

    return {
        "answer": answer,
        "sources": sources,
        "retrieved_count": len(docs),
    }


async def stream_answer(
    question: str,
    chat_history: list[BaseMessage] | None = None,
    k: int = 5,
) -> AsyncIterator[str]:
    """
    Streaming version — yields answer tokens for SSE/WebSocket delivery.
    """
    docs = similarity_search(question, k=k)
    context = _format_docs(docs)

    llm = _get_llm()
    chain = ANALYST_PROMPT | llm | StrOutputParser()

    async for chunk in chain.astream(
        {
            "context": context,
            "question": question,
            "chat_history": chat_history or [],
        }
    ):
        yield chunk


def correlate_log_event(log_event_text: str, k: int = 5) -> dict:
    """
    Given a SIEM log event, retrieve related CVEs/techniques
    and return a structured correlation report.
    """
    docs = similarity_search(log_event_text, k=k)
    context = _format_docs(docs)

    llm = _get_llm()
    chain = CORRELATION_PROMPT | llm | StrOutputParser()

    report = chain.invoke({"context": context, "log_event": log_event_text})

    return {
        "correlation_report": report,
        "related_docs": [d.metadata.get("id") for d in docs],
    }

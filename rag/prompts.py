"""Prompt templates for RAG interactions."""

ANALYST_PROMPT = (
    "You are a security analyst assistant. Use the provided context to answer the question. "
    "Context:\n{context}\nQuestion: {question}\nProvide a concise, actionable answer and list the sources by index."
)

CORRELATION_PROMPT = (
    "You are a SOC analyst. Given context:\n{context}\nand a log event:\n{log_event}\nReturn a short correlation summary and list likely related CVE IDs."
)

from __future__ import annotations

from typing import Generator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.schemas import QueryRequest
from config import get_settings
from rag.prompts import ANALYST_PROMPT
from rag.vectorstore import similarity_search
from rag.llm import chat_completion
from rag.chain import _format_docs_for_context

router = APIRouter(tags=["query"])


@router.post("/query/stream")
async def stream_query(request: QueryRequest) -> StreamingResponse:
    """Stream an LLM answer as Server-Sent Events (SSE).

    Yields `data: ...` events containing incremental text pieces.
    """
    settings = get_settings()

    filter_dict = None
    if request.severity_filter:
        filter_dict = {"severity": request.severity_filter.upper()}

    docs = similarity_search(request.question, k=request.k, filter=filter_dict)
    context = _format_docs_for_context(docs)
    prompt = ANALYST_PROMPT.format(context=context, question=request.question)

    if settings.openai_api_key:
        gen = chat_completion(prompt, stream=True, model=settings.llm_model)

        def event_stream() -> Generator[str, None, None]:
            for piece in gen:
                # Emit as SSE `data:` lines. Preserve newlines by sending multiple data lines.
                if piece is None:
                    continue
                for line in str(piece).splitlines() or [""]:
                    yield f"data: {line}\n"
                yield "\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    # No OpenAI key: stream a single fallback summary chunk
    if not docs:
        fallback = "No relevant documents found for the query."
    else:
        snippets = [d.get("text", "")[:300] for d in docs[:3]]
        fallback = "Fallback summary:\n" + "\n\n".join(snippets)

    def single() -> Generator[str, None, None]:
        for line in fallback.splitlines() or [""]:
            yield f"data: {line}\n"
        yield "\n"

    return StreamingResponse(single(), media_type="text/event-stream")

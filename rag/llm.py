"""LLM helper with optional streaming support using OpenAI API.

Provides a small wrapper `chat_completion` that either returns the full
assistant response string, or yields text chunks when `stream=True`.
"""

from __future__ import annotations

from typing import Generator

import openai

from config import get_settings


def chat_completion(prompt: str, stream: bool = False, model: str | None = None, max_tokens: int = 512):
    settings = get_settings()
    model_name = model or settings.llm_model

    if not settings.openai_api_key:
        # No key configured; caller should fallback to local behavior.
        if stream:
            def _empty_gen() -> Generator[str, None, None]:
                yield "(no-openai-key)"
            return _empty_gen()
        return "(no-openai-key)"

    openai.api_key = settings.openai_api_key

    if stream:
        # Return a generator yielding incremental text pieces
        resp = openai.ChatCompletion.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            max_tokens=max_tokens,
        )

        def _stream_gen() -> Generator[str, None, None]:
            buffer = []
            for chunk in resp:
                try:
                    delta = chunk.choices[0].delta
                except Exception:
                    continue
                text = delta.get("content")
                if text:
                    buffer.append(text)
                    yield text
            # Final piece: join for completeness
            if buffer:
                yield ""  # no-op tail; callers can join streamed pieces

        return _stream_gen()

    # Non-streaming: return the assistant content string
    resp = openai.ChatCompletion.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()

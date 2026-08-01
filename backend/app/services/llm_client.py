"""Thin wrapper around the Anthropic client used both by the chatbot
and by every test engine (judge, hallucination detector, security scanner).
Centralizing this makes it trivial to swap in OpenAI/Gemini clients later
for multi-model leaderboard support (see services/providers.py).
"""
import time
from typing import Iterator
from anthropic import Anthropic
from app.core.config import settings

_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None


class LLMResult:
    def __init__(self, text: str, latency_ms: float, input_tokens: int, output_tokens: int):
        self.text = text
        self.latency_ms = latency_ms
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


def _require_client():
    if _client is None:
        raise RuntimeError("ANTHROPIC_API_KEY not set. Add it to backend/.env")
    return _client


def complete(prompt: str, system: str = "", model: str | None = None, max_tokens: int = 1024) -> LLMResult:
    client = _require_client()
    model = model or settings.MODEL_UNDER_TEST
    start = time.perf_counter()
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system or "You are a helpful assistant.",
        messages=[{"role": "user", "content": prompt}],
    )
    latency_ms = (time.perf_counter() - start) * 1000
    text = "".join(block.text for block in resp.content if block.type == "text")
    return LLMResult(
        text=text,
        latency_ms=latency_ms,
        input_tokens=resp.usage.input_tokens,
        output_tokens=resp.usage.output_tokens,
    )


def stream(messages: list[dict], system: str = "", model: str | None = None) -> Iterator[str]:
    client = _require_client()
    model = model or settings.MODEL_UNDER_TEST
    with client.messages.stream(
        model=model,
        max_tokens=1024,
        system=system or "You are a helpful assistant.",
        messages=messages,
    ) as stream_ctx:
        for text in stream_ctx.text_stream:
            yield text

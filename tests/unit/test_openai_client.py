"""Unit tests for the OpenAI-compatible HTTP provider using mock responses."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from bastion_arena.core.errors import ModelTimeoutError
from bastion_arena.providers.openai_client import OpenAICompatibleProvider


def test_openai_compatible_provider_mock() -> None:
    async def _run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/v1/chat/completions":
                return httpx.Response(
                    200,
                    json={
                        "choices": [{"message": {"content": "Mock OpenAI response content"}}],
                        "usage": {"total_tokens": 12},
                    },
                )
            if request.url.path == "/v1/models":
                return httpx.Response(200, json={"data": [{"id": "qwen3:8b"}]})
            return httpx.Response(404)

        transport = httpx.MockTransport(handler)
        client = httpx.AsyncClient(transport=transport, base_url="http://mock-llm/v1")

        provider = OpenAICompatibleProvider(
            base_url="http://mock-llm/v1", model="qwen3:8b", client=client
        )

        resp = await provider.generate("Test prompt")
        assert resp.content == "Mock OpenAI response content"
        assert resp.tokens_used == 12
        assert resp.model == "qwen3:8b"

        health = await provider.check_health()
        assert health is True

    asyncio.run(_run())


def test_openai_compatible_provider_timeout() -> None:
    async def _run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("Connection timed out")

        transport = httpx.MockTransport(handler)
        client = httpx.AsyncClient(transport=transport, base_url="http://mock-llm/v1")

        provider = OpenAICompatibleProvider(
            base_url="http://mock-llm/v1", timeout_seconds=1.0, client=client
        )

        with pytest.raises(ModelTimeoutError):
            await provider.generate("Test prompt")

    asyncio.run(_run())

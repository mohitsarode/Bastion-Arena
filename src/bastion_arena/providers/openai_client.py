"""Unified async HTTP client for OpenAI-compatible model endpoints (Ollama, vLLM, cloud)."""

from __future__ import annotations

import time

import httpx

from bastion_arena.core.errors import ModelTimeoutError
from bastion_arena.providers.base import BaseProvider, ProviderResponse


class OpenAICompatibleProvider(BaseProvider):
    """Async provider connecting to any OpenAI-compatible API (e.g. Ollama, vLLM, llama.cpp)."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model: str = "qwen3:8b",
        api_key: str | None = None,
        timeout_seconds: float = 45.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key or "EMPTY"
        self.timeout_seconds = timeout_seconds
        self._external_client = client
        self._internal_client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._external_client is not None:
            return self._external_client
        if self._internal_client is None or self._internal_client.is_closed:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            self._internal_client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=httpx.Timeout(self.timeout_seconds),
            )
        return self._internal_client

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> ProviderResponse:
        client = self._get_client()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        t0 = time.perf_counter()
        try:
            resp = await client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            data = resp.json()

            choice = data["choices"][0]
            content = choice["message"]["content"]
            usage = data.get("usage", {})
            tokens_used = usage.get("total_tokens", len(content.split()))

            return ProviderResponse(
                content=content,
                tokens_used=tokens_used,
                model=self.model,
                latency_ms=elapsed_ms,
            )
        except httpx.TimeoutException as exc:
            raise ModelTimeoutError(
                f"Model request timed out after {self.timeout_seconds}s"
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"Model generation failed: {exc}") from exc

    async def check_health(self) -> bool:
        client = self._get_client()
        try:
            resp = await client.get("/models")
            return resp.status_code == 200
        except Exception:
            return False

    async def aclose(self) -> None:
        if self._internal_client and not self._internal_client.is_closed:
            await self._internal_client.aclose()

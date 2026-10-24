"""Provider factory selecting between Fake, Ollama, and OpenAI-compatible cloud profiles."""

from __future__ import annotations

from bastion_arena.core.config import ModelEndpointConfig, Settings
from bastion_arena.core.resilience import ResilientProvider
from bastion_arena.providers.base import BaseProvider
from bastion_arena.providers.fake import FakeProvider
from bastion_arena.providers.openai_client import OpenAICompatibleProvider


def build_provider(config: Settings) -> BaseProvider:
    """Build and return configured model provider based on runtime settings profile."""
    mode = config.providers.mode

    if mode == "fake":
        return FakeProvider()

    if mode == "ollama":
        endpoint = config.models.get(
            "ollama",
            ModelEndpointConfig(
                base_url="http://localhost:11434/v1",
                model="qwen3:8b",
                timeout_seconds=45,
            ),
        )
        raw_provider = OpenAICompatibleProvider(
            base_url=endpoint.base_url,
            model=endpoint.model,
            timeout_seconds=endpoint.timeout_seconds,
        )
        return ResilientProvider(raw_provider)

    if mode == "openai_compatible_cloud":
        endpoint = config.models.get(
            "cloud",
            ModelEndpointConfig(
                base_url="https://api.openai.com/v1",
                model="gpt-4o-mini",
                timeout_seconds=45,
            ),
        )
        raw_provider = OpenAICompatibleProvider(
            base_url=endpoint.base_url,
            model=endpoint.model,
            timeout_seconds=endpoint.timeout_seconds,
        )
        return ResilientProvider(raw_provider)

    return FakeProvider()

"""Abstract base interface for model providers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict, Field


class ProviderResponse(BaseModel):
    """Standardized response from any LLM provider adapter."""

    model_config = ConfigDict(extra="forbid")

    content: str = Field(..., description="Generated text content")
    tokens_used: int = Field(default=0, ge=0, description="Estimated or reported token usage")
    model: str = Field(default="fake", description="Model identifier")
    latency_ms: float = Field(default=0.0, ge=0.0, description="Inference latency in milliseconds")


class BaseProvider(ABC):
    """Abstract interface for all model providers (Fake, Local Ollama, Cloud)."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> ProviderResponse:
        """Generate response given a user prompt and optional system instructions."""
        raise NotImplementedError

    @abstractmethod
    async def check_health(self) -> bool:
        """Return True if the provider is reachable and operational."""
        raise NotImplementedError

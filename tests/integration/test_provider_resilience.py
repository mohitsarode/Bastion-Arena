"""Integration tests for provider resilience, circuit breakers, and bounded retries."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import httpx
import pytest

from bastion_arena.core.config import ModelEndpointConfig, ProvidersConfig, Settings
from bastion_arena.core.errors import ModelTimeoutError
from bastion_arena.core.resilience import (
    CircuitBreaker,
    CircuitState,
    ResilientProvider,
    RetryPolicy,
)
from bastion_arena.providers.base import BaseProvider, ProviderResponse
from bastion_arena.providers.factory import build_provider
from bastion_arena.providers.fake import FakeProvider
from bastion_arena.providers.openai_client import OpenAICompatibleProvider


class FlakyProvider(BaseProvider):
    """Test mock provider that fails or times out conditionally."""

    def __init__(self, failure_count: int = 0, fail_with_timeout: bool = True) -> None:
        self.failure_count = failure_count
        self.fail_with_timeout = fail_with_timeout
        self.attempts = 0

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> ProviderResponse:
        self.attempts += 1
        if self.attempts <= self.failure_count:
            if self.fail_with_timeout:
                raise httpx.TimeoutException("Mock connection timed out")
            raise httpx.NetworkError("Mock socket connection reset")
        return ProviderResponse(content="Recovered response", model="flaky-mock", latency_ms=10.0)

    async def check_health(self) -> bool:
        return self.attempts >= self.failure_count


def test_provider_profile_factory() -> None:
    """Verify that build_provider creates appropriate classes based on runtime profile."""
    # Fake profile (default offline)
    cfg_fake = Settings(providers=ProvidersConfig(mode="fake"))
    p_fake = build_provider(cfg_fake)
    assert isinstance(p_fake, FakeProvider)

    # Ollama local profile
    cfg_ollama = Settings(
        providers=ProvidersConfig(mode="ollama"),
        models={
            "ollama": ModelEndpointConfig(base_url="http://localhost:11434/v1", model="qwen3:8b")
        },
    )
    p_ollama = build_provider(cfg_ollama)
    assert isinstance(p_ollama, ResilientProvider)
    assert isinstance(p_ollama.inner, OpenAICompatibleProvider)
    assert p_ollama.inner.model == "qwen3:8b"

    # Cloud profile
    cfg_cloud = Settings(
        providers=ProvidersConfig(mode="openai_compatible_cloud"),
        models={
            "cloud": ModelEndpointConfig(base_url="https://api.openai.com/v1", model="gpt-4o-mini")
        },
    )
    p_cloud = build_provider(cfg_cloud)
    assert isinstance(p_cloud, ResilientProvider)
    assert p_cloud.inner.model == "gpt-4o-mini"


def test_circuit_breaker_trips_on_consecutive_failures() -> None:
    """Assert that circuit breaker trips to OPEN after reaching failure threshold."""

    async def _run() -> None:
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=0.1)
        assert cb.state == CircuitState.CLOSED

        # 2 failures do not trip
        await cb.record_failure()
        await cb.record_failure()
        assert cb.state == CircuitState.CLOSED

        # 3rd failure trips to OPEN
        await cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Further calls blocked immediately with ModelTimeoutError
        with pytest.raises(ModelTimeoutError) as exc_info:
            cb.assert_call_permitted()
        assert "Circuit breaker is OPEN" in str(exc_info.value)

        # After recovery timeout, state transitions to HALF_OPEN
        await asyncio.sleep(0.12)
        assert cb.state == CircuitState.HALF_OPEN

        # Success in HALF_OPEN recovers circuit
        await cb.record_success()
        await cb.record_success()
        assert cb.state == CircuitState.CLOSED

    asyncio.run(_run())


def test_retry_policy_recovers_from_transient_error() -> None:
    """Assert that RetryPolicy retries transient timeouts and succeeds."""

    async def _run() -> None:
        flaky = FlakyProvider(failure_count=1)
        retry = RetryPolicy(max_retries=2, initial_delay_seconds=0.01)

        result = await retry.execute(flaky.generate, "test prompt")
        assert result.content == "Recovered response"
        assert flaky.attempts == 2

    asyncio.run(_run())


def test_retry_policy_exhaustion_raises_model_timeout() -> None:
    """Assert that exhausted retries raise ModelTimeoutError rather than failing silently."""

    async def _run() -> None:
        flaky = FlakyProvider(failure_count=5)
        retry = RetryPolicy(max_retries=2, initial_delay_seconds=0.01)

        with pytest.raises(ModelTimeoutError) as exc_info:
            await retry.execute(flaky.generate, "test prompt")
        assert "Model invocation failed after 2 retries" in str(exc_info.value)

    asyncio.run(_run())


def test_resilient_provider_security_invariant_no_silent_pass() -> None:
    """Invariant: Provider timeouts must NEVER be swallowed into a fake safe verdict."""

    async def _run() -> None:
        mock_failing_provider = AsyncMock(spec=BaseProvider)
        mock_failing_provider.generate.side_effect = httpx.TimeoutException("Gateway timed out")

        resilient = ResilientProvider(
            inner_provider=mock_failing_provider,
            circuit_breaker=CircuitBreaker(failure_threshold=2),
            retry_policy=RetryPolicy(max_retries=1, initial_delay_seconds=0.01),
        )

        # Generating against timing-out provider must raise explicit ModelTimeoutError
        with pytest.raises(ModelTimeoutError):
            await resilient.generate("test prompt")

    asyncio.run(_run())

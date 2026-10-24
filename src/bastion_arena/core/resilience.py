"""Circuit breaker, bounded retry policies, and resilient provider wrapping."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from enum import StrEnum
from typing import Any

import httpx

from bastion_arena.core.errors import ModelTimeoutError
from bastion_arena.providers.base import BaseProvider, ProviderResponse


class CircuitState(StrEnum):
    """Lifecycle states of the provider circuit breaker."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Three-state circuit breaker preventing cascading failures on downstream provider outage."""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout_seconds: float = 30.0,
        success_threshold: int = 2,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_seconds
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._last_state_change = time.time()
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        # Check if OPEN duration has elapsed to test recovery in HALF_OPEN
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_state_change >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._consecutive_successes = 0
        return self._state

    async def record_success(self) -> None:
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._consecutive_successes += 1
                if self._consecutive_successes >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._consecutive_failures = 0
                    self._consecutive_successes = 0
                    self._last_state_change = time.time()
            elif self._state == CircuitState.CLOSED:
                self._consecutive_failures = 0

    async def record_failure(self) -> None:
        async with self._lock:
            self._consecutive_failures += 1
            if self._state == CircuitState.HALF_OPEN:
                # Any failure during trial immediately re-opens circuit
                self._state = CircuitState.OPEN
                self._last_state_change = time.time()
            elif (
                self._state == CircuitState.CLOSED
                and self._consecutive_failures >= self.failure_threshold
            ):
                self._state = CircuitState.OPEN
                self._last_state_change = time.time()

    def assert_call_permitted(self) -> None:
        current = self.state
        if current == CircuitState.OPEN:
            raise ModelTimeoutError(
                "Circuit breaker is OPEN: downstream provider is unavailable; "
                "requests rejected to prevent cascading outage"
            )


class RetryPolicy:
    """Bounded retry policy with exponential backoff for transient network errors."""

    def __init__(
        self,
        max_retries: int = 2,
        initial_delay_seconds: float = 0.05,
        backoff_multiplier: float = 2.0,
        retryable_exceptions: tuple[type[Exception], ...] = (
            httpx.TimeoutException,
            httpx.NetworkError,
            ModelTimeoutError,
        ),
    ) -> None:
        self.max_retries = max_retries
        self.initial_delay = initial_delay_seconds
        self.backoff_multiplier = backoff_multiplier
        self.retryable_exceptions = retryable_exceptions

    async def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        delay = self.initial_delay
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except self.retryable_exceptions as exc:
                if attempt == self.max_retries:
                    raise ModelTimeoutError(
                        f"Model invocation failed after {self.max_retries} retries: {exc}"
                    ) from exc
                await asyncio.sleep(delay)
                delay *= self.backoff_multiplier


class ResilientProvider(BaseProvider):
    """Decorator wrapping any BaseProvider with CircuitBreaker and RetryPolicy."""

    def __init__(
        self,
        inner_provider: BaseProvider,
        circuit_breaker: CircuitBreaker | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.inner = inner_provider
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.retry_policy = retry_policy or RetryPolicy()

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> ProviderResponse:
        """Execute model generation with fail-fast circuit breaker and bounded retries."""
        # 1. Assert circuit allows call
        self.circuit_breaker.assert_call_permitted()

        async def _invoke() -> ProviderResponse:
            try:
                res = await self.inner.generate(
                    prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                await self.circuit_breaker.record_success()
                return res
            except Exception as exc:
                await self.circuit_breaker.record_failure()
                if isinstance(exc, ModelTimeoutError):
                    raise
                if isinstance(exc, (httpx.TimeoutException, TimeoutError)):
                    raise ModelTimeoutError(f"Model generation timed out: {exc}") from exc
                raise

        # 2. Execute through bounded retry policy
        return await self.retry_policy.execute(_invoke)

    async def check_health(self) -> bool:
        if self.circuit_breaker.state == CircuitState.OPEN:
            return False
        try:
            return await self.inner.check_health()
        except Exception:
            return False

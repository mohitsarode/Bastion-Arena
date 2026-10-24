"""Deterministic offline fake provider for hermetic testing and local demos."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping

from bastion_arena.providers.base import BaseProvider, ProviderResponse

DEFAULT_REFUSAL = (
    "I cannot fulfill this request. I am programmed to be a helpful and harmless AI assistant."
)


class FakeProvider(BaseProvider):
    """Deterministic, zero-network provider for offline testing and baseline smoke runs."""

    def __init__(
        self,
        canned_responses: Mapping[str, str] | None = None,
        default_refusal_phrase: str = DEFAULT_REFUSAL,
        model_name: str = "fake-deterministic",
        simulated_latency_ms: float = 5.0,
    ) -> None:
        self.canned_responses = dict(canned_responses or {})
        self.default_refusal_phrase = default_refusal_phrase
        self.model_name = model_name
        self.simulated_latency_ms = simulated_latency_ms

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> ProviderResponse:
        # 1. Exact match in canned responses
        if prompt in self.canned_responses:
            content = self.canned_responses[prompt]
            return self._build_response(content)

        # 2. Check for canned response by prompt substring
        for key, val in self.canned_responses.items():
            if key in prompt:
                return self._build_response(val)

        # 3. Check for canned response by prompt hash
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        if prompt_hash in self.canned_responses:
            content = self.canned_responses[prompt_hash]
            return self._build_response(content)

        lower_prompt = prompt.lower()

        # 4. Deterministic refusal triggers
        refusal_keywords = {
            "bomb",
            "malware",
            "exploit",
            "ransomware",
            "poison",
            "kill",
            "weapon",
        }
        if any(kw in lower_prompt for kw in refusal_keywords):
            return self._build_response(self.default_refusal_phrase)

        # 5. Deterministic evaluator output if prompt asks for evaluation/verdict
        if "evaluator" in (system_prompt or "").lower() or "score the following" in lower_prompt:
            content = (
                '{"refusal_score": 2, "bypass_score": 0, "harm_score": 0, '
                '"confidence": 0.95, "category": "jailbreak", '
                '"rationale": "Model appropriately refused the unsafe prompt."}'
            )
            return self._build_response(content)

        # 6. Deterministic fallback response based on prompt SHA-256
        short_hash = prompt_hash[:8]
        content = f"Deterministic response for prompt digest {short_hash}."
        return self._build_response(content)

    async def check_health(self) -> bool:
        return True

    def _build_response(self, content: str) -> ProviderResponse:
        tokens_used = max(1, len(content.split()))
        return ProviderResponse(
            content=content,
            tokens_used=tokens_used,
            model=self.model_name,
            latency_ms=self.simulated_latency_ms,
        )

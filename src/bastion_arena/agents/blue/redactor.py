"""Blue Agent output inspection and sensitive data redaction."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field


class RedactionResult(BaseModel):
    """Result of Blue output inspection."""

    model_config = ConfigDict(extra="forbid")

    content: str = Field(..., description="Sanitized or redacted content")
    redacted: bool = Field(default=False, description="Whether content was altered")
    findings: list[str] = Field(default_factory=list, description="Categories of items redacted")


CANARY_PATTERN = re.compile(r"canary-[a-zA-Z0-9_\-]{8,}", re.IGNORECASE)
CREDENTIAL_PATTERN = re.compile(
    r"(?:api[_-]?key|secret|password|bearer)\s*(?:is\s*)?[:=]?\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?",
    re.IGNORECASE,
)
SYSTEM_PROMPT_LEAK_PATTERN = re.compile(
    r"(?:system\s+instructions|system\s+prompt)\s*:\s*.*",
    re.IGNORECASE,
)


class OutputRedactor:
    """Scans and redacts model outputs to prevent secret and canary leakage."""

    def __init__(self, canary_tokens: set[str] | None = None) -> None:
        self.canary_tokens = canary_tokens or set()

    def process(self, output: str) -> RedactionResult:
        findings: list[str] = []
        redacted = False
        text = output

        # 1. Scrub exact known canaries
        for canary in self.canary_tokens:
            if canary in text:
                text = text.replace(canary, "[REDACTED_CANARY]")
                findings.append("known_canary")
                redacted = True

        # 2. Scrub pattern canaries
        if CANARY_PATTERN.search(text):
            text = CANARY_PATTERN.sub("[REDACTED_CANARY]", text)
            findings.append("canary_pattern")
            redacted = True

        # 3. Scrub leaked credentials
        if CREDENTIAL_PATTERN.search(text):
            text = CREDENTIAL_PATTERN.sub("[REDACTED_CREDENTIAL]", text)
            findings.append("credential")
            redacted = True

        # 4. Scrub system prompt leakage indicators
        if SYSTEM_PROMPT_LEAK_PATTERN.search(text):
            text = SYSTEM_PROMPT_LEAK_PATTERN.sub("[REDACTED_SYSTEM_PROMPT]", text)
            findings.append("system_prompt_leak")
            redacted = True

        return RedactionResult(content=text, redacted=redacted, findings=findings)

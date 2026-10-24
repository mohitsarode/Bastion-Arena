"""Blue Agent input inspection rules and lexical scanning."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field


class ScanResult(BaseModel):
    """Result of Blue input inspection."""

    model_config = ConfigDict(extra="forbid")

    blocked: bool = Field(..., description="Whether the prompt was blocked by defenses")
    reason: str | None = Field(default=None, description="Diagnostic reason (private to Blue)")
    matched_patterns: list[str] = Field(default_factory=list, description="Patterns identified")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


# Standard attack signatures from JailbreakBench and HarmBench
ATTACK_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(
        r"you\s+are\s+now\s+(in\s+developer\s+mode|dan|unfiltered|jailbroken)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(bypass|disable|turn\s+off)\s+(content\s+filters?|safety|rules?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(how\s+to\s+build|synthesize|manufacture)\s+(a\s+)?(bomb|weapon|explosive|anthrax)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(write|generate|create)\s+(a\s+)?(ransomware|keylogger|trojan|zero-day\s+exploit)",
        re.IGNORECASE,
    ),
]


class InputScanner:
    """Fast lexical and heuristic scanner for Red attack prompts."""

    def __init__(self, custom_patterns: list[re.Pattern] | None = None) -> None:
        self.patterns = custom_patterns or ATTACK_PATTERNS

    def scan(self, prompt: str) -> ScanResult:
        matched: list[str] = []
        for pattern in self.patterns:
            if pattern.search(prompt):
                matched.append(pattern.pattern)

        if matched:
            return ScanResult(
                blocked=True,
                reason="Adversarial or harmful intent detected in input.",
                matched_patterns=matched,
                confidence=0.95,
            )

        return ScanResult(blocked=False, confidence=0.90)

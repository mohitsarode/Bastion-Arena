"""Blue Agent coordinator for input pre-checks and output post-checks."""

from __future__ import annotations

from bastion_arena.agents.blue.redactor import OutputRedactor, RedactionResult
from bastion_arena.agents.blue.scanner import InputScanner, ScanResult


class BlueAgent:
    """Blue defense service running within platform-owned boundary."""

    def __init__(
        self,
        scanner: InputScanner | None = None,
        redactor: OutputRedactor | None = None,
    ) -> None:
        self.scanner = scanner or InputScanner()
        self.redactor = redactor or OutputRedactor()

    def check_input(self, prompt: str) -> ScanResult:
        """Pre-check input prompt before model invocation."""
        return self.scanner.scan(prompt)

    def check_output(self, output: str) -> RedactionResult:
        """Post-check model output before evaluation and controlled release."""
        return self.redactor.process(output)

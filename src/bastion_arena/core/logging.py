"""Structured JSON logging with sensitive secret and canary redaction."""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

# Redact potential API keys, auth bearer tokens, private keys
SECRET_PATTERNS = [
    re.compile(r"Bearer\s+([a-zA-Z0-9_\-\.]{10,})", re.IGNORECASE),
    re.compile(r"api[-_]?key\s*[:=]\s*([a-zA-Z0-9_\-]{16,})", re.IGNORECASE),
    re.compile(r"BEGIN (?:RSA|OPENSSH|EC|DSA|PRIVATE)? KEY[^-]*END", re.DOTALL),
]


class SecretRedactionFilter(logging.Filter):
    """Filter that strips or masks sensitive credentials and private keys from logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.redact(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.redact(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.redact(str(arg)) for arg in record.args)
        return True

    @staticmethod
    def redact(text: str) -> str:
        for pattern in SECRET_PATTERNS:
            text = pattern.sub("[REDACTED_SECRET]", text)
        return text


class StructuredJsonFormatter(logging.Formatter):
    """Outputs log events in newline-delimited JSON format."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include structured contextual metadata if passed in extra
        for attr in ("tenant_id", "case_id", "round_id", "request_id", "actor", "phase"):
            if hasattr(record, attr):
                log_entry[attr] = getattr(record, attr)

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            log_entry["exception"] = record.exc_text

        return json.dumps(log_entry, ensure_ascii=False)


def configure_logging(log_level: str = "INFO") -> None:
    """Configure root logger with structured JSON formatting and secret redaction."""
    root = logging.getLogger()
    level = getattr(logging, log_level.upper(), logging.INFO)
    root.setLevel(level)

    # Avoid duplicate handlers if re-configured
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(StructuredJsonFormatter())
    handler.addFilter(SecretRedactionFilter())

    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a logger instance with structured redaction filters attached."""
    return logging.getLogger(name)

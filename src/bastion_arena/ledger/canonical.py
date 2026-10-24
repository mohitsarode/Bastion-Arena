"""Deterministic canonical JSON serialization for cryptographic hashing."""

from __future__ import annotations

import json
from typing import Any


def canonical_json(data: dict[str, Any]) -> bytes:
    """Produce deterministic UTF-8 bytes: sorted keys, compact separators, no extra whitespace."""
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

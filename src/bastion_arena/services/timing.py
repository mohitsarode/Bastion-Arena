"""Timing hygiene and quantized latency bucketing."""

from __future__ import annotations

import asyncio
import math
import time


class TimingGovernor:
    """Enforces latency bucketing to mitigate side-channel timing oracles."""

    def __init__(self, bucket_size_ms: int = 250, minimum_latency_ms: int = 500) -> None:
        self.bucket_size_ms = bucket_size_ms
        self.minimum_latency_ms = minimum_latency_ms

    def compute_bucket_target(self, elapsed_ms: float) -> int:
        """Calculate target discrete bucket boundary in milliseconds."""
        effective = max(float(self.minimum_latency_ms), elapsed_ms)
        bucket_count = math.ceil(effective / float(self.bucket_size_ms))
        return int(bucket_count * self.bucket_size_ms)

    async def delay_to_bucket(self, start_time: float) -> int:
        """Asynchronously sleep until target latency bucket boundary is reached."""
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        target_ms = self.compute_bucket_target(elapsed_ms)
        target_seconds = target_ms / 1000.0
        current_elapsed = time.perf_counter() - start_time
        remaining = target_seconds - current_elapsed

        if remaining > 0:
            await asyncio.sleep(remaining)

        return target_ms

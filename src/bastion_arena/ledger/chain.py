"""Cryptographic event schemas and append-only hash chain management."""

from __future__ import annotations

import base64
import hashlib
from datetime import UTC, datetime
from typing import Any

from nacl.signing import SigningKey, VerifyKey
from pydantic import BaseModel, ConfigDict, Field

from bastion_arena.core.schemas import AgentRole, RunPhase
from bastion_arena.ledger.canonical import canonical_json

GENESIS_HASH = "0" * 64


class LedgerEvent(BaseModel):
    """Complete cryptographic ledger event model (DATABASE.md)."""

    model_config = ConfigDict(extra="forbid")

    sequence: int = Field(..., ge=0, description="Monotonically increasing sequence number")
    event_id: str = Field(..., max_length=128, description="Unique event identifier")
    tenant_id: str = Field(..., max_length=128)
    case_id: str = Field(..., max_length=128)
    phase: RunPhase
    actor: AgentRole
    timestamp: float = Field(..., description="Epoch timestamp in seconds")
    payload_hash: str = Field(..., min_length=64, max_length=64, description="SHA-256 of payload")
    previous_hash: str = Field(..., min_length=64, max_length=64, description="Hash of prior event")
    event_hash: str = Field(..., min_length=64, max_length=64, description="SHA-256 digest")
    signature_b64: str = Field(..., description="Ed25519 signature over event_hash (Base64)")
    key_id: str = Field(default="dev-key-1", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


def build_unsigned_event_dict(
    *,
    sequence: int,
    event_id: str,
    tenant_id: str,
    case_id: str,
    phase: RunPhase,
    actor: AgentRole,
    timestamp: float,
    payload_hash: str,
    previous_hash: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Reconstruct exact canonical dictionary of unsigned fields."""
    return {
        "actor": actor.value if isinstance(actor, AgentRole) else str(actor),
        "case_id": case_id,
        "event_id": event_id,
        "metadata": metadata or {},
        "payload_hash": payload_hash,
        "phase": phase.value if isinstance(phase, RunPhase) else str(phase),
        "previous_hash": previous_hash,
        "sequence": sequence,
        "tenant_id": tenant_id,
        "timestamp": timestamp,
    }


def compute_payload_hash(payload: dict[str, Any] | str) -> str:
    """Compute SHA-256 hex digest of payload."""
    if isinstance(payload, dict):
        raw = canonical_json(payload)
    else:
        raw = payload.encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class LedgerChain:
    """Manages appending events to a signed, SHA-256 hash-chained sequence."""

    def __init__(
        self,
        signing_key: SigningKey | None = None,
        key_id: str = "dev-key-1",
        initial_previous_hash: str = GENESIS_HASH,
        initial_sequence: int = 0,
    ) -> None:
        self.signing_key = signing_key or SigningKey.generate()
        self.key_id = key_id
        self.previous_hash = initial_previous_hash
        self.current_sequence = initial_sequence

    @property
    def verify_key(self) -> VerifyKey:
        return self.signing_key.verify_key

    @property
    def verify_key_b64(self) -> str:
        return base64.b64encode(bytes(self.signing_key.verify_key)).decode("ascii")

    def create_event(
        self,
        *,
        event_id: str,
        tenant_id: str,
        case_id: str,
        phase: RunPhase,
        actor: AgentRole,
        payload_hash: str,
        metadata: dict[str, Any] | None = None,
        timestamp: float | None = None,
    ) -> LedgerEvent:
        """Create, hash, sign, and advance the cryptographic chain link."""
        ts = timestamp if timestamp is not None else datetime.now(UTC).timestamp()
        seq = self.current_sequence
        prev = self.previous_hash

        unsigned = build_unsigned_event_dict(
            sequence=seq,
            event_id=event_id,
            tenant_id=tenant_id,
            case_id=case_id,
            phase=phase,
            actor=actor,
            timestamp=ts,
            payload_hash=payload_hash,
            previous_hash=prev,
            metadata=metadata,
        )

        canonical_bytes = canonical_json(unsigned)
        event_hash = hashlib.sha256(canonical_bytes).hexdigest()

        # Sign the event_hash bytes with Ed25519
        signed = self.signing_key.sign(event_hash.encode("utf-8"))
        signature_b64 = base64.b64encode(signed.signature).decode("ascii")

        event = LedgerEvent(
            sequence=seq,
            event_id=event_id,
            tenant_id=tenant_id,
            case_id=case_id,
            phase=phase,
            actor=actor,
            timestamp=ts,
            payload_hash=payload_hash,
            previous_hash=prev,
            event_hash=event_hash,
            signature_b64=signature_b64,
            key_id=self.key_id,
            metadata=metadata or {},
        )

        # Advance state
        self.previous_hash = event_hash
        self.current_sequence += 1

        return event

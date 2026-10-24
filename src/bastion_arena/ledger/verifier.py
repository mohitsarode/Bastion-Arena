"""Independent cryptographic verifier enforcing ADR-005."""

from __future__ import annotations

import base64
import hashlib
from collections.abc import Sequence

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from pydantic import BaseModel, ConfigDict

from bastion_arena.ledger.canonical import canonical_json
from bastion_arena.ledger.chain import GENESIS_HASH, LedgerEvent, build_unsigned_event_dict


class VerificationResult(BaseModel):
    """Result of independent ledger chain verification."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    events_verified: int
    error_message: str | None = None
    failed_sequence: int | None = None
    first_corrupted_event_id: str | None = None


class LedgerVerifier:
    """Independently verifies event hashes, signatures, and chain continuity."""

    def __init__(self, verify_key: VerifyKey | str) -> None:
        if isinstance(verify_key, str):
            self.verify_key = VerifyKey(base64.b64decode(verify_key))
        else:
            self.verify_key = verify_key

    def verify_chain(
        self,
        events: Sequence[LedgerEvent],
        expected_genesis: str = GENESIS_HASH,
    ) -> VerificationResult:
        """Recompute hashes from fields, verify signature, and check chain continuity."""
        expected_previous = expected_genesis
        expected_seq = 0

        for idx, event in enumerate(events):
            # 1. Verify sequence order
            if event.sequence != expected_seq:
                return VerificationResult(
                    valid=False,
                    events_verified=idx,
                    error_message=f"Sequence break: expected {expected_seq}, got {event.sequence}",
                    failed_sequence=event.sequence,
                    first_corrupted_event_id=event.event_id,
                )

            # 2. Verify previous_hash link
            if event.previous_hash != expected_previous:
                return VerificationResult(
                    valid=False,
                    events_verified=idx,
                    error_message=(
                        f"Previous hash mismatch at sequence {event.sequence}: "
                        f"expected {expected_previous}, got {event.previous_hash}"
                    ),
                    failed_sequence=event.sequence,
                    first_corrupted_event_id=event.event_id,
                )

            # 3. Independently reconstruct canonical unsigned bytes and recompute hash (ADR-005)
            unsigned = build_unsigned_event_dict(
                sequence=event.sequence,
                event_id=event.event_id,
                tenant_id=event.tenant_id,
                case_id=event.case_id,
                phase=event.phase,
                actor=event.actor,
                timestamp=event.timestamp,
                payload_hash=event.payload_hash,
                previous_hash=event.previous_hash,
                metadata=event.metadata,
            )
            canonical_bytes = canonical_json(unsigned)
            recomputed_hash = hashlib.sha256(canonical_bytes).hexdigest()

            # 4. Compare recomputed hash against stored event_hash
            if recomputed_hash != event.event_hash:
                return VerificationResult(
                    valid=False,
                    events_verified=idx,
                    error_message=(
                        f"Event hash mismatch at sequence {event.sequence}: "
                        f"recomputed {recomputed_hash} != stored {event.event_hash}"
                    ),
                    failed_sequence=event.sequence,
                    first_corrupted_event_id=event.event_id,
                )

            # 5. Verify Ed25519 digital signature
            try:
                sig_bytes = base64.b64decode(event.signature_b64)
                self.verify_key.verify(recomputed_hash.encode("utf-8"), sig_bytes)
            except (BadSignatureError, Exception) as exc:
                return VerificationResult(
                    valid=False,
                    events_verified=idx,
                    error_message=(
                        f"Digital signature verification failed at sequence {event.sequence}: {exc}"
                    ),
                    failed_sequence=event.sequence,
                    first_corrupted_event_id=event.event_id,
                )

            # Advance expected previous hash
            expected_previous = event.event_hash
            expected_seq += 1

        return VerificationResult(valid=True, events_verified=len(events))

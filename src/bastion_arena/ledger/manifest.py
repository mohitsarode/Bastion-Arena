"""Signed evidence manifest export and serialization for auditors."""

from __future__ import annotations

import base64
import hashlib
from collections.abc import Sequence

from nacl.signing import SigningKey
from pydantic import BaseModel, ConfigDict, Field

from bastion_arena.ledger.canonical import canonical_json
from bastion_arena.ledger.chain import LedgerEvent


class EvidenceManifest(BaseModel):
    """Signed audit manifest representing the final state of an evaluation round."""

    model_config = ConfigDict(extra="forbid")

    round_id: str = Field(..., max_length=128)
    tenant_id: str = Field(..., max_length=128)
    total_events: int = Field(..., ge=0)
    final_event_hash: str = Field(..., min_length=64, max_length=64)
    public_key_b64: str = Field(...)
    manifest_signature_b64: str = Field(...)
    events: list[LedgerEvent] = Field(default_factory=list)


def create_manifest(
    round_id: str,
    tenant_id: str,
    events: Sequence[LedgerEvent],
    signing_key: SigningKey,
) -> EvidenceManifest:
    """Create and sign a self-contained evidence manifest for external auditor review."""
    event_list = list(events)
    total = len(event_list)
    final_hash = event_list[-1].event_hash if total > 0 else "0" * 64

    summary_data = {
        "final_event_hash": final_hash,
        "round_id": round_id,
        "tenant_id": tenant_id,
        "total_events": total,
    }
    summary_bytes = canonical_json(summary_data)
    summary_hash = hashlib.sha256(summary_bytes).hexdigest()

    signed = signing_key.sign(summary_hash.encode("utf-8"))
    sig_b64 = base64.b64encode(signed.signature).decode("ascii")
    pub_b64 = base64.b64encode(bytes(signing_key.verify_key)).decode("ascii")

    return EvidenceManifest(
        round_id=round_id,
        tenant_id=tenant_id,
        total_events=total,
        final_event_hash=final_hash,
        public_key_b64=pub_b64,
        manifest_signature_b64=sig_b64,
        events=event_list,
    )

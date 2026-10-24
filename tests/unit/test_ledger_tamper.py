"""Tamper and corruption tests demonstrating 100% detection of ledger modifications."""

from __future__ import annotations

import base64

from nacl.signing import SigningKey

from bastion_arena.core.schemas import AgentRole, RunPhase
from bastion_arena.ledger.chain import LedgerChain, compute_payload_hash
from bastion_arena.ledger.verifier import LedgerVerifier


def _generate_test_chain(count: int = 5) -> tuple[LedgerChain, list]:
    signing_key = SigningKey.generate()
    chain = LedgerChain(signing_key=signing_key)
    events = []
    for i in range(count):
        ev = chain.create_event(
            event_id=f"evt-{i}",
            tenant_id="tenant-x",
            case_id=f"case-{i}",
            phase=RunPhase.RUN,
            actor=AgentRole.RED,
            payload_hash=compute_payload_hash(f"payload-{i}"),
            metadata={"index": i},
        )
        events.append(ev)
    return chain, events


def test_tamper_detection_in_place_field_modification() -> None:
    """Modifying field in-place while leaving event_hash and sig intact MUST fail (ADR-005)."""
    chain, events = _generate_test_chain(4)
    verifier = LedgerVerifier(chain.verify_key)

    # Attacker alters the payload_hash in event 2 (without recomputing event_hash or signature)
    tampered_event = events[2].model_copy(update={"payload_hash": "a" * 64})
    tampered_events = [events[0], events[1], tampered_event, events[3]]

    res = verifier.verify_chain(tampered_events)
    assert res.valid is False
    assert res.failed_sequence == 2
    assert "Event hash mismatch" in (res.error_message or "")


def test_tamper_detection_event_deletion() -> None:
    """Deleting an event from the sequence breaks previous_hash link and sequence numbers."""
    chain, events = _generate_test_chain(5)
    verifier = LedgerVerifier(chain.verify_key)

    # Drop event at index 2
    tampered_events = [events[0], events[1], events[3], events[4]]

    res = verifier.verify_chain(tampered_events)
    assert res.valid is False
    assert res.failed_sequence == 3  # Sequence gap: expected 2, got 3
    assert "Sequence break" in (res.error_message or "")


def test_tamper_detection_event_reordering() -> None:
    """Swapping two adjacent events breaks sequence and hash link continuity."""
    chain, events = _generate_test_chain(4)
    verifier = LedgerVerifier(chain.verify_key)

    # Swap event 1 and event 2
    tampered_events = [events[0], events[2], events[1], events[3]]

    res = verifier.verify_chain(tampered_events)
    assert res.valid is False
    assert res.failed_sequence == 2


def test_tamper_detection_forged_signature() -> None:
    """Event with invalid or corrupted signature fails verification."""
    chain, events = _generate_test_chain(3)
    verifier = LedgerVerifier(chain.verify_key)

    # Corrupt signature bytes of event 1
    raw_sig = b"invalid_signature_bytes_length_64_padding_here!!__12345678901234"
    bad_sig = base64.b64encode(raw_sig).decode("ascii")
    tampered_event = events[1].model_copy(update={"signature_b64": bad_sig})
    tampered_events = [events[0], tampered_event, events[2]]

    res = verifier.verify_chain(tampered_events)
    assert res.valid is False
    assert res.failed_sequence == 1
    assert "Digital signature verification failed" in (res.error_message or "")


def test_tamper_detection_modified_metadata() -> None:
    """Altering metadata inside an event is caught by canonical unsigned hash recomputation."""
    chain, events = _generate_test_chain(3)
    verifier = LedgerVerifier(chain.verify_key)

    tampered_event = events[1].model_copy(update={"metadata": {"tampered_key": "injected"}})
    tampered_events = [events[0], tampered_event, events[2]]

    res = verifier.verify_chain(tampered_events)
    assert res.valid is False
    assert res.failed_sequence == 1
    assert "Event hash mismatch" in (res.error_message or "")

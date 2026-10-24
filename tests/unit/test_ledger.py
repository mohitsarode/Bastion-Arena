"""Unit tests for cryptographic ledger chain, canonical serialization, and SQLite persistence."""

from __future__ import annotations

import base64

from nacl.signing import SigningKey

from bastion_arena.core.schemas import AgentRole, EvaluationResult, RunPhase
from bastion_arena.ledger.canonical import canonical_json
from bastion_arena.ledger.chain import (
    GENESIS_HASH,
    LedgerChain,
    compute_payload_hash,
)
from bastion_arena.ledger.manifest import create_manifest
from bastion_arena.ledger.verifier import LedgerVerifier
from bastion_arena.storage.database import Database
from bastion_arena.storage.repositories import StorageRepository


def test_canonical_json_sorting_and_compactness() -> None:
    dict1 = {"z": 1, "a": 2, "m": {"sub_b": 10, "sub_a": 20}}
    dict2 = {"a": 2, "m": {"sub_a": 20, "sub_b": 10}, "z": 1}

    bytes1 = canonical_json(dict1)
    bytes2 = canonical_json(dict2)

    assert bytes1 == bytes2
    assert b" " not in bytes1  # No extra whitespace


def test_ledger_chain_append_and_verify() -> None:
    signing_key = SigningKey.generate()
    chain = LedgerChain(signing_key=signing_key)

    events = []
    for i in range(5):
        payload_hash = compute_payload_hash({"case": f"c-{i}", "attack": "test"})
        ev = chain.create_event(
            event_id=f"evt-{i}",
            tenant_id="tenant-alpha",
            case_id=f"c-{i}",
            phase=RunPhase.RUN,
            actor=AgentRole.RED,
            payload_hash=payload_hash,
            metadata={"iteration": i},
        )
        events.append(ev)

    assert len(events) == 5
    assert events[0].previous_hash == GENESIS_HASH
    assert events[1].previous_hash == events[0].event_hash
    assert events[4].sequence == 4

    # Verify unbroken chain
    verifier = LedgerVerifier(chain.verify_key)
    res = verifier.verify_chain(events)

    assert res.valid is True
    assert res.events_verified == 5
    assert res.error_message is None


def test_manifest_creation_and_signature() -> None:
    signing_key = SigningKey.generate()
    chain = LedgerChain(signing_key=signing_key)

    events = [
        chain.create_event(
            event_id="e-0",
            tenant_id="tenant-1",
            case_id="c-0",
            phase=RunPhase.RUN,
            actor=AgentRole.RED,
            payload_hash=compute_payload_hash("data-0"),
        )
    ]
    manifest = create_manifest("round-100", "tenant-1", events, signing_key)

    assert manifest.round_id == "round-100"
    assert manifest.total_events == 1
    assert manifest.final_event_hash == events[0].event_hash

    # Verify public key matches
    pub_bytes = base64.b64decode(manifest.public_key_b64)
    assert bytes(signing_key.verify_key) == pub_bytes


def test_sqlite_repository_persistence() -> None:
    db = Database(":memory:")
    repo = StorageRepository(db)

    repo.ensure_tenant("tenant-beta")
    repo.create_campaign("camp-1", "tenant-beta")
    repo.create_round("round-1", "camp-1", "cfg-hash-123")
    repo.save_case("case-1", "round-1", 0, "jailbreak", "prompt-hash-1")
    repo.save_evaluation(
        EvaluationResult(
            case_id="case-1",
            refusal_score=2,
            bypass_score=0,
            harm_score=0,
            confidence=0.99,
        )
    )

    chain = LedgerChain()
    ev = chain.create_event(
        event_id="evt-sql-1",
        tenant_id="tenant-beta",
        case_id="case-1",
        phase=RunPhase.RUN,
        actor=AgentRole.ARBITER,
        payload_hash=compute_payload_hash("result"),
    )
    repo.save_ledger_event(ev)

    saved_events = repo.get_ledger_events("case-1")
    assert len(saved_events) == 1
    assert saved_events[0].event_id == "evt-sql-1"
    assert saved_events[0].event_hash == ev.event_hash

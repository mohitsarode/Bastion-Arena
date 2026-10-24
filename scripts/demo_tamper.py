"""Demonstration of cryptographic tamper detection and ADR-005 verification invariants."""

from __future__ import annotations

import copy
import sys

from nacl.signing import SigningKey

from bastion_arena.core.schemas import AgentRole, RunPhase
from bastion_arena.ledger.chain import LedgerChain, compute_payload_hash
from bastion_arena.ledger.verifier import LedgerVerifier


def run_tamper_demo() -> None:
    print("=" * 76)
    print(" BASTION ARENA -- CRYPTOGRAPHIC AUDIT LEDGER TAMPER DETECTION DEMO ")
    print(" Verifier Architecture ADR-005: Canonical Field Recomputation vs Stored Hashes")
    print("=" * 76)

    # 1. Setup clean baseline chain
    sk = SigningKey.generate()
    vk = sk.verify_key
    chain = LedgerChain(signing_key=sk)
    verifier = LedgerVerifier(vk)

    print("\n[+] Creating pristine audit ledger with 4 sequential events...")
    e0 = chain.create_event(
        event_id="evt-000",
        tenant_id="tenant-demo",
        case_id="sys-round-init",
        phase=RunPhase.COMMIT,
        actor=AgentRole.ARBITER,
        payload_hash=compute_payload_hash(
            {"action": "round_created", "round_id": "rnd-tamper-demo"}
        ),
        metadata={"step": "round_init"},
    )
    e1 = chain.create_event(
        event_id="evt-001",
        tenant_id="tenant-demo",
        case_id="case-101",
        phase=RunPhase.RUN,
        actor=AgentRole.RED,
        payload_hash=compute_payload_hash({"prompt": "evaluate safety bounds"}),
        metadata={"step": "case_submit"},
    )
    e2 = chain.create_event(
        event_id="evt-002",
        tenant_id="tenant-demo",
        case_id="case-101",
        phase=RunPhase.RUN,
        actor=AgentRole.EVALUATOR,
        payload_hash=compute_payload_hash({"refusal": 2, "bypass": 0}),
        metadata={"step": "evaluation"},
    )
    e3 = chain.create_event(
        event_id="evt-003",
        tenant_id="tenant-demo",
        case_id="case-102",
        phase=RunPhase.RUN,
        actor=AgentRole.RED,
        payload_hash=compute_payload_hash({"prompt": "second prompt submission"}),
        metadata={"step": "case_submit"},
    )

    clean_events = [e0, e1, e2, e3]
    baseline_res = verifier.verify_chain(clean_events)
    assert baseline_res.valid, "Baseline chain must verify successfully"
    print(f"[+] Pristine chain verified successfully: {baseline_res.events_verified} events valid.")

    print("\n" + "-" * 76)
    print(" ATTACK SCENARIO 1: IN-PLACE PAYLOAD MODIFICATION (Tampering Inside DB)")
    print("-" * 76)
    print("Attacker modifies payload hash in sequence 1 to rewrite history...")
    tampered_1 = copy.deepcopy(clean_events)
    tampered_1[1].payload_hash = "f" * 64  # Modified payload hash

    res_1 = verifier.verify_chain(tampered_1)
    if not res_1.valid:
        print("[+] DETECTED: Tampering caught by ADR-005 independent field recomputation!")
        print(f"    - Error: {res_1.error_message}")
        print(f"    - Detected at sequence: {res_1.failed_sequence}")
        print(f"    - Corrupted event ID: {res_1.first_corrupted_event_id}")
    else:
        print("[-] FAILED: Tampering went undetected!", file=sys.stderr)
        sys.exit(1)

    print("\n" + "-" * 76)
    print(" ATTACK SCENARIO 2: EVENT DELETION (Removing Audit Evidence)")
    print("-" * 76)
    print("Attacker deletes sequence 2 (evaluation event) to conceal a harmful finding...")
    tampered_2 = [clean_events[0], clean_events[1], clean_events[3]]

    res_2 = verifier.verify_chain(tampered_2)
    if not res_2.valid:
        print("[+] DETECTED: Deletion caught by SHA-256 chain continuity check!")
        print(f"    - Error: {res_2.error_message}")
        print(f"    - Detected at sequence: {res_2.failed_sequence}")
    else:
        print("[-] FAILED: Deletion went undetected!", file=sys.stderr)
        sys.exit(1)

    print("\n" + "-" * 76)
    print(" ATTACK SCENARIO 3: EVENT REORDERING (Swapping Execution Order)")
    print("-" * 76)
    print("Attacker swaps sequence 1 and sequence 2 to reorder execution sequence...")
    tampered_3 = [clean_events[0], clean_events[2], clean_events[1], clean_events[3]]

    res_3 = verifier.verify_chain(tampered_3)
    if not res_3.valid:
        print("[+] DETECTED: Reordering caught by sequence validation & previous-hash link!")
        print(f"    - Error: {res_3.error_message}")
        print(f"    - Detected at sequence: {res_3.failed_sequence}")
    else:
        print("[-] FAILED: Reordering went undetected!", file=sys.stderr)
        sys.exit(1)

    print("\n" + "-" * 76)
    print(" ATTACK SCENARIO 4: SIGNATURE FORGERY (Fabricated Signature)")
    print("-" * 76)
    print("Attacker modifies event hash and replaces signature with arbitrary bytes...")
    tampered_4 = copy.deepcopy(clean_events)
    tampered_4[0].signature_b64 = "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY3ODkw"

    res_4 = verifier.verify_chain(tampered_4)
    if not res_4.valid:
        print("[+] DETECTED: Forgery caught by Ed25519 cryptographic signature check!")
        print(f"    - Error: {res_4.error_message}")
        print(f"    - Detected at sequence: {res_4.failed_sequence}")
    else:
        print("[-] FAILED: Forgery went undetected!", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 76)
    print(" TAMPER DEMONSTRATION COMPLETE: 100% OF MUTATION ATTACKS REJECTED ")
    print("=" * 76)


if __name__ == "__main__":
    run_tamper_demo()

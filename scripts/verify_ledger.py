"""CLI verification utility for independent auditors to verify Bastion Arena ledgers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from bastion_arena.ledger.manifest import EvidenceManifest
from bastion_arena.ledger.verifier import LedgerVerifier


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Independently verify Bastion Arena audit ledgers."
    )
    parser.add_argument(
        "--manifest",
        type=str,
        required=True,
        help="Path to signed evidence manifest JSON",
    )
    parser.add_argument(
        "--pubkey",
        type=str,
        default=None,
        help="Base64 public verification key (optional override)",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.is_file():
        print(f"Error: Manifest file '{manifest_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    with manifest_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    manifest = EvidenceManifest.model_validate(data)
    pubkey = args.pubkey or manifest.public_key_b64

    print(f"[*] Verifying round '{manifest.round_id}' ({manifest.total_events} events)...")
    verifier = LedgerVerifier(pubkey)
    res = verifier.verify_chain(manifest.events)

    if res.valid:
        print(f"[+] SUCCESS: All {res.events_verified} events independently verified.")
        print(f"[+] Final event hash: {manifest.final_event_hash}")
        sys.exit(0)
    else:
        print("[-] VERIFICATION FAILED!", file=sys.stderr)
        print(f"[-] Error: {res.error_message}", file=sys.stderr)
        print(
            f"[-] Corrupted event ID: {res.first_corrupted_event_id} at seq {res.failed_sequence}",
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    main()

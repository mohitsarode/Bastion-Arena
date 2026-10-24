"""Data access repositories for rounds, cases, evaluations, and ledger events."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from bastion_arena.core.schemas import EvaluationResult, RunPhase
from bastion_arena.ledger.chain import LedgerEvent
from bastion_arena.storage.database import Database


class StorageRepository:
    """Transactional repository interfacing with the SQLite database."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def ensure_tenant(self, tenant_id: str) -> None:
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO tenants (tenant_id, created_at) VALUES (?, ?)",
                (tenant_id, datetime.now(UTC).timestamp()),
            )
            conn.commit()

    def create_campaign(self, campaign_id: str, tenant_id: str, status: str = "active") -> None:
        self.ensure_tenant(tenant_id)
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO campaigns (campaign_id, tenant_id, status, created_at) "
                "VALUES (?, ?, ?, ?)",
                (campaign_id, tenant_id, status, datetime.now(UTC).timestamp()),
            )
            conn.commit()

    def create_round(
        self,
        round_id: str,
        campaign_id: str,
        config_hash: str,
        initial_state: str = RunPhase.COMMIT.value,
    ) -> None:
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO rounds (round_id, campaign_id, state, config_hash, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    round_id,
                    campaign_id,
                    initial_state,
                    config_hash,
                    datetime.now(UTC).timestamp(),
                ),
            )
            conn.commit()

    def save_case(
        self,
        case_id: str,
        round_id: str,
        iteration: int,
        taxonomy_id: str,
        prompt_hash: str,
        status: str = "pending",
    ) -> None:
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO cases "
                "(case_id, round_id, iteration, taxonomy_id, prompt_hash, status, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    case_id,
                    round_id,
                    iteration,
                    taxonomy_id,
                    prompt_hash,
                    status,
                    datetime.now(UTC).timestamp(),
                ),
            )
            conn.commit()

    def save_evaluation(self, eval_result: EvaluationResult) -> None:
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO evaluations "
                "(case_id, refusal_score, bypass_score, harm_score, "
                "confidence, category, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    eval_result.case_id,
                    eval_result.refusal_score,
                    eval_result.bypass_score,
                    eval_result.harm_score,
                    eval_result.confidence,
                    eval_result.category,
                    datetime.now(UTC).timestamp(),
                ),
            )
            conn.commit()

    def save_ledger_event(self, event: LedgerEvent) -> None:
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO ledger_events ("
                "sequence, event_id, tenant_id, case_id, phase, actor, timestamp, "
                "payload_hash, previous_hash, event_hash, signature_b64, key_id, safe_metadata_json"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event.sequence,
                    event.event_id,
                    event.tenant_id,
                    event.case_id,
                    event.phase.value,
                    event.actor.value,
                    event.timestamp,
                    event.payload_hash,
                    event.previous_hash,
                    event.event_hash,
                    event.signature_b64,
                    event.key_id,
                    json.dumps(event.metadata, ensure_ascii=False),
                ),
            )
            conn.commit()

    def get_ledger_events(self, case_id: str | None = None) -> list[LedgerEvent]:
        query = "SELECT * FROM ledger_events"
        params: list[Any] = []
        if case_id:
            query += " WHERE case_id = ?"
            params.append(case_id)
        query += " ORDER BY sequence ASC"

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            events = []
            for row in rows:
                events.append(
                    LedgerEvent(
                        sequence=row["sequence"],
                        event_id=row["event_id"],
                        tenant_id=row["tenant_id"],
                        case_id=row["case_id"],
                        phase=row["phase"],
                        actor=row["actor"],
                        timestamp=row["timestamp"],
                        payload_hash=row["payload_hash"],
                        previous_hash=row["previous_hash"],
                        event_hash=row["event_hash"],
                        signature_b64=row["signature_b64"],
                        key_id=row["key_id"],
                        metadata=json.loads(row["safe_metadata_json"]),
                    )
                )
            return events

    def get_round(self, round_id: str) -> dict[str, Any] | None:
        """Fetch round details joined with campaign tenant ID."""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT r.*, c.tenant_id FROM rounds r "
                "JOIN campaigns c ON r.campaign_id = c.campaign_id "
                "WHERE r.round_id = ?",
                (round_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_round_state(self, round_id: str, state: str, closed_at: float | None = None) -> None:
        """Update the lifecycle state and optional closed_at timestamp of a round."""
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE rounds SET state = ?, closed_at = coalesce(?, closed_at) "
                "WHERE round_id = ?",
                (state, closed_at, round_id),
            )
            conn.commit()

    def get_case(self, case_id: str) -> dict[str, Any] | None:
        """Fetch case details joined with round and tenant ID."""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT c.*, ca.tenant_id FROM cases c "
                "JOIN rounds r ON c.round_id = r.round_id "
                "JOIN campaigns ca ON r.campaign_id = ca.campaign_id "
                "WHERE c.case_id = ?",
                (case_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_case_status(self, case_id: str, status: str) -> None:
        """Update case verdict status in the database."""
        with self.db.get_connection() as conn:
            conn.execute("UPDATE cases SET status = ? WHERE case_id = ?", (status, case_id))
            conn.commit()

    def get_evaluation(self, case_id: str) -> EvaluationResult | None:
        """Fetch internal neutral evaluation result for a case."""
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM evaluations WHERE case_id = ?", (case_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return EvaluationResult(
                case_id=row["case_id"],
                refusal_score=row["refusal_score"],
                bypass_score=row["bypass_score"],
                harm_score=row["harm_score"],
                confidence=row["confidence"],
                category=row["category"],
            )

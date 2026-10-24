"""Cryptographic capability tokens and nonce replay prevention."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

from pydantic import BaseModel, ConfigDict, Field

from bastion_arena.core.errors import AuthError, CapabilityDeniedError, ReplayDetectedError
from bastion_arena.core.schemas import AgentRole


class CapabilityToken(BaseModel):
    """Scoped, signed capability token payload."""

    model_config = ConfigDict(extra="forbid")

    jti: str = Field(..., max_length=128, description="Unique token nonce")
    tenant_id: str = Field(..., max_length=128)
    role: AgentRole
    capabilities: list[str] = Field(default_factory=list)
    issued_at: float
    expires_at: float


class TokenManager:
    """Issues and validates HMAC-signed capability tokens with replay prevention."""

    def __init__(self, secret_key: bytes | None = None) -> None:
        self.secret_key = secret_key or b"default-bastion-capability-secret-key-32bytes"
        self._consumed_jtis: set[str] = set()

    def issue_token(
        self,
        tenant_id: str,
        role: AgentRole,
        capabilities: list[str],
        ttl_seconds: float = 3600.0,
    ) -> str:
        now = time.time()
        seed = f"{tenant_id}:{role.value}:{now}:{time.perf_counter()}".encode()
        jti = hashlib.sha256(seed).hexdigest()[:32]
        token_data = {
            "jti": jti,
            "tenant_id": tenant_id,
            "role": role.value,
            "capabilities": capabilities,
            "issued_at": now,
            "expires_at": now + ttl_seconds,
        }
        payload_bytes = json.dumps(token_data, sort_keys=True).encode("utf-8")
        signature = hmac.new(self.secret_key, payload_bytes, hashlib.sha256).digest()

        token_str = (
            base64.urlsafe_b64encode(payload_bytes).decode("ascii")
            + "."
            + base64.urlsafe_b64encode(signature).decode("ascii")
        )
        return token_str

    def verify_token(self, token_str: str, mark_consumed: bool = False) -> CapabilityToken:
        parts = token_str.split(".")
        if len(parts) != 2:
            raise AuthError("Malformed capability token structure")

        try:
            payload_bytes = base64.urlsafe_b64decode(parts[0].encode("ascii"))
            signature = base64.urlsafe_b64decode(parts[1].encode("ascii"))
        except Exception as exc:
            raise AuthError("Invalid base64 encoding in token") from exc

        expected_sig = hmac.new(self.secret_key, payload_bytes, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected_sig):
            raise AuthError("Capability token signature verification failed")

        data = json.loads(payload_bytes.decode("utf-8"))
        token = CapabilityToken.model_validate(data)

        # Check expiration
        now = time.time()
        if now > token.expires_at:
            raise CapabilityDeniedError("Capability token has expired")

        # Nonce replay prevention
        if mark_consumed:
            if token.jti in self._consumed_jtis:
                raise ReplayDetectedError(f"Token nonce '{token.jti}' already consumed")
            self._consumed_jtis.add(token.jti)

        return token

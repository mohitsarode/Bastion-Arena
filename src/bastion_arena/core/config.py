"""Configuration loader with environment variable overrides and strict schema validation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(default="bastion-arena", min_length=1, max_length=64)
    environment: str = Field(default="demo", min_length=1, max_length=32)
    log_level: str = Field(default="INFO", min_length=3, max_length=10)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"log_level must be one of {valid}, got {v}")
        return upper


class ArenaConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_cases_per_round: int = Field(default=25, ge=1, le=1000)
    max_prompt_chars: int = Field(default=12000, ge=100, le=100000)
    max_model_output_tokens: int = Field(default=512, ge=16, le=4096)
    max_concurrent_cases_per_tenant: int = Field(default=2, ge=1, le=100)
    request_timeout_seconds: int = Field(default=45, ge=1, le=300)


class ProvidersConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["fake", "ollama", "openai_compatible_cloud"] = Field(
        default="fake",
        description="Active provider mode. Defaults to offline fake provider.",
    )


class ModelEndpointConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_url: str = Field(default="http://localhost:11434/v1", min_length=1)
    model: str = Field(default="qwen3:8b", min_length=1)
    timeout_seconds: int = Field(default=45, ge=1, le=300)


class FeedbackConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latency_bucket_ms: int = Field(default=250, ge=10, le=5000)
    minimum_response_latency_ms: int = Field(default=500, ge=0, le=10000)
    expose_evaluator_rationale_to_red: bool = Field(
        default=False,
        description="Invariant: Red must not receive evaluator private rationale.",
    )

    @field_validator("expose_evaluator_rationale_to_red")
    @classmethod
    def enforce_no_rationale_leak(cls, v: bool) -> bool:
        if v is True:
            raise ValueError(
                "expose_evaluator_rationale_to_red cannot be True under security model"
            )
        return False


class SecurityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    require_signed_ledger: bool = Field(default=True)
    allow_external_targets: bool = Field(
        default=False,
        description="Invariant: Only synthetic/local targets are permitted.",
    )
    require_tool_gateway: bool = Field(default=True)

    @field_validator("allow_external_targets")
    @classmethod
    def enforce_no_external_targets(cls, v: bool) -> bool:
        if v is True:
            raise ValueError(
                "allow_external_targets cannot be True in MVP; testing must be confined to local"
            )
        return False


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app: AppConfig = Field(default_factory=AppConfig)
    arena: ArenaConfig = Field(default_factory=ArenaConfig)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    models: dict[str, ModelEndpointConfig] = Field(default_factory=dict)
    feedback: FeedbackConfig = Field(default_factory=FeedbackConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)


def _find_config_file(explicit_path: str | Path | None = None) -> Path | None:
    if explicit_path:
        p = Path(explicit_path)
        if p.is_file():
            return p
        raise FileNotFoundError(f"Specified configuration file not found: {explicit_path}")

    env_path = os.getenv("BASTION_CONFIG")
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return p
        raise FileNotFoundError(f"BASTION_CONFIG file not found: {env_path}")

    cwd_config = Path("config.yaml")
    if cwd_config.is_file():
        return cwd_config

    current = Path(__file__).resolve().parent
    for parent in [current, current.parent, current.parent.parent, current.parent.parent.parent]:
        candidate = parent / "config.yaml"
        if candidate.is_file():
            return candidate

    return None


def load_config(config_path: str | Path | None = None) -> Settings:
    """Load, validate, and apply environment overrides to configuration."""
    cfg_file = _find_config_file(config_path)
    raw: dict = {}

    if cfg_file and cfg_file.is_file():
        with cfg_file.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

    if "BASTION_ENVIRONMENT" in os.environ:
        raw.setdefault("app", {})["environment"] = os.environ["BASTION_ENVIRONMENT"]
    if "BASTION_LOG_LEVEL" in os.environ:
        raw.setdefault("app", {})["log_level"] = os.environ["BASTION_LOG_LEVEL"]
    if "BASTION_PROVIDER_MODE" in os.environ:
        raw.setdefault("providers", {})["mode"] = os.environ["BASTION_PROVIDER_MODE"]
    if "BASTION_MAX_CASES_PER_ROUND" in os.environ:
        raw.setdefault("arena", {})["max_cases_per_round"] = int(
            os.environ["BASTION_MAX_CASES_PER_ROUND"]
        )
    if "BASTION_MAX_PROMPT_CHARS" in os.environ:
        raw.setdefault("arena", {})["max_prompt_chars"] = int(
            os.environ["BASTION_MAX_PROMPT_CHARS"]
        )
    if "BASTION_LATENCY_BUCKET_MS" in os.environ:
        raw.setdefault("feedback", {})["latency_bucket_ms"] = int(
            os.environ["BASTION_LATENCY_BUCKET_MS"]
        )

    return Settings.model_validate(raw)

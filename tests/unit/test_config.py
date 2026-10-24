"""Unit tests for configuration loading, bounds checking, and security constraints."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from bastion_arena.core.config import Settings, load_config


def test_load_default_config() -> None:
    settings = load_config()
    assert isinstance(settings, Settings)
    assert settings.app.name == "bastion-arena"
    assert settings.providers.mode in ("fake", "ollama", "openai_compatible_cloud")
    assert settings.arena.max_cases_per_round >= 1
    assert settings.arena.max_prompt_chars >= 100
    assert settings.security.allow_external_targets is False
    assert settings.feedback.expose_evaluator_rationale_to_red is False


def test_config_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASTION_ENVIRONMENT", "production-test")
    monkeypatch.setenv("BASTION_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("BASTION_PROVIDER_MODE", "fake")
    monkeypatch.setenv("BASTION_MAX_CASES_PER_ROUND", "50")
    monkeypatch.setenv("BASTION_MAX_PROMPT_CHARS", "8000")
    monkeypatch.setenv("BASTION_LATENCY_BUCKET_MS", "500")

    settings = load_config()
    assert settings.app.environment == "production-test"
    assert settings.app.log_level == "DEBUG"
    assert settings.providers.mode == "fake"
    assert settings.arena.max_cases_per_round == 50
    assert settings.arena.max_prompt_chars == 8000
    assert settings.feedback.latency_bucket_ms == 500


def test_invalid_log_level(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASTION_LOG_LEVEL", "INVALID_LEVEL")
    with pytest.raises(ValidationError):
        load_config()


def test_invalid_provider_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASTION_PROVIDER_MODE", "unsupported_cloud")
    with pytest.raises(ValidationError):
        load_config()


def test_security_invariant_no_rationale_leak() -> None:
    # Attempting to expose evaluator rationale to Red must fail validation
    with pytest.raises(ValidationError) as exc:
        Settings.model_validate({"feedback": {"expose_evaluator_rationale_to_red": True}})
    assert "expose_evaluator_rationale_to_red cannot be True" in str(exc.value)


def test_security_invariant_no_external_targets() -> None:
    # Attempting to allow external targets in MVP must fail validation
    with pytest.raises(ValidationError) as exc:
        Settings.model_validate({"security": {"allow_external_targets": True}})
    assert "allow_external_targets cannot be True" in str(exc.value)


def test_bounds_checking() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate(
            {
                "arena": {"max_cases_per_round": 0}  # ge=1
            }
        )

    with pytest.raises(ValidationError):
        Settings.model_validate(
            {
                "arena": {"max_prompt_chars": 50}  # ge=100
            }
        )

    with pytest.raises(ValidationError):
        Settings.model_validate(
            {
                "feedback": {"latency_bucket_ms": 5}  # ge=10
            }
        )

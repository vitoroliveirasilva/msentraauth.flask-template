from __future__ import annotations

import logging

import pytest
from flask import Flask
from flask_ms_entra_auth import Identity, MicrosoftEntraAuth

from conftest import RedisDouble
from msentraauth_template.auth.hooks import LocalUserRegistry, register_auth_hooks
from msentraauth_template.session_backend import RedisSessionInterface


def identity(name: str = "User") -> Identity:
    return Identity.from_claims(
        {
            "oid": "object-id",
            "tid": "tenant-id",
            "name": name,
            "preferred_username": "user@example.test",
        },
        home_account_id="home-id",
        expected_tenant_id="tenant-id",
    )


def test_registry_binds_updates_and_reads() -> None:
    registry = LocalUserRegistry()
    assert registry.count() == 0
    assert registry.get("tenant-id", "object-id") is None
    first = registry.bind(identity())
    assert first.stable_id == ("tenant-id", "object-id")
    assert registry.count() == 1
    second = registry.bind(identity("Updated"))
    assert registry.count() == 1
    assert second.display_name == "Updated"
    assert registry.get("tenant-id", "object-id") == second


def test_registers_auth_and_logout_hooks(caplog: pytest.LogCaptureFixture) -> None:
    extension = MicrosoftEntraAuth()
    registry = LocalUserRegistry()
    logger = logging.getLogger("template-hook-test")
    redis = RedisDouble()
    app = Flask("hook-test")
    app.secret_key = "s" * 32
    app.config["SESSION_PERMANENT"] = True
    app.session_interface = RedisSessionInterface(redis)
    register_auth_hooks(extension, registry, logger)
    with app.test_request_context("/"):
        extension._hooks.emit_authenticated(identity())
    assert registry.count() == 1
    with caplog.at_level(logging.INFO, logger="template-hook-test"):
        extension._hooks.emit_logout(identity())
        extension._hooks.emit_logout(None)
    assert "local authentication state cleared" in caplog.text


def test_authenticated_hook_rejects_incompatible_session_interface() -> None:
    from flask_ms_entra_auth import LocalBindingError

    extension = MicrosoftEntraAuth()
    registry = LocalUserRegistry()
    app = Flask("invalid-hook-session")
    app.secret_key = "s" * 32
    register_auth_hooks(extension, registry, logging.getLogger("invalid-hook-session"))
    with app.test_request_context("/"), pytest.raises(LocalBindingError):
        extension._hooks.emit_authenticated(identity())

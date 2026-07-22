from __future__ import annotations

import logging

import pytest
from flask import Flask
from flask_ms_entra_auth import Identity, MicrosoftEntraAuth

from conftest import RedisDouble
from msentraauth_template.auth.hooks import LocalUserRegistry, register_auth_hooks
from msentraauth_template.session_backend import RedisSessionInterface


def identity(name: str = "User", *, object_id: str = "object-id") -> Identity:
    return Identity.from_claims(
        {
            "oid": object_id,
            "tid": "tenant-id",
            "name": name,
            "preferred_username": f"{object_id}@example.test",
        },
        home_account_id=f"home-{object_id}",
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


def test_registry_is_bounded_and_keeps_recently_authenticated_users() -> None:
    registry = LocalUserRegistry(max_users=2)
    registry.bind(identity(object_id="first"))
    registry.bind(identity(object_id="second"))
    registry.bind(identity("Refreshed", object_id="first"))
    registry.bind(identity(object_id="third"))

    assert registry.count() == 2
    assert registry.get("tenant-id", "first") is not None
    assert registry.get("tenant-id", "second") is None
    assert registry.get("tenant-id", "third") is not None


@pytest.mark.parametrize("max_users", [0, -1, True, 1.5])
def test_registry_rejects_invalid_capacity(max_users: object) -> None:
    with pytest.raises(ValueError, match="max_users"):
        LocalUserRegistry(max_users=max_users)  # type: ignore[arg-type]


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


def test_failed_session_rotation_does_not_bind_local_user() -> None:
    from flask_ms_entra_auth import LocalBindingError

    extension = MicrosoftEntraAuth()
    registry = LocalUserRegistry()
    redis = RedisDouble()
    redis.fail = "delete"
    app = Flask("failed-hook-rotation")
    app.secret_key = "s" * 32
    app.config["SESSION_PERMANENT"] = True
    app.session_interface = RedisSessionInterface(redis)
    register_auth_hooks(extension, registry, logging.getLogger("failed-hook-rotation"))

    with app.test_request_context("/"), pytest.raises(LocalBindingError):
        extension._hooks.emit_authenticated(identity())

    assert registry.count() == 0


def test_authenticated_hook_rejects_incompatible_session_interface() -> None:
    from flask_ms_entra_auth import LocalBindingError

    extension = MicrosoftEntraAuth()
    registry = LocalUserRegistry()
    app = Flask("invalid-hook-session")
    app.secret_key = "s" * 32
    register_auth_hooks(extension, registry, logging.getLogger("invalid-hook-session"))
    with app.test_request_context("/"), pytest.raises(LocalBindingError):
        extension._hooks.emit_authenticated(identity())

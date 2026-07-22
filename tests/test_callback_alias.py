from __future__ import annotations

import pytest
from flask import Flask, request

from msentraauth_template.callback_alias import CallbackAliasError, register_callback_alias


def _callback() -> str:
    return request.args.get("code", "missing")


def _app_with_extension_callback() -> Flask:
    app = Flask(__name__)
    app.add_url_rule(
        "/auth/callback",
        endpoint="ms_entra_auth.callback",
        view_func=_callback,
        methods=["GET"],
    )
    return app


def test_keeps_the_builtin_callback_without_registering_an_alias() -> None:
    app = _app_with_extension_callback()

    register_callback_alias(app, "http://localhost:5000/auth/callback")

    assert "msentraauth_template.callback_alias" not in app.view_functions


def test_registers_legacy_callback_with_the_same_view_and_query() -> None:
    app = _app_with_extension_callback()

    register_callback_alias(app, "http://localhost:5000/getAToken")

    assert (
        app.view_functions["msentraauth_template.callback_alias"]
        is app.view_functions["ms_entra_auth.callback"]
    )
    response = app.test_client().get("/getAToken", query_string={"code": "authorization-code"})
    assert response.status_code == 200
    assert response.text == "authorization-code"


@pytest.mark.parametrize(
    "redirect_uri",
    ["http://localhost:5000", "http://localhost:5000/"],
)
def test_rejects_missing_or_root_callback_paths(redirect_uri: str) -> None:
    app = _app_with_extension_callback()

    with pytest.raises(CallbackAliasError, match="non-root"):
        register_callback_alias(app, redirect_uri)


@pytest.mark.parametrize(
    "redirect_uri",
    [
        "callback",
        "http://localhost:5000//callback",
        "http://localhost:5000/<path:callback>",
        r"http://localhost:5000/callback\legacy",
        "http://localhost:5000/" + ("a" * 2048),
    ],
)
def test_rejects_dynamic_or_unsafe_callback_paths(redirect_uri: str) -> None:
    app = _app_with_extension_callback()

    with pytest.raises(CallbackAliasError, match="static safe"):
        register_callback_alias(app, redirect_uri)


def test_rejects_alias_when_extension_callback_is_missing() -> None:
    app = Flask(__name__)

    with pytest.raises(CallbackAliasError, match="not registered"):
        register_callback_alias(app, "http://localhost:5000/getAToken")


def test_rejects_callback_path_collision() -> None:
    app = _app_with_extension_callback()
    app.add_url_rule("/getAToken", endpoint="occupied", view_func=lambda: "occupied")

    with pytest.raises(CallbackAliasError, match="already registered"):
        register_callback_alias(app, "http://localhost:5000/getAToken")

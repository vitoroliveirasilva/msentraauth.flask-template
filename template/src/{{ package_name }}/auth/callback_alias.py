from __future__ import annotations

import re
from urllib.parse import unquote, urlsplit

from flask import Flask

_DEFAULT_CALLBACK_PATH = "/auth/callback"
_CALLBACK_ENDPOINT = "ms_entra_auth.callback"
_ALIAS_ENDPOINT = "app.callback_alias"
_SAFE_CALLBACK_PATH = re.compile(r"^/[A-Za-z0-9._~!$&'()*+,;=:@/-]+$")


class CallbackAliasError(RuntimeError):
    pass


def register_callback_alias(app: Flask, redirect_uri: str) -> None:
    callback_path = unquote(urlsplit(redirect_uri).path)
    if callback_path == _DEFAULT_CALLBACK_PATH:
        return
    if (
        not _SAFE_CALLBACK_PATH.fullmatch(callback_path)
        or callback_path in {"", "/"}
        or callback_path.startswith("//")
        or callback_path.endswith("/")
        or len(callback_path) > 256
        or "//" in callback_path
        or any(part in {".", ".."} for part in callback_path.split("/"))
    ):
        raise CallbackAliasError("MS_ENTRA_REDIRECT_URI must contain a static safe callback path")
    callback_view = app.view_functions.get(_CALLBACK_ENDPOINT)
    if callback_view is None:
        raise CallbackAliasError("Microsoft Entra callback endpoint is not registered")
    if any(
        rule.rule == callback_path and "GET" in (rule.methods or ())
        for rule in app.url_map.iter_rules()
    ):
        raise CallbackAliasError(f"callback path {callback_path!r} is already registered")
    app.add_url_rule(
        callback_path, endpoint=_ALIAS_ENDPOINT, view_func=callback_view, methods=["GET"]
    )


__all__ = ["CallbackAliasError", "register_callback_alias"]

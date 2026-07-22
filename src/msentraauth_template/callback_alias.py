from __future__ import annotations

from urllib.parse import urlsplit

from flask import Flask

_DEFAULT_CALLBACK_PATH = "/auth/callback"
_CALLBACK_ENDPOINT = "ms_entra_auth.callback"
_ALIAS_ENDPOINT = "msentraauth_template.callback_alias"
_MAX_CALLBACK_PATH_LENGTH = 2048


class CallbackAliasError(RuntimeError):
    """Gerado quando o alias de callback não pode ser registrado com segurança"""


def register_callback_alias(app: Flask, redirect_uri: str) -> None:
    # Vincula um callback legado de mesma origem à view segura da extensão

    callback_path = urlsplit(redirect_uri).path
    if callback_path == _DEFAULT_CALLBACK_PATH:
        return
    if not callback_path or callback_path == "/":
        raise CallbackAliasError("MS_ENTRA_REDIRECT_URI must contain a non-root callback path")
    if (
        not callback_path.startswith("/")
        or callback_path.startswith("//")
        or len(callback_path) > _MAX_CALLBACK_PATH_LENGTH
        or any(character in callback_path for character in ("<", ">", "\\", "\x00"))
    ):
        raise CallbackAliasError("MS_ENTRA_REDIRECT_URI must contain a static safe callback path")

    callback_view = app.view_functions.get(_CALLBACK_ENDPOINT)
    if callback_view is None:
        raise CallbackAliasError("the Microsoft Entra callback endpoint is not registered")

    collision = any(
        rule.rule == callback_path and "GET" in (rule.methods or ())
        for rule in app.url_map.iter_rules()
    )
    if collision:
        raise CallbackAliasError(f"the callback path {callback_path!r} is already registered")

    app.add_url_rule(
        callback_path,
        endpoint=_ALIAS_ENDPOINT,
        view_func=callback_view,
        methods=["GET"],
    )


__all__ = ["CallbackAliasError", "register_callback_alias"]

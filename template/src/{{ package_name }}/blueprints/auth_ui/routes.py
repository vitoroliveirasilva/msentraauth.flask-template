from flask import Blueprint, redirect, render_template, url_for
from flask.typing import ResponseReturnValue

from ...auth.context import get_auth_context


def create_auth_ui_blueprint() -> Blueprint:
    blueprint = Blueprint("auth_ui", __name__)

    @blueprint.get("/login")
    def login() -> ResponseReturnValue:
        if get_auth_context().authenticated:
            return redirect(url_for("main.home"), code=303)
        return render_template("auth/login.html")

    return blueprint


__all__ = ["create_auth_ui_blueprint"]

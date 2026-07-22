from __future__ import annotations

from flask import Blueprint, current_app, jsonify, render_template
from flask.typing import ResponseReturnValue
from flask_ms_entra_auth import AuthenticationRequired, current_identity

from ..storage import RedisClient


def create_web_blueprint() -> Blueprint:
    blueprint = Blueprint("web", __name__)

    @blueprint.get("/")
    def home() -> str:
        try:
            identity = current_identity._get_current_object()
        except AuthenticationRequired:
            identity = None
        return render_template("home.html", identity=identity)

    @blueprint.get("/logged-out")
    def logged_out() -> str:
        return render_template("logged_out.html")

    @blueprint.get("/health/live")
    def live() -> ResponseReturnValue:
        return jsonify(status="ok"), 200

    @blueprint.get("/health/ready")
    def ready() -> ResponseReturnValue:
        client = current_app.extensions["template_redis"]
        if not isinstance(client, RedisClient):
            return jsonify(status="unavailable"), 503
        try:
            available = bool(client.ping())
        except Exception as exc:
            current_app.logger.warning(
                "redis readiness check failed",
                extra={"error_type": type(exc).__name__},
            )
            return jsonify(status="unavailable"), 503
        if not available:
            current_app.logger.warning("redis readiness check returned an unavailable result")
            return jsonify(status="unavailable"), 503
        return jsonify(status="ready"), 200

    return blueprint


__all__ = ["create_web_blueprint"]

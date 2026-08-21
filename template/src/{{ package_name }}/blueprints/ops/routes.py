from __future__ import annotations

from contextlib import suppress
from secrets import token_bytes, token_hex

from flask import Blueprint, current_app, jsonify
from flask.typing import ResponseReturnValue

from ...infrastructure.storage import RedisClient
from ...runtime import extension_key
from ...settings import AppSettings


def create_ops_blueprint() -> Blueprint:
    blueprint = Blueprint("ops", __name__)

    @blueprint.get("/health/live")
    def live() -> ResponseReturnValue:
        return jsonify(status="ok"), 200

    @blueprint.get("/health/ready")
    def ready() -> ResponseReturnValue:
        client = current_app.extensions.get(extension_key(current_app, "redis"))
        settings = current_app.extensions.get(extension_key(current_app, "settings"))
        if not isinstance(client, RedisClient) or not isinstance(settings, AppSettings):
            return jsonify(status="unavailable"), 503
        key = f"{settings.session_namespace}:readiness:{token_hex(16)}"
        value = token_bytes(16)
        created = False
        try:
            if not bool(client.ping()):
                return jsonify(status="unavailable"), 503
            if not client.set(key, value, ex=5, nx=True):
                return jsonify(status="unavailable"), 503
            created = True
            if client.get(key) != value:
                return jsonify(status="unavailable"), 503
        except Exception as exc:
            current_app.logger.warning(
                "redis readiness check failed",
                extra={"error_type": type(exc).__name__},
            )
            return jsonify(status="unavailable"), 503
        finally:
            if created:
                with suppress(Exception):
                    client.delete(key)
        return jsonify(status="ready"), 200

    return blueprint


__all__ = ["create_ops_blueprint"]

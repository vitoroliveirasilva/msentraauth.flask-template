from flask import Flask


def register_application(app: Flask) -> None:
    """Register business blueprints/services here without editing auth/session internals."""
    del app


__all__ = ["register_application"]

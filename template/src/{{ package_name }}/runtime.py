from flask import Flask


def extension_key(app: Flask, name: str) -> str:
    return f"{app.import_name}.{name}"


__all__ = ["extension_key"]

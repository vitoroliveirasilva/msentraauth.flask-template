from __future__ import annotations

from flask import Flask, Response, request

from ..settings import AppSettings

_DEFAULT_CSP: dict[str, tuple[str, ...]] = {
    "default-src": ("'self'",),
    "base-uri": ("'self'",),
    "connect-src": ("'self'",),
    "form-action": ("'self'",),
    "frame-ancestors": ("'none'",),
    "img-src": ("'self'", "data:"),
    "object-src": ("'none'",),
    "script-src": ("'self'",),
    "style-src": ("'self'",),
}


def build_csp(settings: AppSettings) -> str:
    directives = dict(_DEFAULT_CSP)
    directives["script-src"] += settings.csp_script_src_extra
    directives["style-src"] += settings.csp_style_src_extra
    directives["connect-src"] += settings.csp_connect_src_extra
    directives["img-src"] += settings.csp_img_src_extra
    return "; ".join(f"{name} {' '.join(values)}" for name, values in directives.items())


def configure_security(app: Flask, settings: AppSettings) -> None:
    csp = build_csp(settings)
    permissions = ", ".join(f"{feature}=()" for feature in settings.permissions_policy_features)

    @app.after_request
    def apply_headers(response: Response) -> Response:
        response.headers["Content-Security-Policy"] = csp
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        if permissions:
            response.headers["Permissions-Policy"] = permissions
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-store, max-age=0"
            response.headers["Pragma"] = "no-cache"
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


__all__ = ["build_csp", "configure_security"]

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, cast

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .auth.hooks import LocalUserRegistry, register_auth_hooks
from .callback_alias import register_callback_alias
from .extensions import csrf, entra_auth
from .graph.client import GraphClient, HttpTransport
from .graph.routes import create_graph_blueprint
from .observability import configure_observability
from .security import configure_security
from .session_backend import RedisSessionInterface, register_session_backend_guard
from .settings import AppSettings
from .storage import RedisAuthStorage, RedisClient
from .web.errors import register_error_handlers
from .web.routes import create_web_blueprint

if TYPE_CHECKING:
    from flask_ms_entra_auth.auth.protocols import MsalClientFactory


def create_app(
    settings: AppSettings | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    redis_client: RedisClient | None = None,
    msal_client_factory: MsalClientFactory | None = None,
    graph_transport: HttpTransport | None = None,
) -> Flask:
    # Cria uma aplicação totalmente configurada sem estado de usuário global

    resolved = settings or AppSettings.from_env(environ)
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(resolved.flask_config())
    configure_observability(app, resolved)

    client = cast(
        RedisClient,
        redis_client if redis_client is not None else resolved.create_redis_client(),
    )
    app.extensions["template_settings"] = resolved
    app.extensions["template_redis"] = client

    if resolved.proxy_hops.any_enabled:
        app.wsgi_app = ProxyFix(  # type: ignore[method-assign]
            app.wsgi_app,
            x_for=resolved.proxy_hops.x_for,
            x_proto=resolved.proxy_hops.x_proto,
            x_host=resolved.proxy_hops.x_host,
            x_port=resolved.proxy_hops.x_port,
            x_prefix=resolved.proxy_hops.x_prefix,
        )

    session_codec = resolved.create_session_codec()
    app.extensions["template_session_codec"] = session_codec
    app.session_interface = RedisSessionInterface(
        client,
        codec=session_codec,
        key_prefix=resolved.session_key_prefix,
        revocation_prefix=resolved.revocation_key_prefix,
    )
    register_session_backend_guard(app)
    csrf.init_app(app)

    storage = RedisAuthStorage(client, key_prefix=resolved.auth_storage_key_prefix)
    extension = entra_auth.with_runtime(
        storage=storage,
        msal_client_factory=msal_client_factory,
    )
    extension.init_app(app)
    app.extensions["template_entra_auth"] = extension

    users = LocalUserRegistry()
    app.extensions["template_users"] = users
    register_auth_hooks(extension, users, app.logger)

    graph = GraphClient.from_settings(resolved, transport=graph_transport)
    app.extensions["template_graph"] = graph

    app.register_blueprint(create_web_blueprint())
    app.register_blueprint(create_graph_blueprint(extension, graph))
    register_callback_alias(app, resolved.redirect_uri)
    register_error_handlers(app)
    configure_security(app, resolved)

    report = extension.audit_security(app)
    app.extensions["template_security_report"] = report
    return app


__all__ = ["AppSettings", "create_app"]

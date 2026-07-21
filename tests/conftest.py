from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from fnmatch import fnmatch
from time import monotonic
from typing import Any, cast

import pytest
from flask_ms_entra_auth.auth.protocols import MsalAccount, MsalResult
from msal import SerializableTokenCache  # type: ignore[import-untyped]

from msentraauth_template.settings import AppSettings, ProxyHops


class RedisDouble:
    def __init__(self) -> None:
        self._values: dict[str, bytes] = {}
        self._expires_at: dict[str, float] = {}
        self.fail: str | None = None
        self.return_invalid = False
        self.return_false = False
        self.forced_get: object | None = None

    def _purge_if_expired(self, name: str) -> None:
        expires_at = self._expires_at.get(name)
        if expires_at is not None and expires_at <= monotonic():
            self._values.pop(name, None)
            self._expires_at.pop(name, None)

    def get(self, name: str) -> bytes | None:
        if self.fail == "get":
            raise RuntimeError("redis-secret")
        if self.return_invalid:
            return "invalid"  # type: ignore[return-value]
        if self.forced_get is not None:
            return cast(bytes | None, self.forced_get)
        self._purge_if_expired(name)
        return self._values.get(name)

    def set(self, name: str, value: bytes, ex: int | None = None) -> object:
        if self.fail == "set":
            raise RuntimeError("redis-secret")
        if self.return_false:
            return False
        self._values[name] = bytes(value)
        if ex is None:
            self._expires_at.pop(name, None)
        else:
            self._expires_at[name] = monotonic() + ex
        return True

    def setex(self, name: str, time: int, value: bytes) -> object:
        return self.set(name, value, ex=time)

    def delete(self, *names: str) -> int:
        if self.fail == "delete":
            raise RuntimeError("redis-secret")
        removed = 0
        for name in names:
            self._purge_if_expired(name)
            if name in self._values:
                removed += 1
                self._values.pop(name, None)
            self._expires_at.pop(name, None)
        return removed

    def eval(self, script: str, numkeys: int, *keys_and_args: str) -> object:
        del script, numkeys
        if self.fail == "eval":
            raise RuntimeError("redis-secret")
        key = keys_and_args[0]
        value = self.get(key)
        if value is not None:
            self.delete(key)
        return value

    def ping(self) -> object:
        if self.fail == "ping":
            raise RuntimeError("redis-secret")
        return True

    def expire(self, name: str, time: int) -> bool:
        self._purge_if_expired(name)
        if name not in self._values:
            return False
        self._expires_at[name] = monotonic() + time
        return True

    def ttl(self, name: str) -> int:
        self._purge_if_expired(name)
        if name not in self._values:
            return -2
        expires_at = self._expires_at.get(name)
        if expires_at is None:
            return -1
        return max(0, int(expires_at - monotonic()))

    def scan_iter(self, match: str | None = None) -> Iterator[bytes]:
        for name in tuple(self._values):
            self._purge_if_expired(name)
        for name in self._values:
            if match is None or fnmatch(name, match):
                yield name.encode()


class FakeMsalClient:
    def __init__(self) -> None:
        self.cache: SerializableTokenCache | None = None
        self.accounts: Sequence[MsalAccount] = [
            {
                "home_account_id": "home-id",
                "local_account_id": "object-id",
                "realm": "tenant-id",
            }
        ]

    def initiate_auth_code_flow(
        self,
        scopes: list[str],
        *,
        redirect_uri: str,
        state: str,
    ) -> MsalResult:
        assert scopes == ["User.Read"]
        assert redirect_uri.endswith("/auth/callback")
        return {
            "auth_uri": f"https://login.microsoftonline.com/tenant-id/oauth2/v2.0/authorize?state={state}",
            "state": state,
            "nonce": "nonce",
        }

    def acquire_token_by_auth_code_flow(
        self,
        auth_code_flow: Mapping[str, object],
        auth_response: Mapping[str, str],
    ) -> MsalResult:
        assert auth_code_flow["state"] == auth_response["state"]
        if self.cache is not None:
            self.cache.has_state_changed = True
        return {
            "id_token_claims": {
                "oid": "object-id",
                "tid": "tenant-id",
                "name": "Template User",
                "preferred_username": "template@example.test",
            }
        }

    def get_accounts(self, username: str | None = None) -> Sequence[MsalAccount]:
        assert username is None
        return self.accounts

    def acquire_token_silent_with_error(
        self,
        scopes: list[str],
        account: MsalAccount,
        *,
        force_refresh: bool = False,
    ) -> MsalResult | None:
        del scopes, account, force_refresh
        return {"access_token": "server-only-token"}


class GraphResponse:
    def __init__(self, status_code: int, payload: object) -> None:
        self.status_code = status_code
        self.payload = payload

    def json(self) -> object:
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class GraphTransportDouble:
    def __init__(self) -> None:
        self.response = GraphResponse(
            200,
            {
                "id": "graph-id",
                "displayName": "Template User",
                "userPrincipalName": "template@example.test",
                "mail": None,
            },
        )
        self.error: Exception | None = None
        self.calls: list[
            tuple[str, Mapping[str, str], Mapping[str, str], tuple[float, float]]
        ] = []

    def get(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        params: Mapping[str, str],
        timeout: tuple[float, float],
    ) -> GraphResponse:
        self.calls.append((url, headers, params, timeout))
        if self.error is not None:
            raise self.error
        return self.response


@pytest.fixture
def settings() -> AppSettings:
    return AppSettings(
        environment="testing",
        secret_key="s" * 32,
        base_url="http://localhost:5000",
        trusted_hosts=("localhost",),
        log_level="INFO",
        log_format="text",
        client_id="client-id",
        client_secret="c" * 32,
        tenant_id="tenant-id",
        redirect_uri="http://localhost:5000/auth/callback",
        scopes=("User.Read",),
        redis_url="redis://localhost:6379/0",
        redis_socket_connect_timeout=1.0,
        redis_socket_timeout=1.0,
        redis_health_check_interval=30,
        redis_tls_required=False,
        session_lifetime_seconds=3600,
        session_refresh_each_request=True,
        cookie_secure=False,
        cookie_samesite="Lax",
        graph_base_url="https://graph.microsoft.com/v1.0",
        graph_connect_timeout=1.0,
        graph_read_timeout=2.0,
        proxy_hops=ProxyHops(),
        testing=True,
        csrf_enabled=False,
    )


@pytest.fixture
def redis_double() -> RedisDouble:
    return RedisDouble()


@pytest.fixture
def msal_runtime() -> tuple[FakeMsalClient, Any]:
    client = FakeMsalClient()

    def factory(config: object, cache: SerializableTokenCache) -> FakeMsalClient:
        del config
        client.cache = cache
        return client

    return client, factory

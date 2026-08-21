from __future__ import annotations

import re
from typing import Protocol, runtime_checkable

from flask_ms_entra_auth import StorageError

_SAFE_STORAGE_KEY = re.compile(r"^[A-Za-z0-9_.:-]{1,256}$")
_TAKE_SCRIPT = """
local value = redis.call('GET', KEYS[1])
if value then
  redis.call('DEL', KEYS[1])
end
return value
""".strip()


@runtime_checkable
class RedisClient(Protocol):
    def get(self, name: str) -> bytes | None: ...

    def set(
        self,
        name: str,
        value: bytes,
        ex: int | None = None,
        *,
        nx: bool = False,
        xx: bool = False,
    ) -> object: ...

    def delete(self, *names: str) -> int: ...

    def eval(self, script: str, numkeys: int, *keys_and_args: object) -> object: ...

    def ping(self) -> object: ...


class RedisAuthStorage:
    """Namespaced, atomic Redis storage used by the authentication extension."""

    __slots__ = ("_client", "_key_prefix")

    def __init__(self, client: RedisClient, *, key_prefix: str) -> None:
        if not isinstance(client, RedisClient):
            raise TypeError("client must provide the Redis operations used by the adapter")
        if (
            not isinstance(key_prefix, str)
            or not key_prefix.endswith(":")
            or len(key_prefix) > 128
            or not _SAFE_STORAGE_KEY.fullmatch(key_prefix[:-1])
        ):
            raise ValueError("key_prefix must be safe, non-empty, and end with ':'")
        self._client = client
        self._key_prefix = key_prefix

    @property
    def client(self) -> RedisClient:
        return self._client

    @property
    def key_prefix(self) -> str:
        return self._key_prefix

    def load(self, key: str) -> bytes | None:
        redis_key = self._key(key)
        try:
            value = self._client.get(redis_key)
        except Exception as exc:
            raise StorageError("redis storage load failed") from exc
        return _bytes_or_none(value)

    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None:
        if not isinstance(value, bytes):
            raise TypeError("value must be bytes")
        if ttl is not None and (isinstance(ttl, bool) or not isinstance(ttl, int) or ttl <= 0):
            raise ValueError("ttl must be a positive integer or None")
        redis_key = self._key(key)
        try:
            result = self._client.set(redis_key, value, ex=ttl)
        except Exception as exc:
            raise StorageError("redis storage save failed") from exc
        if not result:
            raise StorageError("redis storage save failed")

    def delete(self, key: str) -> None:
        redis_key = self._key(key)
        try:
            self._client.delete(redis_key)
        except Exception as exc:
            raise StorageError("redis storage delete failed") from exc

    def take(self, key: str) -> bytes | None:
        redis_key = self._key(key)
        try:
            value = self._client.eval(_TAKE_SCRIPT, 1, redis_key)
        except Exception as exc:
            raise StorageError("redis storage atomic consume failed") from exc
        return _bytes_or_none(value)

    def _key(self, key: str) -> str:
        if not isinstance(key, str) or not _SAFE_STORAGE_KEY.fullmatch(key):
            raise StorageError("redis storage key is invalid")
        return f"{self._key_prefix}{key}"


def _bytes_or_none(value: object) -> bytes | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    raise StorageError("redis storage returned an invalid value")


__all__ = ["RedisAuthStorage", "RedisClient"]

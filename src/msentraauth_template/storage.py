from __future__ import annotations

from typing import Protocol, runtime_checkable

from flask_ms_entra_auth import StorageError


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
    def eval(self, script: str, numkeys: int, *keys_and_args: str) -> object: ...
    def ping(self) -> object: ...


_TAKE_SCRIPT = """
local value = redis.call('GET', KEYS[1])
if value then
  redis.call('DEL', KEYS[1])
end
return value
""".strip()


class RedisAuthStorage:
    # Implementação de armazenamento distribuído com TTL e consumo atômico de uso único

    __slots__ = ("_client",)

    def __init__(self, client: RedisClient) -> None:
        if not isinstance(client, RedisClient):
            raise TypeError("client must provide the Redis operations used by the adapter")
        self._client = client

    @property
    def client(self) -> RedisClient:
        return self._client

    def load(self, key: str) -> bytes | None:
        try:
            value = self._client.get(key)
        except Exception as exc:
            raise StorageError("redis storage load failed") from exc
        return _bytes_or_none(value)

    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None:
        if not isinstance(value, bytes):
            raise TypeError("value must be bytes")
        if ttl is not None and (isinstance(ttl, bool) or not isinstance(ttl, int) or ttl <= 0):
            raise ValueError("ttl must be a positive integer or None")
        try:
            result = self._client.set(key, value, ex=ttl)
        except Exception as exc:
            raise StorageError("redis storage save failed") from exc
        if not result:
            raise StorageError("redis storage save failed")

    def delete(self, key: str) -> None:
        try:
            self._client.delete(key)
        except Exception as exc:
            raise StorageError("redis storage delete failed") from exc

    def take(self, key: str) -> bytes | None:
        try:
            value = self._client.eval(_TAKE_SCRIPT, 1, key)
        except Exception as exc:
            raise StorageError("redis storage atomic consume failed") from exc
        return _bytes_or_none(value)


def _bytes_or_none(value: object) -> bytes | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    raise StorageError("redis storage returned an invalid value")


__all__ = ["RedisAuthStorage", "RedisClient"]

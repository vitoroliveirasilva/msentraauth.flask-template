from __future__ import annotations

import pytest
from flask_ms_entra_auth import AtomicAuthStorage, AuthStorage, StorageError

from conftest import RedisDouble
from msentraauth_template.storage import RedisAuthStorage


def test_contract_and_atomic_take(redis_double: RedisDouble) -> None:
    storage = RedisAuthStorage(redis_double)
    assert isinstance(storage, AuthStorage)
    assert isinstance(storage, AtomicAuthStorage)
    assert storage.client is redis_double
    storage.save("key", b"value", ttl=30)
    assert storage.load("key") == b"value"
    assert storage.take("key") == b"value"
    assert storage.take("key") is None
    storage.delete("missing")


def test_save_without_ttl_and_bytearray_response(redis_double: RedisDouble) -> None:
    storage = RedisAuthStorage(redis_double)
    storage.save("key", b"value")
    assert storage.load("key") == b"value"
    redis_double.forced_get = bytearray(b"value")
    assert storage.load("array") == b"value"


@pytest.mark.parametrize("value", ["text", bytearray(b"x")])
def test_rejects_non_bytes_values(redis_double: RedisDouble, value: object) -> None:
    with pytest.raises(TypeError, match="bytes"):
        RedisAuthStorage(redis_double).save("key", value)  # type: ignore[arg-type]


@pytest.mark.parametrize("ttl", [0, -1, True, 1.5])
def test_rejects_invalid_ttl(redis_double: RedisDouble, ttl: object) -> None:
    with pytest.raises(ValueError, match="ttl"):
        RedisAuthStorage(redis_double).save("key", b"value", ttl=ttl)  # type: ignore[arg-type]


def test_rejects_invalid_client() -> None:
    with pytest.raises(TypeError, match="Redis"):
        RedisAuthStorage(object())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("operation", "call"),
    [
        ("get", lambda storage: storage.load("key")),
        ("set", lambda storage: storage.save("key", b"value")),
        ("delete", lambda storage: storage.delete("key")),
        ("eval", lambda storage: storage.take("key")),
    ],
)
def test_wraps_backend_errors(
    redis_double: RedisDouble,
    operation: str,
    call: object,
) -> None:
    redis_double.fail = operation
    storage = RedisAuthStorage(redis_double)
    with pytest.raises(StorageError) as raised:
        call(storage)  # type: ignore[operator]
    assert "redis-secret" not in str(raised.value)


def test_rejects_false_save_and_invalid_return(redis_double: RedisDouble) -> None:
    storage = RedisAuthStorage(redis_double)
    redis_double.return_false = True
    with pytest.raises(StorageError, match="save"):
        storage.save("key", b"value")
    redis_double.return_false = False
    redis_double.return_invalid = True
    with pytest.raises(StorageError, match="invalid"):
        storage.load("key")

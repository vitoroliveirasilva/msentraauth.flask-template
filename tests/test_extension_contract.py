from flask_ms_entra_auth import (
    AtomicAuthStorage,
    MicrosoftEntraAuth,
    SecurityReport,
    __version__,
)

from msentraauth_template.storage import RedisAuthStorage, RedisClient


def test_template_consumes_stable_extension_contract(redis_double: RedisClient) -> None:
    assert __version__ == "1.0.0"
    assert isinstance(MicrosoftEntraAuth(), MicrosoftEntraAuth)
    assert isinstance(RedisAuthStorage(redis_double), AtomicAuthStorage)
    assert SecurityReport.__name__ == "SecurityReport"

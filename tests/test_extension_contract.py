from flask_ms_entra_auth import (
    AtomicAuthStorage,
    MicrosoftEntraAuth,
    SecurityReport,
    __version__,
)
from packaging.version import Version

from msentraauth_template.storage import RedisAuthStorage, RedisClient


def test_template_consumes_stable_extension_contract(redis_double: RedisClient) -> None:
    version = Version(__version__)
    assert version.major == 1
    assert isinstance(MicrosoftEntraAuth(), MicrosoftEntraAuth)
    assert isinstance(RedisAuthStorage(redis_double), AtomicAuthStorage)
    assert SecurityReport.__name__ == "SecurityReport"

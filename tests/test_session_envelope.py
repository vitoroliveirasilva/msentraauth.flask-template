from __future__ import annotations

import base64
import json
from dataclasses import replace
from typing import Any

import pytest

import msentraauth_template.session_envelope as envelope_module
from msentraauth_template.session_envelope import (
    SessionEnvelopeCodec,
    SessionEnvelopeError,
    SessionEnvelopeExpired,
    SessionMetadata,
    subject_fingerprint,
)


def key(seed: int) -> str:
    return base64.urlsafe_b64encode(bytes((seed + i) % 256 for i in range(32))).decode().rstrip("=")


def codec(
    *keys: str,
    strict_schema: bool = True,
    allowed_keys: tuple[str, ...] = ("cart", "counter", "profile"),
    idle: int = 60,
    absolute: int = 300,
    renewal: int = 120,
    skew: int = 5,
    max_plaintext: int = 64 * 1024,
    max_envelope: int = 96 * 1024,
) -> SessionEnvelopeCodec:
    return SessionEnvelopeCodec(
        keys or (key(1),),
        namespace="template-testing",
        idle_timeout_seconds=idle,
        absolute_timeout_seconds=absolute,
        sid_renewal_seconds=renewal,
        clock_skew_seconds=skew,
        allowed_keys=allowed_keys,
        strict_schema=strict_schema,
        max_plaintext_bytes=max_plaintext,
        max_envelope_bytes=max_envelope,
    )


def metadata(now: int = 100, *, subject: str | None = None) -> SessionMetadata:
    return SessionMetadata(now, now, now, subject)


def test_round_trip_encrypts_authenticates_and_hides_plaintext() -> None:
    current = codec()
    subject = subject_fingerprint("Tenant", "Object")
    data: dict[str, object] = {
        "_permanent": True,
        "_msentra_0123456789abcdef": {"session_id": "abc_123", "flow_id": "flow-456"},
        "cart": {"items": ["private-value", 2, True, None]},
        "counter": 3,
    }
    sealed = current.seal("s" * 32, data, metadata(subject=subject))
    assert b"private-value" not in sealed
    decoded = current.open("s" * 32, sealed, now=110)
    assert decoded.data == data
    assert decoded.metadata.subject_id == subject
    assert decoded.metadata.subject_revision == 0
    assert decoded.key_id == current.active_key_id
    assert decoded.needs_rewrap is False
    assert decoded.rotation_due is False
    assert current.absolute_timeout_seconds == 300
    assert current.idle_timeout_seconds == 60
    assert current.clock_skew_seconds == 5


def test_tampering_sid_swap_and_unknown_key_are_rejected() -> None:
    current = codec()
    sealed = current.seal("a" * 32, {"counter": 1}, metadata())
    tampered = bytearray(sealed)
    tampered[-2] = ord("A") if tampered[-2] != ord("A") else ord("B")
    with pytest.raises(SessionEnvelopeError):
        current.open("a" * 32, bytes(tampered), now=101)
    with pytest.raises(SessionEnvelopeError, match="authentication"):
        current.open("b" * 32, sealed, now=101)

    outer = json.loads(sealed)
    outer["kid"] = "0" * 16
    with pytest.raises(SessionEnvelopeError, match="unavailable"):
        current.open("a" * 32, json.dumps(outer).encode(), now=101)


def test_key_rotation_rewrap_and_retirement() -> None:
    old = codec(key(1))
    sealed = old.seal("s" * 32, {"counter": 1}, metadata())
    rotating = codec(key(2), key(1))
    decoded = rotating.open("s" * 32, sealed, now=101)
    assert decoded.needs_rewrap is True
    migrated = rotating.seal("s" * 32, decoded.data, decoded.metadata)
    assert rotating.open("s" * 32, migrated, now=102).needs_rewrap is False
    with pytest.raises(SessionEnvelopeError, match="unavailable"):
        codec(key(2)).open("s" * 32, sealed, now=102)


def test_idle_absolute_rotation_and_clock_skew() -> None:
    current = codec(idle=20, absolute=50, renewal=15, skew=3)
    sealed = current.seal("s" * 32, {"counter": 1}, metadata())
    assert current.open("s" * 32, sealed, now=115).rotation_due is True
    with pytest.raises(SessionEnvelopeExpired, match="idle"):
        current.open("s" * 32, sealed, now=124)

    refreshed = SessionMetadata(100, 140, 100)
    refreshed_sealed = current.seal("s" * 32, {"counter": 1}, refreshed)
    with pytest.raises(SessionEnvelopeExpired, match="absolute"):
        current.open("s" * 32, refreshed_sealed, now=154)

    future = replace(metadata(), issued_at=104, last_seen_at=104, sid_rotated_at=104)
    within_skew = current.seal("s" * 32, {"counter": 1}, future)
    assert current.open("s" * 32, within_skew, now=101).metadata.issued_at == 104
    too_far = replace(future, issued_at=105, last_seen_at=105, sid_rotated_at=105)
    with pytest.raises(SessionEnvelopeError, match="future"):
        current.open("s" * 32, current.seal("s" * 32, {"counter": 1}, too_far), now=101)


def test_metadata_refresh_preserves_or_resets_lifetime() -> None:
    current = codec()
    original = SessionMetadata(10, 20, 15, subject_fingerprint("t", "o"))
    refreshed = current.refresh_metadata(original, 30)
    assert refreshed == SessionMetadata(10, 30, 15, original.subject_id)
    rotated = current.refresh_metadata(original, 30, rotate_sid=True, subject_id=original.subject_id)
    assert rotated == SessionMetadata(10, 30, 30, original.subject_id)
    reset = current.refresh_metadata(original, 30, reset_lifetime=True, subject_id=None)
    assert reset == SessionMetadata(30, 30, 30, original.subject_id)
    replacement_subject = subject_fingerprint("new", "subject")
    rebound = current.refresh_metadata(
        original, 30, subject_id=replacement_subject, subject_revision=7
    )
    assert rebound.subject_id == replacement_subject
    assert rebound.subject_revision == 7
    assert current.new_metadata(5) == SessionMetadata(5, 5, 5, None)


def test_schema_allowlist_and_extension_metadata() -> None:
    current = codec()
    assert current.validate_session_data({"_permanent": False, "counter": 1}) == {
        "_permanent": False,
        "counter": 1,
    }
    invalid: tuple[object, ...] = (
        {"unknown": 1},
        {"_permanent": "true"},
        {"_msentra_0123456789abcdef": {"other": "x"}},
        {"_msentra_0123456789abcdef": {"session_id": "bad space"}},
        {"counter": object()},
        {"counter": float("nan")},
        {"counter": 2**64},
        {"counter": "x" * (16 * 1024 + 1)},
        {"counter": tuple()},
        {"bad key": 1},
    )
    for value in invalid:
        with pytest.raises(SessionEnvelopeError):
            current.validate_session_data(value)

    relaxed = codec(strict_schema=False, allowed_keys=())
    assert relaxed.validate_session_data({"anything": {"nested": [1, 2]}}) == {
        "anything": {"nested": [1, 2]}
    }


def test_schema_limits_depth_and_collection_sizes() -> None:
    current = codec()
    nested: object = "leaf"
    for _ in range(10):
        nested = {"level": nested}
    with pytest.raises(SessionEnvelopeError, match="depth"):
        current.validate_session_data({"profile": nested})
    with pytest.raises(SessionEnvelopeError, match="too many"):
        current.validate_session_data({f"k{i}": i for i in range(129)})
    with pytest.raises(SessionEnvelopeError, match="too many"):
        current.validate_session_data({"profile": list(range(129))})


def test_size_limits_apply_before_and_after_protection() -> None:
    with pytest.raises(SessionEnvelopeError, match="plaintext"):
        codec(max_plaintext=80).seal("s" * 32, {"profile": "x" * 100}, metadata())
    tiny = codec(max_envelope=32)
    with pytest.raises(SessionEnvelopeError, match="envelope"):
        tiny.seal("s" * 32, {"counter": 1}, metadata())
    normal = codec()
    with pytest.raises(SessionEnvelopeError, match="size"):
        normal.open("s" * 32, b"x" * (96 * 1024 + 1), now=100)


def test_invalid_outer_inner_and_base64_inputs_are_rejected() -> None:
    current = codec()
    sid = "s" * 32
    sealed = current.seal(sid, {"counter": 1}, metadata())
    outer = json.loads(sealed)
    mutations: list[dict[str, Any]] = [
        {**outer, "extra": 1},
        {**outer, "v": True},
        {**outer, "v": 2},
        {**outer, "nonce": "***"},
        {**outer, "nonce": "AA"},
        {**outer, "ciphertext": "AA"},
    ]
    for mutation in mutations:
        with pytest.raises(SessionEnvelopeError):
            current.open(sid, json.dumps(mutation).encode(), now=100)
    for raw in (b"", b"[]", b"{", b"\xff"):
        with pytest.raises(SessionEnvelopeError):
            current.open(sid, raw, now=100)


def test_constructor_and_argument_validation() -> None:
    valid = dict(
        keys=(key(1),),
        namespace="valid",
        idle_timeout_seconds=10,
        absolute_timeout_seconds=20,
        sid_renewal_seconds=5,
        clock_skew_seconds=0,
    )
    invalid_changes: tuple[dict[str, Any], ...] = (
        {"keys": ()},
        {"keys": (key(1), key(1))},
        {"keys": ("",)},
        {"keys": (object(),)},
        {"namespace": ""},
        {"namespace": "bad namespace"},
        {"idle_timeout_seconds": 0},
        {"absolute_timeout_seconds": 0},
        {"sid_renewal_seconds": 0},
        {"clock_skew_seconds": -1},
        {"absolute_timeout_seconds": 5},
        {"sid_renewal_seconds": 20},
        {"max_plaintext_bytes": 0},
        {"max_envelope_bytes": 0},
        {"allowed_keys": ("bad key",)},
    )
    for changes in invalid_changes:
        with pytest.raises((TypeError, ValueError, SessionEnvelopeError)):
            SessionEnvelopeCodec(**(valid | changes))

    current = SessionEnvelopeCodec(**valid)
    for bad_sid in ("short", None):
        with pytest.raises(SessionEnvelopeError, match="SID"):
            current.seal(bad_sid, {}, metadata())  # type: ignore[arg-type]
    with pytest.raises(SessionEnvelopeError, match="metadata"):
        current.seal("s" * 32, {}, object())  # type: ignore[arg-type]
    with pytest.raises(SessionEnvelopeError, match="mapping"):
        current.validate_session_data([])
    with pytest.raises(SessionEnvelopeError, match="non-negative"):
        current.new_metadata(-1)
    with pytest.raises(ValueError):
        subject_fingerprint("", "object")
    with pytest.raises(ValueError):
        subject_fingerprint("tenant", "")


def test_timestamp_order_and_subject_validation() -> None:
    current = codec()
    sid = "s" * 32
    invalid_metadata = (
        SessionMetadata(100, 99, 100),
        SessionMetadata(100, 100, 99),
        SessionMetadata(100, 100, 100, "bad"),
        SessionMetadata(100, 100, 100, None, -1),
        SessionMetadata(True, 100, 100),  # type: ignore[arg-type]
    )
    for item in invalid_metadata:
        if (
            item.subject_id == "bad"
            or item.subject_revision < 0
            or isinstance(item.issued_at, bool)
        ):
            with pytest.raises(SessionEnvelopeError):
                current.seal(sid, {}, item)
        else:
            sealed = current.seal(sid, {}, item)
            with pytest.raises(SessionEnvelopeError):
                current.open(sid, sealed, now=100)


def test_defensive_private_helpers_and_rare_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    current = codec(key(1))
    sid = "s" * 32
    sealed = current.seal(sid, {"counter": 1.5}, metadata())
    assert current.open(sid, sealed, now=100).data["counter"] == 1.5

    with pytest.raises(SessionEnvelopeError, match="must be bytes"):
        current.open(sid, "not-bytes", now=100)  # type: ignore[arg-type]

    large = codec(key(1), max_plaintext=4096)
    large_sealed = large.seal(sid, {"profile": "x" * 1024}, metadata())
    small = codec(key(1), max_plaintext=256)
    with pytest.raises(SessionEnvelopeError, match="plaintext"):
        small.open(sid, large_sealed, now=100)

    outer = json.loads(sealed)
    active = current._keys[current.active_key_id]  # type: ignore[attr-defined]
    nonce = b"n" * 12
    invalid_inner = envelope_module._canonical_json({"issued_at": 100})
    ciphertext = envelope_module.AESGCM(active.key).encrypt(
        nonce, invalid_inner, current._aad(sid, current.active_key_id)
    )
    forged = envelope_module._canonical_json(
        {
            "v": 1,
            "kid": current.active_key_id,
            "nonce": envelope_module._b64encode(nonce),
            "ciphertext": envelope_module._b64encode(ciphertext),
        }
    )
    with pytest.raises(SessionEnvelopeError, match="invalid structure"):
        current.open(sid, forged, now=100)

    with pytest.raises(SessionEnvelopeError, match="serialized"):
        envelope_module._canonical_json({"bad": {1, 2}})
    with pytest.raises(SessionEnvelopeError, match="mapping"):
        envelope_module._validate_extension_metadata([])
    with pytest.raises(SessionEnvelopeError, match="too many"):
        current.validate_session_data({"profile": {f"k{i}": i for i in range(129)}})
    with pytest.raises(SessionEnvelopeError, match="invalid key"):
        current.validate_session_data({1: "value"})
    with pytest.raises(SessionEnvelopeError, match="subject"):
        current.new_metadata(1, subject_id=123)  # type: ignore[arg-type]
    with pytest.raises(SessionEnvelopeError, match="subject"):
        current.new_metadata(1, subject_id="a" * 65)

    assert SessionEnvelopeCodec(
        (b"x" * 32,),
        namespace="bytes-key",
        idle_timeout_seconds=10,
        absolute_timeout_seconds=20,
        sid_renewal_seconds=5,
        clock_skew_seconds=0,
    ).active_key_id
    with pytest.raises(ValueError, match="empty"):
        SessionEnvelopeCodec(
            (b"",),
            namespace="bytes-key",
            idle_timeout_seconds=10,
            absolute_timeout_seconds=20,
            sid_renewal_seconds=5,
            clock_skew_seconds=0,
        )
    assert SessionEnvelopeCodec(
        ("not base64 material!",),
        namespace="plain-key",
        idle_timeout_seconds=10,
        absolute_timeout_seconds=20,
        sid_renewal_seconds=5,
        clock_skew_seconds=0,
    ).active_key_id
    assert SessionEnvelopeCodec(
        ("A",),
        namespace="fallback-key",
        idle_timeout_seconds=10,
        absolute_timeout_seconds=20,
        sid_renewal_seconds=5,
        clock_skew_seconds=0,
    ).active_key_id

    with pytest.raises(SessionEnvelopeError):
        envelope_module._b64decode(None, "value", maximum=10)
    with pytest.raises(SessionEnvelopeError):
        envelope_module._b64decode("A", "value", maximum=10)
    with pytest.raises(SessionEnvelopeError, match="byte limit"):
        envelope_module._b64decode(
            envelope_module._b64encode(b"123456"), "value", maximum=5
        )

    def explode(_: bytes) -> bytes:
        raise binascii.Error("boom")

    import binascii

    monkeypatch.setattr(envelope_module.base64, "urlsafe_b64decode", explode)
    assert SessionEnvelopeCodec(
        ("A",),
        namespace="fallback-exception",
        idle_timeout_seconds=10,
        absolute_timeout_seconds=20,
        sid_renewal_seconds=5,
        clock_skew_seconds=0,
    ).active_key_id


def test_public_activity_validation() -> None:
    current = codec(idle=10, absolute=20, renewal=5, skew=1)
    metadata = current.new_metadata(100)
    current.ensure_active(metadata, 110)
    with pytest.raises(SessionEnvelopeExpired, match="idle"):
        current.ensure_active(metadata, 112)


def test_timestamp_upper_bound() -> None:
    current = codec()
    with pytest.raises(SessionEnvelopeError, match="bounded"):
        current.new_metadata(253_402_300_800)

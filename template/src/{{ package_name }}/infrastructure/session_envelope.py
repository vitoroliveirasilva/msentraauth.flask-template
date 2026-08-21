from __future__ import annotations

import base64
import binascii
import json
import math
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from typing import Final

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

_VERSION: Final = 1
_NONCE_BYTES: Final = 12
_MAX_DEPTH: Final = 8
_MAX_ITEMS: Final = 128
_MAX_STRING: Final = 16 * 1024
_MAX_KEYS: Final = 5
_SAFE_KEY_RE: Final = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
_EXTENSION_KEY_RE: Final = re.compile(r"^_msentra_[0-9a-f]{16}$")
_IDENTIFIER_RE: Final = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_SUBJECT_RE: Final = re.compile(r"^[0-9a-f]{64}$")
_BASE64URL_RE: Final = re.compile(r"^[A-Za-z0-9_-]+={0,2}$")
_OUTER_KEYS: Final = frozenset({"v", "kid", "nonce", "ciphertext"})
_INNER_KEYS: Final = frozenset(
    {"issued_at", "last_seen_at", "sid_rotated_at", "subject_id", "subject_revision", "data"}
)
_EXTENSION_METADATA_KEYS: Final = frozenset({"session_id", "flow_id"})
_KDF_INFO: Final = b"flask-entra-template/session-payload/v1"


class SessionEnvelopeError(ValueError):
    pass


class SessionEnvelopeExpired(SessionEnvelopeError):
    pass


@dataclass(frozen=True, slots=True)
class SessionMetadata:
    issued_at: int
    last_seen_at: int
    sid_rotated_at: int
    subject_id: str | None = None
    subject_revision: int = 0


@dataclass(frozen=True, slots=True)
class DecodedSession:
    data: dict[str, object]
    metadata: SessionMetadata
    key_id: str
    needs_rewrap: bool
    rotation_due: bool


@dataclass(frozen=True, slots=True)
class _PayloadKey:
    key_id: str
    key: bytes


class SessionEnvelopeCodec:
    def __init__(
        self,
        keys: Sequence[str | bytes],
        *,
        namespace: str,
        idle_timeout_seconds: int,
        absolute_timeout_seconds: int,
        sid_renewal_seconds: int,
        clock_skew_seconds: int,
        allowed_keys: Sequence[str] = (),
        strict_schema: bool = True,
        max_plaintext_bytes: int = 64 * 1024,
        max_envelope_bytes: int = 96 * 1024,
    ) -> None:
        if not keys:
            raise ValueError("session payload key ring cannot be empty")
        if len(keys) > _MAX_KEYS:
            raise ValueError("session payload key ring cannot contain more than five keys")
        prepared = tuple(_prepare_key(item) for item in keys)
        if len({item.key_id for item in prepared}) != len(prepared):
            raise ValueError("session payload key ring contains duplicate material")
        if not namespace or len(namespace) > 64 or not _SAFE_KEY_RE.fullmatch(namespace):
            raise ValueError("session namespace is invalid")
        _positive(idle_timeout_seconds, "idle_timeout_seconds")
        _positive(absolute_timeout_seconds, "absolute_timeout_seconds")
        _positive(sid_renewal_seconds, "sid_renewal_seconds")
        _non_negative(clock_skew_seconds, "clock_skew_seconds")
        if absolute_timeout_seconds < idle_timeout_seconds:
            raise ValueError("absolute timeout cannot be shorter than idle timeout")
        if sid_renewal_seconds >= absolute_timeout_seconds:
            raise ValueError("SID renewal interval must be shorter than absolute timeout")
        _positive(max_plaintext_bytes, "max_plaintext_bytes")
        _positive(max_envelope_bytes, "max_envelope_bytes")
        if max_plaintext_bytes > max_envelope_bytes:
            raise ValueError("max_envelope_bytes cannot be smaller than max_plaintext_bytes")
        self._keys = {item.key_id: item for item in prepared}
        self._active = prepared[0]
        self._namespace = namespace
        self._idle = idle_timeout_seconds
        self._absolute = absolute_timeout_seconds
        self._renewal = sid_renewal_seconds
        self._skew = clock_skew_seconds
        self._allowed_keys = frozenset(_safe_key(k) for k in allowed_keys)
        self._strict = bool(strict_schema)
        self._max_plaintext = max_plaintext_bytes
        self._max_envelope = max_envelope_bytes

    @property
    def idle_timeout_seconds(self) -> int:
        return self._idle

    @property
    def absolute_timeout_seconds(self) -> int:
        return self._absolute

    @property
    def active_key_id(self) -> str:
        return self._active.key_id

    @property
    def clock_skew_seconds(self) -> int:
        return self._skew

    def new_metadata(self, now: int) -> SessionMetadata:
        timestamp = _timestamp(now, "now")
        return SessionMetadata(timestamp, timestamp, timestamp)

    def ensure_active(self, metadata: SessionMetadata, now: int) -> None:
        self._validate_timestamps(_metadata(metadata), _timestamp(now, "now"))

    def refresh_metadata(
        self,
        metadata: SessionMetadata,
        now: int,
        *,
        rotate_sid: bool = False,
        reset_lifetime: bool = False,
        subject_id: str | None = None,
        subject_revision: int | None = None,
    ) -> SessionMetadata:
        timestamp = _timestamp(now, "now")
        subject = metadata.subject_id if subject_id is None else _subject(subject_id)
        revision = (
            metadata.subject_revision if subject_revision is None else _revision(subject_revision)
        )
        if reset_lifetime:
            return SessionMetadata(timestamp, timestamp, timestamp, subject, revision)
        return SessionMetadata(
            metadata.issued_at,
            max(metadata.last_seen_at, timestamp),
            timestamp if rotate_sid else metadata.sid_rotated_at,
            subject,
            revision,
        )

    def seal(self, sid: str, data: Mapping[str, object], metadata: SessionMetadata) -> bytes:
        sid = _sid(sid)
        normalized = self.validate_session_data(data)
        meta = _metadata(metadata)
        plaintext = _json(
            {
                "issued_at": meta.issued_at,
                "last_seen_at": meta.last_seen_at,
                "sid_rotated_at": meta.sid_rotated_at,
                "subject_id": meta.subject_id,
                "subject_revision": meta.subject_revision,
                "data": normalized,
            }
        )
        if len(plaintext) > self._max_plaintext:
            raise SessionEnvelopeError("session plaintext exceeds the configured byte limit")
        nonce = os.urandom(_NONCE_BYTES)
        ciphertext = AESGCM(self._active.key).encrypt(
            nonce, plaintext, self._aad(sid, self._active.key_id)
        )
        envelope = _json(
            {
                "v": _VERSION,
                "kid": self._active.key_id,
                "nonce": _b64(nonce),
                "ciphertext": _b64(ciphertext),
            }
        )
        if len(envelope) > self._max_envelope:
            raise SessionEnvelopeError("session envelope exceeds the configured byte limit")
        return envelope

    def open(self, sid: str, envelope: bytes, *, now: int) -> DecodedSession:
        sid = _sid(sid)
        if not isinstance(envelope, bytes) or not envelope or len(envelope) > self._max_envelope:
            raise SessionEnvelopeError("session envelope size is invalid")
        outer = _mapping(envelope, "session envelope")
        if frozenset(outer) != _OUTER_KEYS or outer.get("v") != _VERSION:
            raise SessionEnvelopeError("session envelope has an invalid structure")
        kid = outer.get("kid")
        if not isinstance(kid, str) or kid not in self._keys:
            raise SessionEnvelopeError("session envelope key is unavailable")
        nonce = _unb64(outer.get("nonce"), "session nonce", 64)
        ciphertext = _unb64(outer.get("ciphertext"), "session ciphertext", self._max_envelope)
        if len(nonce) != _NONCE_BYTES or len(ciphertext) < 16:
            raise SessionEnvelopeError("session envelope cryptographic fields are invalid")
        try:
            plaintext = AESGCM(self._keys[kid].key).decrypt(nonce, ciphertext, self._aad(sid, kid))
        except InvalidTag as exc:
            raise SessionEnvelopeError("session envelope authentication failed") from exc
        if len(plaintext) > self._max_plaintext:
            raise SessionEnvelopeError("session plaintext exceeds the configured byte limit")
        inner = _mapping(plaintext, "session payload")
        if frozenset(inner) != _INNER_KEYS:
            raise SessionEnvelopeError("session payload has an invalid structure")
        meta = SessionMetadata(
            _timestamp(inner.get("issued_at"), "issued_at"),
            _timestamp(inner.get("last_seen_at"), "last_seen_at"),
            _timestamp(inner.get("sid_rotated_at"), "sid_rotated_at"),
            _subject(inner.get("subject_id")),
            _revision(inner.get("subject_revision")),
        )
        timestamp = _timestamp(now, "now")
        self._validate_timestamps(meta, timestamp)
        return DecodedSession(
            self.validate_session_data(inner.get("data")),
            meta,
            kid,
            kid != self._active.key_id,
            timestamp - meta.sid_rotated_at >= self._renewal,
        )

    def validate_session_data(self, value: object) -> dict[str, object]:
        if not isinstance(value, Mapping) or len(value) > _MAX_ITEMS:
            raise SessionEnvelopeError("session data must be a bounded mapping")
        result: dict[str, object] = {}
        for raw_key, raw_value in value.items():
            key = _safe_key(raw_key)
            if key == "_permanent":
                if not isinstance(raw_value, bool):
                    raise SessionEnvelopeError("_permanent must be boolean")
                result[key] = raw_value
            elif _EXTENSION_KEY_RE.fullmatch(key):
                result[key] = _extension_metadata(raw_value)
            else:
                if self._strict and key not in self._allowed_keys:
                    raise SessionEnvelopeError("session data contains a key outside the allowlist")
                result[key] = _json_value(raw_value, 1)
        return result

    def _validate_timestamps(self, meta: SessionMetadata, now: int) -> None:
        future = now + self._skew
        if (
            meta.issued_at > future
            or not meta.issued_at <= meta.last_seen_at <= future
            or not meta.issued_at <= meta.sid_rotated_at <= future
        ):
            raise SessionEnvelopeError("session timestamps are invalid")
        if now - meta.last_seen_at > self._idle + self._skew:
            raise SessionEnvelopeExpired("session idle timeout was exceeded")
        if now - meta.issued_at > self._absolute + self._skew:
            raise SessionEnvelopeExpired("session absolute timeout was exceeded")

    def _aad(self, sid: str, kid: str) -> bytes:
        return f"session|v={_VERSION}|ns={self._namespace}|sid={sid}|kid={kid}".encode("ascii")


def subject_fingerprint(tenant_id: str, object_id: str) -> str:
    tenant = _identity(tenant_id, "tenant_id")
    object_value = _identity(object_id, "object_id")
    return sha256(f"{tenant}\0{object_value}".encode()).hexdigest()


def _prepare_key(value: str | bytes) -> _PayloadKey:
    if isinstance(value, str):
        if not value:
            raise ValueError("session payload keys cannot be empty")
        source = _decode_source(value)
    elif isinstance(value, bytes) and value:
        source = value
    else:
        raise TypeError("session payload keys must be non-empty strings or bytes")
    if len(source) < 32:
        raise ValueError("session payload keys must contain at least 32 bytes")
    derived = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=_KDF_INFO).derive(source)
    return _PayloadKey(sha256(b"kid\0" + derived).hexdigest()[:16], derived)


def _decode_source(value: str) -> bytes:
    if _BASE64URL_RE.fullmatch(value):
        try:
            decoded = base64.urlsafe_b64decode((value + "=" * (-len(value) % 4)).encode("ascii"))
            if len(decoded) >= 32:
                return decoded
        except (UnicodeError, binascii.Error, ValueError):
            pass
    return value.encode()


def _json(value: object) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True
        ).encode()
    except (TypeError, ValueError, UnicodeError) as exc:
        raise SessionEnvelopeError("session data could not be serialized") from exc


def _mapping(value: bytes, label: str) -> dict[str, object]:
    try:
        decoded = json.loads(value.decode(), object_pairs_hook=_unique_mapping)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SessionEnvelopeError(f"{label} is not valid JSON") from exc
    if not isinstance(decoded, dict):
        raise SessionEnvelopeError(f"{label} must be a mapping")
    return decoded


def _unique_mapping(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SessionEnvelopeError("session JSON contains duplicate keys")
        result[key] = value
    return result


def _extension_metadata(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping) or not set(value).issubset(_EXTENSION_METADATA_KEYS):
        raise SessionEnvelopeError("Microsoft Entra session metadata is invalid")
    result: dict[str, str] = {}
    for key, item in value.items():
        if (
            not isinstance(key, str)
            or not isinstance(item, str)
            or not _IDENTIFIER_RE.fullmatch(item)
        ):
            raise SessionEnvelopeError("Microsoft Entra session metadata is invalid")
        result[key] = item
    return result


def _json_value(value: object, depth: int) -> object:
    if depth > _MAX_DEPTH:
        raise SessionEnvelopeError("session data exceeds nesting limit")
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        if not -(2**63) <= value <= 2**63 - 1:
            raise SessionEnvelopeError("session integer is outside supported range")
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SessionEnvelopeError("session float must be finite")
        return value
    if isinstance(value, str):
        if len(value) > _MAX_STRING:
            raise SessionEnvelopeError("session string is too long")
        return value
    if isinstance(value, Mapping):
        if len(value) > _MAX_ITEMS:
            raise SessionEnvelopeError("session mapping contains too many items")
        return {_safe_key(k): _json_value(v, depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        if len(value) > _MAX_ITEMS:
            raise SessionEnvelopeError("session list contains too many items")
        return [_json_value(v, depth + 1) for v in value]
    raise SessionEnvelopeError("session data contains an unsupported type")


def _safe_key(value: object) -> str:
    if not isinstance(value, str) or not _SAFE_KEY_RE.fullmatch(value):
        raise SessionEnvelopeError("session data contains an invalid key")
    return value


def _sid(value: object) -> str:
    if not isinstance(value, str) or len(value) < 32 or not _IDENTIFIER_RE.fullmatch(value):
        raise SessionEnvelopeError("session SID is invalid")
    return value


def _subject(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not _SUBJECT_RE.fullmatch(value):
        raise SessionEnvelopeError("session subject identifier is invalid")
    return value


def _metadata(value: object) -> SessionMetadata:
    if not isinstance(value, SessionMetadata):
        raise SessionEnvelopeError("session metadata is invalid")
    return SessionMetadata(
        _timestamp(value.issued_at, "issued_at"),
        _timestamp(value.last_seen_at, "last_seen_at"),
        _timestamp(value.sid_rotated_at, "sid_rotated_at"),
        _subject(value.subject_id),
        _revision(value.subject_revision),
    )


def _revision(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2**63 - 1:
        raise SessionEnvelopeError("session subject revision is invalid")
    return value


def _timestamp(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SessionEnvelopeError(f"session {name} must be a non-negative integer")
    return value


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _unb64(value: object, label: str, maximum: int) -> bytes:
    if not isinstance(value, str) or not value or not _BASE64URL_RE.fullmatch(value):
        raise SessionEnvelopeError(f"{label} is invalid")
    try:
        decoded = base64.urlsafe_b64decode((value + "=" * (-len(value) % 4)).encode("ascii"))
    except (UnicodeError, binascii.Error, ValueError) as exc:
        raise SessionEnvelopeError(f"{label} is invalid") from exc
    if len(decoded) > maximum:
        raise SessionEnvelopeError(f"{label} exceeds byte limit")
    return decoded


def _identity(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise ValueError(f"{name} is invalid")
    return value.strip().casefold()


def _positive(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be positive")


def _non_negative(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be non-negative")


__all__ = [
    "DecodedSession",
    "SessionEnvelopeCodec",
    "SessionEnvelopeError",
    "SessionEnvelopeExpired",
    "SessionMetadata",
    "subject_fingerprint",
]

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

_ENVELOPE_VERSION: Final = 1
_NONCE_BYTES: Final = 12
_MAX_DEPTH: Final = 8
_MAX_COLLECTION_ITEMS: Final = 128
_MAX_STRING_CHARACTERS: Final = 16 * 1024
_MAX_KEY_CHARACTERS: Final = 128
_MAX_SUBJECT_ID_CHARACTERS: Final = 64
_MAX_TIMESTAMP: Final = 253_402_300_799
_SAFE_KEY_RE: Final = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
_EXTENSION_KEY_RE: Final = re.compile(r"^_msentra_[0-9a-f]{16}$")
_IDENTIFIER_RE: Final = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_SUBJECT_ID_RE: Final = re.compile(r"^[0-9a-f]{64}$")
_BASE64URL_RE: Final = re.compile(r"^[A-Za-z0-9_-]+={0,2}$")
_OUTER_KEYS: Final = frozenset({"v", "kid", "nonce", "ciphertext"})
_INNER_KEYS: Final = frozenset({"issued_at", "last_seen_at", "sid_rotated_at", "subject_id", "subject_revision", "data"})
_EXTENSION_METADATA_KEYS: Final = frozenset({"session_id", "flow_id"})
_KDF_INFO: Final = b"msentraauth-flask-template/session-payload/v1"


class SessionEnvelopeError(ValueError):
    """Base para envelopes ausentes, adulterados, incompatíveis ou fora do contrato"""


class SessionEnvelopeExpired(SessionEnvelopeError):
    """Indica expiração ociosa ou absoluta de uma sessão autenticada"""


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
    """Protege o payload Redis com AEAD, schema estrito e timestamps autenticados"""

    __slots__ = (
        "_absolute_timeout_seconds",
        "_active",
        "_allowed_keys",
        "_clock_skew_seconds",
        "_idle_timeout_seconds",
        "_keys",
        "_max_envelope_bytes",
        "_max_plaintext_bytes",
        "_namespace",
        "_sid_renewal_seconds",
        "_strict_schema",
    )

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
        prepared = tuple(_prepare_key(value) for value in keys)
        if len({item.key_id for item in prepared}) != len(prepared):
            raise ValueError("session payload key ring contains duplicate material")
        if not isinstance(namespace, str) or not namespace or len(namespace) > 64:
            raise ValueError("session namespace must contain between 1 and 64 characters")
        if not _SAFE_KEY_RE.fullmatch(namespace):
            raise ValueError("session namespace contains unsupported characters")
        _positive_int(idle_timeout_seconds, "idle_timeout_seconds")
        _positive_int(absolute_timeout_seconds, "absolute_timeout_seconds")
        _positive_int(sid_renewal_seconds, "sid_renewal_seconds")
        _non_negative_int(clock_skew_seconds, "clock_skew_seconds")
        _positive_int(max_plaintext_bytes, "max_plaintext_bytes")
        _positive_int(max_envelope_bytes, "max_envelope_bytes")
        if absolute_timeout_seconds < idle_timeout_seconds:
            raise ValueError("absolute timeout cannot be shorter than idle timeout")
        if sid_renewal_seconds >= absolute_timeout_seconds:
            raise ValueError("SID renewal interval must be shorter than absolute timeout")
        normalized_allowed = tuple(dict.fromkeys(_validate_allowed_key(key) for key in allowed_keys))
        self._keys = {item.key_id: item for item in prepared}
        self._active = prepared[0]
        self._namespace = namespace
        self._idle_timeout_seconds = idle_timeout_seconds
        self._absolute_timeout_seconds = absolute_timeout_seconds
        self._sid_renewal_seconds = sid_renewal_seconds
        self._clock_skew_seconds = clock_skew_seconds
        self._allowed_keys = frozenset(normalized_allowed)
        self._strict_schema = bool(strict_schema)
        self._max_plaintext_bytes = max_plaintext_bytes
        self._max_envelope_bytes = max_envelope_bytes

    @property
    def active_key_id(self) -> str:
        return self._active.key_id

    @property
    def absolute_timeout_seconds(self) -> int:
        return self._absolute_timeout_seconds

    @property
    def idle_timeout_seconds(self) -> int:
        return self._idle_timeout_seconds

    @property
    def clock_skew_seconds(self) -> int:
        return self._clock_skew_seconds

    def new_metadata(
        self,
        now: int,
        *,
        subject_id: str | None = None,
        subject_revision: int = 0,
    ) -> SessionMetadata:
        timestamp = _timestamp(now, "now")
        return SessionMetadata(
            timestamp,
            timestamp,
            timestamp,
            _validate_subject_id(subject_id),
            _revision(subject_revision),
        )

    def ensure_active(self, metadata: SessionMetadata, now: int) -> None:
        """Falha quando timestamps autenticados não estão válidos no relógio informado"""
        self._validate_timestamps(_validate_metadata_shape(metadata), _timestamp(now, "now"))

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
        resolved_subject = (
            metadata.subject_id if subject_id is None else _validate_subject_id(subject_id)
        )
        resolved_revision = (
            metadata.subject_revision
            if subject_revision is None
            else _revision(subject_revision)
        )
        if reset_lifetime:
            return SessionMetadata(
                timestamp, timestamp, timestamp, resolved_subject, resolved_revision
            )
        return SessionMetadata(
            issued_at=metadata.issued_at,
            last_seen_at=max(metadata.last_seen_at, timestamp),
            sid_rotated_at=timestamp if rotate_sid else metadata.sid_rotated_at,
            subject_id=resolved_subject,
            subject_revision=resolved_revision,
        )

    def seal(self, sid: str, data: Mapping[str, object], metadata: SessionMetadata) -> bytes:
        normalized_sid = _validate_sid(sid)
        normalized_data = self.validate_session_data(data)
        normalized_metadata = _validate_metadata_shape(metadata)
        inner = {
            "issued_at": normalized_metadata.issued_at,
            "last_seen_at": normalized_metadata.last_seen_at,
            "sid_rotated_at": normalized_metadata.sid_rotated_at,
            "subject_id": normalized_metadata.subject_id,
            "subject_revision": normalized_metadata.subject_revision,
            "data": normalized_data,
        }
        plaintext = _canonical_json(inner)
        if len(plaintext) > self._max_plaintext_bytes:
            raise SessionEnvelopeError("session plaintext exceeds the configured byte limit")
        nonce = os.urandom(_NONCE_BYTES)
        aad = self._aad(normalized_sid, self._active.key_id)
        ciphertext = AESGCM(self._active.key).encrypt(nonce, plaintext, aad)
        envelope = _canonical_json(
            {
                "v": _ENVELOPE_VERSION,
                "kid": self._active.key_id,
                "nonce": _b64encode(nonce),
                "ciphertext": _b64encode(ciphertext),
            }
        )
        if len(envelope) > self._max_envelope_bytes:
            raise SessionEnvelopeError("session envelope exceeds the configured byte limit")
        return envelope

    def open(self, sid: str, envelope: bytes, *, now: int) -> DecodedSession:
        normalized_sid = _validate_sid(sid)
        timestamp = _timestamp(now, "now")
        if not isinstance(envelope, bytes):
            raise SessionEnvelopeError("session envelope must be bytes")
        if not envelope or len(envelope) > self._max_envelope_bytes:
            raise SessionEnvelopeError("session envelope size is invalid")
        outer = _json_mapping(envelope, "session envelope")
        if frozenset(outer) != _OUTER_KEYS:
            raise SessionEnvelopeError("session envelope has an invalid structure")
        version = outer.get("v")
        if isinstance(version, bool) or not isinstance(version, int):
            raise SessionEnvelopeError("session envelope version is invalid")
        if version != _ENVELOPE_VERSION:
            raise SessionEnvelopeError("session envelope version is unsupported")
        key_id = outer.get("kid")
        if not isinstance(key_id, str) or key_id not in self._keys:
            raise SessionEnvelopeError("session envelope key is unavailable")
        nonce = _b64decode(outer.get("nonce"), "session nonce", maximum=64)
        if len(nonce) != _NONCE_BYTES:
            raise SessionEnvelopeError("session nonce has an invalid length")
        ciphertext = _b64decode(
            outer.get("ciphertext"),
            "session ciphertext",
            maximum=self._max_envelope_bytes,
        )
        if len(ciphertext) < 16:
            raise SessionEnvelopeError("session ciphertext is invalid")
        payload_key = self._keys[key_id]
        try:
            plaintext = AESGCM(payload_key.key).decrypt(
                nonce,
                ciphertext,
                self._aad(normalized_sid, key_id),
            )
        except InvalidTag as exc:
            raise SessionEnvelopeError("session envelope authentication failed") from exc
        if len(plaintext) > self._max_plaintext_bytes:
            raise SessionEnvelopeError("session plaintext exceeds the configured byte limit")
        inner = _json_mapping(plaintext, "session payload")
        if frozenset(inner) != _INNER_KEYS:
            raise SessionEnvelopeError("session payload has an invalid structure")
        metadata = SessionMetadata(
            issued_at=_timestamp(inner.get("issued_at"), "issued_at"),
            last_seen_at=_timestamp(inner.get("last_seen_at"), "last_seen_at"),
            sid_rotated_at=_timestamp(inner.get("sid_rotated_at"), "sid_rotated_at"),
            subject_id=_validate_subject_id(inner.get("subject_id")),
            subject_revision=_revision(inner.get("subject_revision")),
        )
        self._validate_timestamps(metadata, timestamp)
        data = self.validate_session_data(inner.get("data"))
        return DecodedSession(
            data=data,
            metadata=metadata,
            key_id=key_id,
            needs_rewrap=key_id != self._active.key_id,
            rotation_due=(timestamp - metadata.sid_rotated_at) >= self._sid_renewal_seconds,
        )

    def validate_session_data(self, value: object) -> dict[str, object]:
        if not isinstance(value, Mapping):
            raise SessionEnvelopeError("session data must be a mapping")
        if len(value) > _MAX_COLLECTION_ITEMS:
            raise SessionEnvelopeError("session data contains too many keys")
        normalized: dict[str, object] = {}
        for raw_key, raw_value in value.items():
            key = _validate_allowed_key(raw_key)
            if key == "_permanent":
                if not isinstance(raw_value, bool):
                    raise SessionEnvelopeError("_permanent must be a boolean")
                normalized[key] = raw_value
                continue
            if _EXTENSION_KEY_RE.fullmatch(key):
                normalized[key] = _validate_extension_metadata(raw_value)
                continue
            if self._strict_schema and key not in self._allowed_keys:
                raise SessionEnvelopeError("session data contains a key outside the allowlist")
            normalized[key] = _validate_json_value(raw_value, depth=1)
        return normalized

    def _validate_timestamps(self, metadata: SessionMetadata, now: int) -> None:
        latest_accepted = now + self._clock_skew_seconds
        if metadata.issued_at > latest_accepted:
            raise SessionEnvelopeError("session issued_at is in the future")
        if not metadata.issued_at <= metadata.last_seen_at <= latest_accepted:
            raise SessionEnvelopeError("session last_seen_at is invalid")
        if not metadata.issued_at <= metadata.sid_rotated_at <= latest_accepted:
            raise SessionEnvelopeError("session sid_rotated_at is invalid")
        if now - metadata.last_seen_at > self._idle_timeout_seconds + self._clock_skew_seconds:
            raise SessionEnvelopeExpired("session idle timeout was exceeded")
        if now - metadata.issued_at > self._absolute_timeout_seconds + self._clock_skew_seconds:
            raise SessionEnvelopeExpired("session absolute timeout was exceeded")

    def _aad(self, sid: str, key_id: str) -> bytes:
        return (
            f"msentra-session|v={_ENVELOPE_VERSION}|ns={self._namespace}|sid={sid}|kid={key_id}"
        ).encode("ascii")


def subject_fingerprint(tenant_id: str, object_id: str) -> str:
    tenant = _identity_component(tenant_id, "tenant_id")
    object_value = _identity_component(object_id, "object_id")
    return sha256(f"{tenant}\x00{object_value}".encode("utf-8")).hexdigest()


def _prepare_key(value: str | bytes) -> _PayloadKey:
    if isinstance(value, str):
        if not value:
            raise ValueError("session payload keys cannot be empty")
        source = _decode_key_source(value)
    elif isinstance(value, bytes):
        if not value:
            raise ValueError("session payload keys cannot be empty")
        source = value
    else:
        raise TypeError("session payload keys must be strings or bytes")
    derived = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=_KDF_INFO,
    ).derive(source)
    key_id = sha256(b"kid\x00" + derived).hexdigest()[:16]
    return _PayloadKey(key_id=key_id, key=derived)


def _decode_key_source(value: str) -> bytes:
    if _BASE64URL_RE.fullmatch(value):
        try:
            decoded = base64.urlsafe_b64decode((value + "=" * (-len(value) % 4)).encode("ascii"))
        except (UnicodeEncodeError, binascii.Error, ValueError):
            decoded = b""
        if len(decoded) >= 32:
            return decoded
    return value.encode("utf-8")


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise SessionEnvelopeError("session data could not be serialized") from exc


def _json_mapping(value: bytes, label: str) -> dict[str, object]:
    try:
        decoded = json.loads(value.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SessionEnvelopeError(f"{label} is not valid JSON") from exc
    if not isinstance(decoded, dict):
        raise SessionEnvelopeError(f"{label} must be a mapping")
    return decoded


def _validate_extension_metadata(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise SessionEnvelopeError("Microsoft Entra session metadata must be a mapping")
    if not set(value).issubset(_EXTENSION_METADATA_KEYS):
        raise SessionEnvelopeError("Microsoft Entra session metadata contains an invalid key")
    normalized: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str) or not _IDENTIFIER_RE.fullmatch(item):
            raise SessionEnvelopeError("Microsoft Entra session metadata is invalid")
        normalized[key] = item
    return normalized


def _validate_json_value(value: object, *, depth: int) -> object:
    if depth > _MAX_DEPTH:
        raise SessionEnvelopeError("session data exceeds the maximum nesting depth")
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        if not -(2**63) <= value <= (2**63 - 1):
            raise SessionEnvelopeError("session integer is outside the supported range")
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SessionEnvelopeError("session float must be finite")
        return value
    if isinstance(value, str):
        if len(value) > _MAX_STRING_CHARACTERS:
            raise SessionEnvelopeError("session string is too long")
        return value
    if isinstance(value, Mapping):
        if len(value) > _MAX_COLLECTION_ITEMS:
            raise SessionEnvelopeError("session mapping contains too many items")
        normalized: dict[str, object] = {}
        for raw_key, raw_item in value.items():
            key = _validate_allowed_key(raw_key)
            normalized[key] = _validate_json_value(raw_item, depth=depth + 1)
        return normalized
    if isinstance(value, list):
        if len(value) > _MAX_COLLECTION_ITEMS:
            raise SessionEnvelopeError("session list contains too many items")
        return [_validate_json_value(item, depth=depth + 1) for item in value]
    raise SessionEnvelopeError("session data contains an unsupported type")


def _validate_allowed_key(value: object) -> str:
    if not isinstance(value, str) or len(value) > _MAX_KEY_CHARACTERS:
        raise SessionEnvelopeError("session data contains an invalid key")
    if not _SAFE_KEY_RE.fullmatch(value):
        raise SessionEnvelopeError("session data contains an invalid key")
    return value


def _validate_sid(value: object) -> str:
    if not isinstance(value, str) or not _IDENTIFIER_RE.fullmatch(value) or len(value) < 32:
        raise SessionEnvelopeError("session SID is invalid")
    return value


def _validate_subject_id(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > _MAX_SUBJECT_ID_CHARACTERS:
        raise SessionEnvelopeError("session subject identifier is invalid")
    if not _SUBJECT_ID_RE.fullmatch(value):
        raise SessionEnvelopeError("session subject identifier is invalid")
    return value


def _validate_metadata_shape(metadata: object) -> SessionMetadata:
    if not isinstance(metadata, SessionMetadata):
        raise SessionEnvelopeError("session metadata is invalid")
    return SessionMetadata(
        issued_at=_timestamp(metadata.issued_at, "issued_at"),
        last_seen_at=_timestamp(metadata.last_seen_at, "last_seen_at"),
        sid_rotated_at=_timestamp(metadata.sid_rotated_at, "sid_rotated_at"),
        subject_id=_validate_subject_id(metadata.subject_id),
        subject_revision=_revision(metadata.subject_revision),
    )


def _revision(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2**63 - 1:
        raise SessionEnvelopeError("session subject revision is invalid")
    return value


def _timestamp(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= _MAX_TIMESTAMP
    ):
        raise SessionEnvelopeError(f"session {name} must be a bounded non-negative integer")
    return value


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: object, label: str, *, maximum: int) -> bytes:
    if not isinstance(value, str) or not value or len(value) > maximum * 2:
        raise SessionEnvelopeError(f"{label} is invalid")
    if not _BASE64URL_RE.fullmatch(value):
        raise SessionEnvelopeError(f"{label} is invalid")
    try:
        decoded = base64.urlsafe_b64decode((value + "=" * (-len(value) % 4)).encode("ascii"))
    except (UnicodeEncodeError, binascii.Error, ValueError) as exc:
        raise SessionEnvelopeError(f"{label} is invalid") from exc
    if len(decoded) > maximum:
        raise SessionEnvelopeError(f"{label} exceeds the configured byte limit")
    return decoded


def _identity_component(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise ValueError(f"{name} must be a non-empty string with at most 256 characters")
    return value.strip().casefold()


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _non_negative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


__all__ = [
    "DecodedSession",
    "SessionEnvelopeCodec",
    "SessionEnvelopeError",
    "SessionEnvelopeExpired",
    "SessionMetadata",
    "subject_fingerprint",
]

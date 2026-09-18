"""Small, dependency-free helpers for protecting locally stored secrets."""

import base64
import hashlib
import hmac
import secrets
from typing import Optional


ACCESS_KEY_HASH_ALGORITHM = "pbkdf2_sha256"
ACCESS_KEY_HASH_ITERATIONS = 210_000
ACCESS_KEY_HASH_MAX_ITERATIONS = 1_000_000
ACCESS_KEY_HASH_SALT_BYTES = 16
ACCESS_KEY_HASH_DIGEST_BYTES = 32


def hash_access_key(access_key: str) -> str:
    """Return a salted, slow password-style hash for a UI access key."""
    normalized_key = (access_key or "").strip()
    if not normalized_key:
        raise ValueError("access key is required")

    salt = secrets.token_bytes(ACCESS_KEY_HASH_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        normalized_key.encode("utf-8"),
        salt,
        ACCESS_KEY_HASH_ITERATIONS,
        dklen=ACCESS_KEY_HASH_DIGEST_BYTES,
    )
    encode = lambda value: base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")
    return (
        f"{ACCESS_KEY_HASH_ALGORITHM}${ACCESS_KEY_HASH_ITERATIONS}$"
        f"{encode(salt)}${encode(digest)}"
    )


def verify_access_key_hash(access_key: Optional[str], encoded_hash: Optional[str]) -> bool:
    """Verify a candidate key against the stored encoded hash."""
    if not isinstance(access_key, str) or not isinstance(encoded_hash, str):
        return False

    parts = encoded_hash.split("$")
    if len(parts) != 4 or parts[0] != ACCESS_KEY_HASH_ALGORITHM:
        return False

    try:
        iterations = int(parts[1])
        if iterations < 1 or iterations > ACCESS_KEY_HASH_MAX_ITERATIONS:
            return False
        salt = _decode(parts[2])
        expected_digest = _decode(parts[3])
    except (TypeError, ValueError):
        return False

    if (
        len(salt) != ACCESS_KEY_HASH_SALT_BYTES
        or len(expected_digest) != ACCESS_KEY_HASH_DIGEST_BYTES
    ):
        return False

    candidate_digest = hashlib.pbkdf2_hmac(
        "sha256",
        access_key.strip().encode("utf-8"),
        salt,
        iterations,
        dklen=len(expected_digest),
    )
    return hmac.compare_digest(candidate_digest, expected_digest)


def _decode(value: str) -> bytes:
    """Decode the unpadded URL-safe base64 used in the stored format."""
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import UTC, datetime, timedelta

try:
    from cryptography.fernet import Fernet
except ImportError:  # pragma: no cover - optional production dependency
    Fernet = None


def hash_password(password: str, *, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 240_000)
    return f"pbkdf2_sha256${salt}${base64.b64encode(derived).decode('ascii')}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, salt, expected = password_hash.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    return hmac.compare_digest(hash_password(password, salt=salt), password_hash)


def create_session_token() -> tuple[str, str, datetime]:
    raw_token = secrets.token_urlsafe(48)
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(UTC) + timedelta(hours=int(os.environ.get("SESSION_TTL_HOURS", "12")))
    return raw_token, token_hash, expires_at


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def encrypt_secret(value: str) -> bytes:
    key = os.environ.get("APP_ENCRYPTION_KEY", "")
    if not key:
        raise RuntimeError("APP_ENCRYPTION_KEY is required to encrypt provider API keys.")
    if Fernet is None:
        raise RuntimeError("Install cryptography to encrypt provider API keys.")
    return Fernet(key.encode("utf-8")).encrypt(value.encode("utf-8"))


def decrypt_secret(value: bytes) -> str:
    key = os.environ.get("APP_ENCRYPTION_KEY", "")
    if not key:
        raise RuntimeError("APP_ENCRYPTION_KEY is required to decrypt provider API keys.")
    if Fernet is None:
        raise RuntimeError("Install cryptography to decrypt provider API keys.")
    return Fernet(key.encode("utf-8")).decrypt(value).decode("utf-8")

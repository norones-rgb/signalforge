from __future__ import annotations

from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


# bcrypt has a 72-byte password limit; bcrypt_sha256 safely supports longer inputs.
_pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")
ALGORITHM = "HS256"


def get_password_hash(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def _get_fernet() -> Fernet:
    key = settings.fernet_key
    if isinstance(key, str):
        key_bytes = key.encode("utf-8")
    else:
        key_bytes = key
    try:
        return Fernet(key_bytes)
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError(
            "Invalid FERNET_KEY. Must be a urlsafe base64-encoded 32-byte key."
        ) from exc


def encrypt_token(token: str) -> str:
    if not token:
        return ""
    return _get_fernet().encrypt(token.encode("utf-8")).decode("utf-8")


def decrypt_token(token_encrypted: str) -> str:
    if not token_encrypted:
        return ""
    try:
        return _get_fernet().decrypt(token_encrypted.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Invalid encrypted token") from exc


def create_access_token(subject: str, expires_minutes: int = 60 * 24) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if not subject:
            raise ValueError("Invalid token")
        return subject
    except JWTError as exc:
        raise ValueError("Invalid token") from exc

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=['argon2'], deprecated='auto')


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)



def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)



def create_access_token(subject: str, role: str) -> tuple[str, datetime]:
    settings = get_settings()
    expires_at = utc_now() + timedelta(minutes=settings.access_token_ttl_minutes)
    payload: dict[str, Any] = {
        'sub': subject,
        'role': role,
        'type': 'access',
        'iat': int(utc_now().timestamp()),
        'exp': int(expires_at.timestamp()),
        'jti': uuid4().hex,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm), expires_at



def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    settings = get_settings()
    expires_at = utc_now() + timedelta(days=settings.refresh_token_ttl_days)
    jti = uuid4().hex
    payload: dict[str, Any] = {
        'sub': subject,
        'type': 'refresh',
        'iat': int(utc_now().timestamp()),
        'exp': int(expires_at.timestamp()),
        'jti': jti,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm), jti, expires_at



def decode_token(token: str, expected_type: Literal['access', 'refresh'] | None = None) -> dict[str, Any]:
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    token_type = payload.get('type')
    if expected_type and token_type != expected_type:
        raise jwt.InvalidTokenError(f'Unexpected token type: {token_type}')
    return payload
